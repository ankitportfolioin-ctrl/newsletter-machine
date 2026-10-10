"""X (Twitter) collector with honest tier chain.

Tiers (preferred tier comes from sources.yaml, default official_api):
  official_api — X API v2 `tweets/search/recent` with X_BEARER_TOKEN.
      Reality: search requires a paid tier (Basic+). Free-tier tokens get
      HTTP 402/403, which we record and fall through — never crash.
  provider     — configured third-party JSON API (see providers/generic.py).
  manual       — always available as guidance: import a CSV/URL-list with
      --manual-file … --manual-platform x.

ToS: official API or lawful providers only. No scraping, no session hijacking.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from newsletter_machine.collectors.base import BaseCollector, CollectorResult, Item
from newsletter_machine.collectors.http import create_client, get_limiter, polite_get
from newsletter_machine.collectors.providers import get_provider, manual_hint, provider_available
from newsletter_machine.collectors.providers.base import ProviderError
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text

SEARCH_URL = "https://api.x.com/2/tweets/search/recent"


def _parse_dt(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def tweet_to_item(tweet: dict, users: dict[str, str], language: str) -> Item | None:
    tid = str(tweet.get("id", "") or "")
    text = str(tweet.get("text", "") or "")
    if not tid or not text:
        return None
    author_id = str(tweet.get("author_id", "") or "")
    username = users.get(author_id, author_id or "unknown")
    url = f"https://x.com/{username}/status/{tid}"
    metrics_raw = tweet.get("public_metrics", {}) or {}
    return Item(
        platform="x",
        external_id=tid,
        url=url,
        canonical_url=canonicalize_url(url),
        author=normalize_text("@" + username, max_chars=512),
        title=normalize_text(text[:160], max_chars=500),
        text=normalize_text(text, max_chars=5000),
        published_at=_parse_dt(tweet.get("created_at")),
        metrics={
            "likes": int(metrics_raw.get("like_count", 0) or 0),
            "shares": int(metrics_raw.get("retweet_count", 0) or 0),
            "comments": int(metrics_raw.get("reply_count", 0) or 0),
            "views": int(metrics_raw.get("impression_count", 0) or 0),
        },
        language=language,
        raw={"author_id": author_id},
    )


class XTwitterCollector(BaseCollector):
    platform = "x"

    def __init__(
        self,
        bearer_token: str | None = None,
        per_min: int = 15,
        preferred_tier: str | None = None,
    ) -> None:
        self.bearer_token = (
            bearer_token if bearer_token is not None else os.getenv("X_BEARER_TOKEN", "")
        )
        self.per_min = per_min
        self.preferred_tier = preferred_tier or os.getenv("X_TIER", "official_api")

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        targets = getattr(niche, "targets", None)
        queries = list(getattr(targets, "x_queries", []) or [])
        accounts = list(getattr(targets, "x_accounts", []) or [])
        language = getattr(niche, "language", "en") or "en"
        if not queries and not accounts:
            return CollectorResult(
                items=[], errors=["no x_queries or x_accounts configured"], tier_used="disabled"
            )
        search_queries = list(queries) + [f"from:{a.lstrip('@')}" for a in accounts]
        errors: list[str] = []
        chain = self._chain()
        if "official_api" in chain and self.bearer_token:
            result = await self._official_collect(search_queries, since, limit, language)
            errors.extend(result.errors)
            if result.items:
                return result
        elif "official_api" in chain:
            errors.append("missing X_BEARER_TOKEN (X API v2 needs a paid tier for search)")
        if "provider" in chain and provider_available():
            try:
                provider = get_provider()
                assert provider is not None
                items = await provider.fetch("x", search_queries, since, limit)
                if items:
                    errors.append("official API unavailable — used provider fallback")
                    return CollectorResult(
                        items=items, errors=errors, quota_used=0, tier_used="provider"
                    )
                errors.append("provider returned 0 items")
            except ProviderError as e:
                errors.append(f"provider: {e}")
        elif "provider" in chain:
            errors.append("PROVIDER_BASE_URL not set (no provider fallback)")
        errors.append(manual_hint("x"))
        return CollectorResult(items=[], errors=errors, quota_used=0, tier_used="disabled")

    def _chain(self) -> list[str]:
        if self.preferred_tier == "provider":
            return ["provider"]
        if self.preferred_tier in ("manual", "disabled"):
            return []
        return ["official_api", "provider"]

    async def _official_collect(
        self, queries: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        items: list[Item] = []
        errors: list[str] = []
        quota_used = 0
        limiter = get_limiter("x", self.per_min)
        per_query = max(1, min(25, max(1, limit // max(1, len(queries)))))
        seen: set[str] = set()
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        async with create_client(headers=headers) as client:
            for query in queries:
                if len(items) >= limit:
                    break
                try:
                    resp = await polite_get(
                        client,
                        limiter,
                        SEARCH_URL,
                        {
                            "query": f"({query}) -is:retweet",
                            "max_results": min(max(per_query, 10), 100),
                            "tweet.fields": "created_at,public_metrics,author_id",
                            "expansions": "author_id",
                            "user.fields": "username",
                            "start_time": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        },
                    )
                    quota_used += 1
                    if resp.status_code == 402:
                        errors.append(
                            "search: HTTP 402 (X free tier excludes search — paid Basic+ required)"
                        )
                        break  # retrying other queries is pointless on paywall
                    if resp.status_code in (401, 403):
                        errors.append(
                            f"search: HTTP {resp.status_code} (bad/revoked token or forbidden)"
                        )
                        break
                    if resp.status_code == 429:
                        errors.append(
                            "search: HTTP 429 (X rate limit — back off or lower rate_limit_per_min)"
                        )
                        continue
                    resp.raise_for_status()
                    payload = resp.json()
                    users = {
                        u.get("id", ""): u.get("username", "")
                        for u in payload.get("includes", {}).get("users", [])
                    }
                    for tweet in payload.get("data", []):
                        if len(items) >= limit:
                            break
                        item = tweet_to_item(tweet, users, language)
                        if item is None or item.external_id in seen:
                            continue
                        if item.published_at is not None and item.published_at < since:
                            continue
                        seen.add(item.external_id)
                        items.append(item)
                except Exception as e:  # noqa: BLE001 - one bad query never kills the run
                    errors.append(f"search {query!r}: {type(e).__name__}: {e}")
        return CollectorResult(
            items=items, errors=errors, quota_used=quota_used, tier_used="official_api"
        )

    def tier_status(self) -> tuple[str, str]:
        parts = []
        if os.getenv("X_BEARER_TOKEN"):
            parts.append("official_api: token present (search needs paid tier; 402/403 fall back)")
        else:
            parts.append("official_api: missing X_BEARER_TOKEN")
        parts.append(
            "provider: configured"
            if provider_available()
            else "provider: PROVIDER_BASE_URL not set"
        )
        parts.append("manual: always available via --manual-file")
        return ("official_api", "; ".join(parts))
