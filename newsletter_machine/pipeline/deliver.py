"""Delivery: file output, SMTP, Resend, webhook. One receipt, honest errors."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from newsletter_machine.logging import get_logger

RESEND_URL = "https://api.resend.com/emails"
log = get_logger("newsletter_machine.deliver")


def _transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return 500 <= exc.response.status_code < 600
    return False


@retry(
    retry=retry_if_exception(_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _post_with_retry(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    resp = await client.post(url, **kwargs)
    if 500 <= resp.status_code < 600:
        raise httpx.HTTPStatusError(
            f"transient {resp.status_code}", request=resp.request, response=resp
        )
    return resp


class DeliveryError(RuntimeError):
    pass


async def deliver_newsletter(
    session: Any,
    settings: Any,
    newsletter_cfg: Any,
    newsletter_id: int,
    method: str | None = None,
    to_override: list[str] | None = None,
) -> dict[str, Any]:
    """Deliver a built newsletter. Returns a receipt dict; raises DeliveryError."""
    from newsletter_machine.db.models import Newsletter as NewsletterRow

    row = session.get(NewsletterRow, newsletter_id)
    if row is None:
        raise DeliveryError(f"newsletter {newsletter_id} not found")
    chosen = (method or getattr(newsletter_cfg, "delivery_method", "file") or "file").lower()
    recipients = list(to_override or []) or list(getattr(newsletter_cfg, "recipients", []) or [])

    if chosen == "file":
        receipt: dict[str, Any] = {
            "method": "file",
            "paths": [row.html_path, row.md_path, row.txt_path],
            "missing": [
                p
                for p in (row.html_path, row.md_path, row.txt_path)
                if not p or not Path(p).exists()
            ],
        }
    elif chosen == "smtp":
        receipt = _send_smtp(settings, recipients, row.subject, row.html_path, row.txt_path)
    elif chosen == "resend":
        receipt = await _send_resend(settings, recipients, row.subject, row.html_path, row.txt_path)
    elif chosen == "webhook":
        receipt = await _send_webhook(settings, row)
    elif chosen == "none":
        receipt = {"method": "none", "skipped": True}
    else:
        raise DeliveryError(f"unknown delivery method {chosen!r} (file|smtp|resend|webhook|none)")
    content = dict(row.content_json or {})
    content["delivery"] = receipt
    row.content_json = content
    row.status = "delivered"
    session.add(row)
    session.commit()
    log.info(
        "newsletter_delivered",
        extra={"ctx_newsletter": newsletter_id, "ctx_method": receipt.get("method")},
    )
    return receipt


def _read(path: str | None) -> str:
    if not path or not Path(path).exists():
        return ""
    return Path(path).read_text(encoding="utf-8")


def _send_smtp(
    settings: Any, recipients: list[str], subject: str, html_path: str, txt_path: str
) -> dict[str, Any]:
    if not recipients:
        raise DeliveryError("smtp needs recipients (newsletter.recipients or --to)")
    for name in ("smtp_host", "smtp_user", "smtp_password", "smtp_from"):
        if not getattr(settings, name, ""):
            raise DeliveryError(f"smtp needs {name.upper()} in .env")
    message = MIMEMultipart("alternative")
    message["Subject"] = subject or "Newsletter"
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(recipients)
    text = _read(txt_path) or "Plain-text version unavailable."
    html = _read(html_path) or f"<p>{text[:500]}</p>"
    message.attach(MIMEText(text, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(settings.smtp_host, int(settings.smtp_port)) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, recipients, message.as_string())
    except (smtplib.SMTPException, OSError) as e:
        raise DeliveryError(f"smtp failed: {type(e).__name__}: {e}") from e
    return {"method": "smtp", "to": recipients}


async def _send_resend(
    settings: Any, recipients: list[str], subject: str, html_path: str, txt_path: str
) -> dict[str, Any]:
    if not settings.resend_api_key:
        raise DeliveryError("resend needs RESEND_API_KEY in .env")
    if not recipients:
        raise DeliveryError("resend needs recipients (newsletter.recipients or --to)")
    sender = settings.smtp_from or "newsletter@localhost"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await _post_with_retry(
                client,
                RESEND_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": sender,
                    "to": recipients,
                    "subject": subject or "Newsletter",
                    "html": _read(html_path),
                    "text": _read(txt_path),
                },
            )
    except httpx.TransportError as e:
        raise DeliveryError(f"resend transport error: {e}") from e
    except httpx.HTTPStatusError as e:
        raise DeliveryError(f"resend unavailable after retries: {e}") from e
    if resp.status_code >= 400:
        raise DeliveryError(f"resend HTTP {resp.status_code}: {resp.text[:200]}")
    return {"method": "resend", "to": recipients, "id": resp.json().get("id")}


async def _send_webhook(settings: Any, row: Any) -> dict[str, Any]:
    url = settings.delivery_webhook_url or ""
    if not url:
        raise DeliveryError("webhook needs DELIVERY_WEBHOOK_URL in .env")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await _post_with_retry(
                client,
                url,
                json={
                    "niche_id": row.niche_id,
                    "date": row.date,
                    "subject": row.subject,
                    "html": _read(row.html_path),
                    "text": _read(row.txt_path),
                },
            )
    except httpx.TransportError as e:
        raise DeliveryError(f"webhook transport error: {e}") from e
    except httpx.HTTPStatusError as e:
        raise DeliveryError(f"webhook unavailable after retries: {e}") from e
    if resp.status_code >= 400:
        raise DeliveryError(f"webhook HTTP {resp.status_code}: {resp.text[:200]}")
    return {"method": "webhook", "url": url, "status": resp.status_code}
