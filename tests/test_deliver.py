"""Phase 6: delivery transports (respx for HTTP, fakes for SMTP, tmp files)."""

from __future__ import annotations

import smtplib
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.config import NewsletterConfig, Settings
from newsletter_machine.db.models import Base, Newsletter
from newsletter_machine.db.session import get_engine, make_session_factory
from newsletter_machine.pipeline.deliver import DeliveryError, deliver_newsletter


def _settings(tmp_path: Path, **overrides) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{tmp_path}/t.db",
        output_dir=str(tmp_path / "out"),
        **overrides,
    )


def _cfg(**overrides) -> NewsletterConfig:
    base: dict = {"name": "T", "delivery_method": "file", "recipients": []}
    base.update(overrides)
    return NewsletterConfig.model_validate(base)


def _seeded(tmp_path: Path, settings: Settings) -> tuple[object, int]:
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    session = make_session_factory(engine)()
    html = tmp_path / "n.html"
    txt = tmp_path / "n.txt"
    md = tmp_path / "n.md"
    html.write_text("<html><body>Hi</body></html>", encoding="utf-8")
    txt.write_text("Hi", encoding="utf-8")
    md.write_text("# Hi", encoding="utf-8")
    row = Newsletter(
        date="2026-10-10",
        niche_id="n1",
        subject="S",
        html_path=str(html),
        md_path=str(md),
        txt_path=str(txt),
        content_json={},
        status="built",
    )
    session.add(row)
    session.commit()
    return session, row.id


async def test_file_delivery_receipt(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session, nid = _seeded(tmp_path, settings)
    try:
        receipt = await deliver_newsletter(session, settings, _cfg(), nid)
        assert receipt["method"] == "file" and receipt["missing"] == []
        from newsletter_machine.db.models import Newsletter as Row

        assert session.get(Row, nid).status == "delivered"
    finally:
        session.close()


async def test_unknown_method_and_missing_row(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session, nid = _seeded(tmp_path, settings)
    try:
        with pytest.raises(DeliveryError, match="unknown delivery method"):
            await deliver_newsletter(session, settings, _cfg(), nid, method="pigeon")
        with pytest.raises(DeliveryError, match="not found"):
            await deliver_newsletter(session, settings, _cfg(), 999999)
    finally:
        session.close()


async def test_smtp_needs_config_then_sends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(tmp_path)
    session, nid = _seeded(tmp_path, settings)
    try:
        with pytest.raises(DeliveryError, match="recipients"):
            await deliver_newsletter(session, settings, _cfg(delivery_method="smtp"), nid)

        sent: dict = {}

        class FakeSMTP:
            def __init__(self, host, port):
                sent["host"] = host

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def starttls(self):
                sent["tls"] = True

            def login(self, user, password):
                sent["user"] = user

            def sendmail(self, sender, recipients, message):
                sent["recipients"] = recipients
                sent["bytes"] = len(message)

        monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
        full = _settings(
            tmp_path,
            smtp_host="mail.example.com",
            smtp_user="u",
            smtp_password="p",
            smtp_from="news@example.com",
        )
        receipt = await deliver_newsletter(
            session, full, _cfg(delivery_method="smtp"), nid, to_override=["a@example.com"]
        )
        assert receipt == {"method": "smtp", "to": ["a@example.com"]}
        assert sent["tls"] is True and sent["bytes"] > 0
    finally:
        session.close()


@respx.mock
async def test_resend_and_webhook(tmp_path: Path) -> None:
    settings = _settings(
        tmp_path, resend_api_key="rk", delivery_webhook_url="https://hooks.example.com/x"
    )
    session, nid = _seeded(tmp_path, settings)
    try:
        respx.post("https://api.resend.com/emails").mock(
            return_value=Response(200, json={"id": "re_1"})
        )
        receipt = await deliver_newsletter(
            session, settings, _cfg(delivery_method="resend"), nid, to_override=["a@example.com"]
        )
        assert receipt == {"method": "resend", "to": ["a@example.com"], "id": "re_1"}

        respx.post("https://hooks.example.com/x").mock(return_value=Response(200, text="ok"))
        receipt = await deliver_newsletter(session, settings, _cfg(delivery_method="webhook"), nid)
        assert receipt["method"] == "webhook" and receipt["status"] == 200

        respx.post("https://hooks.example.com/x").mock(return_value=Response(500, text="boom"))
        with pytest.raises(DeliveryError, match="unavailable after retries"):
            await deliver_newsletter(session, settings, _cfg(delivery_method="webhook"), nid)

        no_key = _settings(tmp_path)
        with pytest.raises(DeliveryError, match="RESEND_API_KEY"):
            await deliver_newsletter(
                session, no_key, _cfg(delivery_method="resend"), nid, to_override=["a@example.com"]
            )
    finally:
        session.close()


def test_cli_send_file_method(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import yaml
    from typer.testing import CliRunner

    from newsletter_machine.cli import app as cli_app
    from newsletter_machine.config import clear_config_cache

    (tmp_path / "niches.yaml").write_text(yaml.safe_dump({"niches": []}), encoding="utf-8")
    (tmp_path / "sources.yaml").write_text(yaml.safe_dump({"collectors": {}}), encoding="utf-8")
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "T", "delivery_method": "file"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    clear_config_cache()
    try:
        settings = _settings(tmp_path)
        session, nid = _seeded(tmp_path, settings)
        session.close()
        result = CliRunner().invoke(cli_app, ["send", "--newsletter", str(nid)])
        assert result.exit_code == 0, result.output
        assert "Delivered newsletter" in result.output
        missing = CliRunner().invoke(cli_app, ["send", "--newsletter", "999999"])
        assert missing.exit_code == 1
    finally:
        clear_config_cache()
