"""Quora collector with honest tier chain.

Ground truth (checked 2026-10-10): Quora has NO official API and serves NO
public topic RSS — even plain topic pages return HTTP 403 to bot clients.
So the working tiers are:
  provider — third-party Q&A snapshots via the provider interface.
  manual   — guidance: --manual-file … --manual-platform quora (works today).
  rss      — supported ONLY if a user explicitly sets tier: rss; the collector
      then tries {topic}/rss once per topic and records the outcome instead of
      crashing. Expect failure; the error says so plainly.

ToS: no scraping of Quora behind its bot protection; provider/manual only.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import feedparser

from newsletter_machine.collectors.base import BaseCollector, CollectorResult, Item
from newsletter_machine.collectors.http import create_client, get_limiter, polite_get
from newsletter_machine.collectors.providers import get_provider, manual_hint, provider_available
from newsletter_machine.collectors.providers.base import ProviderError
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text


class QuoraCollector(BaseCollector):
    platform = "quora"

    def __init__(self, per_min: int = 10, preferred_tier: str | None = None) -> None:
        self.per_min = per_min
        self.preferred_tier = preferred_tier or os.getenv("QUORA_TIER", "manual")

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        targets = getattr(niche, "targets", None)
        topics = list(getattr(targets, "quora_topics", []) or [])
        language = getattr(niche, "language", "en") or "en"
        if not topics:
            return CollectorResult(
                items=[], errors=["no quora_topics configured"], tier_used="disabled"
            )
        errors: list[str] = []
        if "rss" in self._chain():
            result = await self._rss_attempt(topics, since, limit, language)
            errors.extend(result.errors)
            if result.items:
                return result
        if "provider" in self._chain() and provider_available():
            try:
                provider = get_provider()
                assert provider is not None
                items = await provider.fetch("quora", topics, since, limit)
                if items:
                    errors.append("no official API/RSS — used provider fallback")
                    return CollectorResult(
                        items=items, errors=errors, quota_used=0, tier_used="provider"
                    )
                errors.append("provider returned 0 items")
            except ProviderError as e:
                errors.append(f"provider: {e}")
        elif "provider" in self._chain():
            errors.append("PROVIDER_BASE_URL not set (no provider fallback)")
        if not any("official API" in e for e in errors):
            errors.append(
                "Quora has no official API and no public topic RSS (topic pages 403 to bots)"
            )
        errors.append(manual_hint("quora"))
        return CollectorResult(items=[], errors=errors, quota_used=0, tier_used="disabled")

    def _chain(self) -> list[str]:
        if self.preferred_tier == "rss":
            return ["rss", "provider"]
        if self.preferred_tier == "provider":
            return ["provider"]
        if self.preferred_tier in ("disabled",):
            return []
        return ["provider"]

    async def _rss_attempt(
        self, topics: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        """Try per-topic RSS once each. Quora discontinued these; failure is the expected path."""
        items: list[Item] = []
        errors: list[str] = []
        quota_used = 0
        limiter = get_limiter("quora", self.per_min)
        per_topic = max(1, limit // max(1, len(topics)))
        async with create_client() as client:
            for topic in topics:
                if len(items) >= limit:
                    break
                slug = "".join(w.capitalize() for w in str(topic).replace("-", " ").split())
                url = f"https://www.quora.com/topic/{slug}/rss"
                try:
                    resp = await polite_get(client, limiter, url)
                    quota_used += 1
                    if resp.status_code in (401, 403, 404):
                        errors.append(
                            f"topic {topic!r}: HTTP {resp.status_code} (no public feed — expected)"
                        )
                        continue
                    resp.raise_for_status()
                    parsed = feedparser.parse(resp.content)
                    if not parsed.entries:
                        errors.append(
                            f"topic {topic!r}: feed empty/unparseable (no public feed — expected)"
                        )
                        continue
                    for entry in parsed.entries[:per_topic]:
                        link = getattr(entry, "link", "") or ""
                        if not link or len(items) >= limit:
                            continue
                        canonical = canonicalize_url(link)
                        items.append(
                            Item(
                                platform="quora",
                                external_id=canonical,
                                url=link,
                                canonical_url=canonical,
                                author=normalize_text(getattr(entry, "author", ""), max_chars=512),
                                title=normalize_text(
                                    getattr(entry, "title", "") or canonical, max_chars=1000
                                ),
                                text=normalize_text(getattr(entry, "summary", ""), max_chars=5000),
                                language=language,
                                raw={"via": "topic-rss"},
                            )
                        )
                except Exception as e:  # noqa: BLE001 - expected path, recorded not raised
                    errors.append(
                        f"topic {topic!r}: {type(e).__name__} (no public feed — expected)"
                    )
        return CollectorResult(items=items, errors=errors, quota_used=quota_used, tier_used="rss")

    def tier_status(self) -> tuple[str, str]:
        parts = ["official_api: NONE — no official API exists (topic pages HTTP 403 to bots)"]
        parts.append(
            "provider: configured"
            if provider_available()
            else "provider: PROVIDER_BASE_URL not set"
        )
        parts.append("manual: always available via --manual-file")
        return ("manual", "; ".join(parts))
