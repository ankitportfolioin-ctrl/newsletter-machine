"""Generic HTTP provider: POST queries, map the documented JSON schema to Items.

Request (POST {base_url}, Bearer {api_key})::
    {"platform": "x", "queries": ["AI marketing"], "since": "<iso>", "limit": 10}

Expected response (JSON object):::
    {"items": [{"url": "https://… (required)", "platform": "x",
                "external_id": "…", "title": "…", "text": "…", "author": "…",
                "published_at": "<iso>", "language": "en",
                "metrics": {"likes": 1}, "media_urls": ["https://…"]}]}

Unknown extra keys are ignored; `url` is the only required field
(`external_id` falls back to sha256(url), `platform` to the requested one).
Any Apify actor (or compatible service) wrapped to speak this schema works —
see README "Provider fallback" for a mapping example.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from typing import Any

from newsletter_machine.collectors.base import Item
from newsletter_machine.collectors.http import create_client, get_limiter
from newsletter_machine.collectors.providers.base import DataProvider, ProviderError
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text


def _parse_dt(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def map_provider_row(row: dict[str, Any], platform: str) -> Item:
    url = str(row.get("url", "") or "").strip()
    if not url:
        raise ProviderError("provider row is missing required 'url'")
    external_id = (
        str(row.get("external_id", "") or "").strip()
        or hashlib.sha256(url.encode()).hexdigest()[:32]
    )
    metrics = row.get("metrics", {}) or {}
    media = row.get("media_urls", []) or []
    return Item(
        platform=str(row.get("platform", "") or platform).strip() or platform,
        external_id=external_id,
        url=url,
        canonical_url=canonicalize_url(url),
        author=normalize_text(str(row.get("author", "") or ""), max_chars=512),
        title=normalize_text(str(row.get("title", "") or url), max_chars=1000),
        text=normalize_text(str(row.get("text", "") or ""), max_chars=20000),
        media_urls=[str(u) for u in media if str(u).startswith("http")][:4],
        published_at=_parse_dt(row.get("published_at")),
        metrics=dict(metrics) if isinstance(metrics, dict) else {},
        language=str(row.get("language", "") or "en").strip() or "en",
        raw={"via": "provider"},
    )


class GenericHTTPProvider(DataProvider):
    name = "generic_http"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (
            (base_url if base_url is not None else os.getenv("PROVIDER_BASE_URL", ""))
            .strip()
            .rstrip("/")
        )
        self.api_key = api_key if api_key is not None else os.getenv("PROVIDER_API_KEY", "")
        if not self.base_url:
            raise ProviderError("PROVIDER_BASE_URL is not set")

    async def fetch(
        self, platform: str, queries: list[str], since: datetime, limit: int
    ) -> list[Item]:
        limiter = get_limiter("provider", 15)
        await limiter.acquire()
        try:
            async with create_client(
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
            ) as client:
                resp = await client.post(
                    self.base_url,
                    json={
                        "platform": platform,
                        "queries": queries,
                        "since": since.isoformat(),
                        "limit": limit,
                    },
                )
        except Exception as e:  # noqa: BLE001 - network failure becomes ProviderError
            raise ProviderError(f"provider request failed: {type(e).__name__}: {e}") from e
        if resp.status_code in (401, 403):
            raise ProviderError(f"provider: HTTP {resp.status_code} (bad API key?)")
        if resp.status_code == 402:
            raise ProviderError("provider: HTTP 402 (out of credit / paywalled)")
        if resp.status_code == 429:
            raise ProviderError("provider: HTTP 429 (rate limited)")
        if resp.status_code >= 400:
            raise ProviderError(f"provider: HTTP {resp.status_code}")
        try:
            payload = resp.json()
        except ValueError as e:
            raise ProviderError(f"provider: non-JSON response: {e}") from e
        rows = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(rows, list):
            raise ProviderError("provider: expected {'items': [...]}")
        items: list[Item] = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            try:
                item = map_provider_row(row, platform)
            except ProviderError:
                continue
            if item.published_at is not None and item.published_at < since:
                continue
            items.append(item)
        return items
