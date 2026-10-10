"""Reddit collector: official OAuth (script app) with public-JSON fallback.

Official path (REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET):
  POST reddit.com/api/v1/access_token (client_credentials) ->
  GET oauth.reddit.com/r/{sub}/hot +top + global /search for keywords.

No credentials? Falls back to public https://www.reddit.com/r/{sub}/hot.json
(rate-limited, polite 1 req / 2s) and reports tier_used="public_json" so the
diagnostics footer tells the truth. Failures (401/403/429/quota) are recorded
as errors; the run never crashes.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from newsletter_machine.collectors.base import BaseCollector, CollectorResult, Item
from newsletter_machine.collectors.http import create_client, get_limiter, polite_get
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_BASE = "https://oauth.reddit.com"
PUBLIC_BASE = "https://www.reddit.com"


def _post_published(created_utc: Any) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(created_utc), tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _post_to_item(data: dict, language: str) -> Item | None:
    pid = str(data.get("id", "") or "")
    if not pid:
        return None
    permalink = str(data.get("permalink", "") or "")
    url = data.get("url_overridden_by_dest") or (
        f"https://www.reddit.com{permalink}" if permalink else ""
    )
    if not url:
        return None
    title = normalize_text(str(data.get("title", "") or pid), max_chars=1000)
    text = normalize_text(str(data.get("selftext", "") or ""), max_chars=8000)
    return Item(
        platform="reddit",
        external_id=pid,
        url=url,
        canonical_url=canonicalize_url(url),
        author=normalize_text(str(data.get("author", "") or ""), max_chars=512),
        title=title,
        text=text or title,
        published_at=_post_published(data.get("created_utc")),
        metrics={
            "upvotes": int(data.get("score", 0) or 0),
            "upvote_ratio": float(data.get("upvote_ratio", 0.0) or 0.0),
            "comments": int(data.get("num_comments", 0) or 0),
            "subreddit": str(data.get("subreddit", "") or ""),
        },
        language=language,
        raw={"permalink": permalink},
    )


class RedditCollector(BaseCollector):
    platform = "reddit"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
        per_min: int = 30,
    ) -> None:
        self.client_id = client_id if client_id is not None else os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = (
            client_secret if client_secret is not None else os.getenv("REDDIT_CLIENT_SECRET", "")
        )
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "newsletter-machine/0.1")
        self.per_min = per_min

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        targets = getattr(niche, "targets", None)
        subreddits = list(getattr(targets, "subreddits", []) or [])
        keywords = list(getattr(niche, "keywords_include", []) or [])
        language = getattr(niche, "language", "en") or "en"
        if not subreddits and not keywords:
            return CollectorResult(
                items=[], errors=["no subreddits or keywords configured"], tier_used="disabled"
            )
        try:
            if self.client_id and self.client_secret:
                return await self._oauth_collect(subreddits, keywords, since, limit, language)
            return await self._public_collect(subreddits, since, limit, language)
        except Exception as e:  # noqa: BLE001 - contract: never crash
            return CollectorResult(
                items=[], errors=[f"reddit: {type(e).__name__}: {e}"], tier_used="disabled"
            )

    async def _oauth_collect(
        self, subreddits: list[str], keywords: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        items: list[Item] = []
        errors: list[str] = []
        quota_used = 0
        limiter = get_limiter("reddit", min(self.per_min, 30))
        seen: set[str] = set()

        def keep(item: Item | None) -> None:
            if item is None or item.external_id in seen or len(items) >= limit:
                return
            if item.published_at is not None and item.published_at < since:
                return
            seen.add(item.external_id)
            items.append(item)

        async with create_client(headers={"User-Agent": self.user_agent}) as client:
            # Token (basic auth, client_credentials)
            try:
                await limiter.acquire()
                resp = await client.post(
                    TOKEN_URL,
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"User-Agent": self.user_agent},
                )
                quota_used += 1
                if resp.status_code in (401, 403):
                    errors.append(f"oauth token: HTTP {resp.status_code} (bad id/secret)")
                    return CollectorResult(
                        items=[], errors=errors, quota_used=quota_used, tier_used="official_api"
                    )
                resp.raise_for_status()
                token = resp.json().get("access_token", "")
                if not token:
                    errors.append("oauth token: empty access_token")
                    return CollectorResult(
                        items=[], errors=errors, quota_used=quota_used, tier_used="official_api"
                    )
            except Exception as e:  # noqa: BLE001
                errors.append(f"oauth token: {type(e).__name__}: {e}")
                return CollectorResult(
                    items=[], errors=errors, quota_used=quota_used, tier_used="official_api"
                )

            oauth_headers = {"User-Agent": self.user_agent, "Authorization": f"Bearer {token}"}
            async with create_client(headers=oauth_headers) as api:
                per_sub = max(1, limit // max(1, len(subreddits))) if subreddits else limit
                for sub in subreddits:
                    if len(items) >= limit:
                        break
                    for sort in ("hot", "top"):
                        if len(items) >= limit:
                            break
                        try:
                            params: dict[str, Any] = {"limit": min(per_sub, 25)}
                            if sort == "top":
                                params["t"] = "week"
                            resp = await polite_get(
                                api, limiter, f"{OAUTH_BASE}/r/{sub}/{sort}", params
                            )
                            quota_used += 1
                            if resp.status_code in (401, 403, 429):
                                errors.append(f"r/{sub}/{sort}: HTTP {resp.status_code}")
                                continue
                            resp.raise_for_status()
                            for child in resp.json().get("data", {}).get("children", []):
                                keep(_post_to_item(child.get("data", {}), language))
                        except Exception as e:  # noqa: BLE001
                            errors.append(f"r/{sub}/{sort}: {type(e).__name__}: {e}")
                for query in keywords[:2]:
                    if len(items) >= limit:
                        break
                    try:
                        resp = await polite_get(
                            api,
                            limiter,
                            f"{OAUTH_BASE}/search",
                            {"q": query, "limit": 10, "sort": "top", "t": "week"},
                        )
                        quota_used += 1
                        resp.raise_for_status()
                        for child in resp.json().get("data", {}).get("children", []):
                            keep(_post_to_item(child.get("data", {}), language))
                    except Exception as e:  # noqa: BLE001
                        errors.append(f"search {query!r}: {type(e).__name__}: {e}")
        return CollectorResult(
            items=items, errors=errors, quota_used=quota_used, tier_used="official_api"
        )

    async def _public_collect(
        self, subreddits: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        items: list[Item] = []
        errors = [
            "REDDIT_CLIENT_ID/SECRET missing — public .json fallback (limits, no search)"
        ]
        quota_used = 0
        if not subreddits:
            errors.append("public fallback needs subreddits; keywords-only search requires OAuth")
            return CollectorResult(items=[], errors=errors, tier_used="disabled")
        limiter = get_limiter("reddit-public", 30)  # 1 req / 2s, inside Reddit's public limits
        seen: set[str] = set()
        async with create_client(headers={"User-Agent": self.user_agent}) as client:
            per_sub = max(1, limit // max(1, len(subreddits)))
            for sub in subreddits:
                if len(items) >= limit:
                    break
                try:
                    resp = await polite_get(
                        client,
                        limiter,
                        f"{PUBLIC_BASE}/r/{sub}/hot.json",
                        {"limit": min(per_sub, 25)},
                    )
                    quota_used += 1
                    if resp.status_code == 429:
                        errors.append(f"r/{sub}: HTTP 429 (public rate limit — add OAuth creds)")
                        continue
                    if resp.status_code >= 400:
                        errors.append(f"r/{sub}: HTTP {resp.status_code}")
                        continue
                    for child in resp.json().get("data", {}).get("children", []):
                        data = child.get("data", {})
                        if data.get("id") in seen or len(items) >= limit:
                            continue
                        item = _post_to_item(data, language)
                        if item is None:
                            continue
                        if item.published_at is not None and item.published_at < since:
                            continue
                        seen.add(item.external_id)
                        items.append(item)
                except Exception as e:  # noqa: BLE001
                    errors.append(f"r/{sub}: {type(e).__name__}: {e}")
        return CollectorResult(
            items=items, errors=errors, quota_used=quota_used, tier_used="public_json"
        )

    def tier_status(self) -> tuple[str, str]:
        if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
            return ("official_api", "OAuth credentials present")
        return ("official_api", "missing REDDIT_CLIENT_ID/SECRET (public .json fallback)")
