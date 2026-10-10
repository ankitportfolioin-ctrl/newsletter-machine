"""Instagram collector with honest tier chain.

Official API reality (Instagram Graph API, Facebook-login business accounts):
  - WITH INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_BUSINESS_ID: fetches the OWN
    account's recent media and filters captions client-side by niche
    hashtags/keywords. This is the only content endpoint available without a
    reviewed app.
  - Hashtag search (`/ig_hashtag_search`) exists but needs an approved app with
    extra permissions — NOT attempted; documented instead of faked.
  - There is no public/RSS access and no lawful scraping path; without creds
    we go provider → manual.

Tiers: official_api → provider → manual (guidance via --manual-file).
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

GRAPH_VERSION = "v18.0"


def media_to_item(media: dict, language: str) -> Item | None:
    mid = str(media.get("id", "") or "")
    permalink = str(media.get("permalink", "") or "")
    caption = str(media.get("caption", "") or "")
    if not mid or not permalink:
        return None
    try:
        published = datetime.fromisoformat(str(media.get("timestamp", "")).replace("Z", "+00:00"))
        if published.tzinfo is None:
            published = published.replace(tzinfo=UTC)
    except (ValueError, AttributeError):
        published = None
    media_urls: list[str] = []
    if media.get("media_type") in ("IMAGE", "CAROUSEL_ALBUM") and str(
        media.get("media_url", "")
    ).startswith("http"):
        media_urls.append(str(media["media_url"]))
    return Item(
        platform="instagram",
        external_id=mid,
        url=permalink,
        canonical_url=canonicalize_url(permalink),
        author="",
        title=normalize_text(caption[:160] or permalink, max_chars=500),
        text=normalize_text(caption, max_chars=5000),
        media_urls=media_urls,
        published_at=published,
        metrics={
            "likes": int(media.get("like_count", 0) or 0),
            "comments": int(media.get("comments_count", 0) or 0),
        },
        language=language,
        raw={"media_type": str(media.get("media_type", "") or "")},
    )


class InstagramCollector(BaseCollector):
    platform = "instagram"

    def __init__(
        self,
        access_token: str | None = None,
        business_id: str | None = None,
        per_min: int = 15,
        preferred_tier: str | None = None,
    ) -> None:
        self.access_token = (
            access_token if access_token is not None else os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        )
        self.business_id = (
            business_id if business_id is not None else os.getenv("INSTAGRAM_BUSINESS_ID", "")
        )
        self.per_min = per_min
        self.preferred_tier = preferred_tier or os.getenv("INSTAGRAM_TIER", "official_api")

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        targets = getattr(niche, "targets", None)
        hashtags = [
            h.lstrip("#").lower() for h in (getattr(targets, "instagram_hashtags", []) or [])
        ]
        accounts = list(getattr(targets, "instagram_accounts", []) or [])
        keywords = [k.lower() for k in (getattr(niche, "keywords_include", []) or [])]
        language = getattr(niche, "language", "en") or "en"
        if not hashtags and not accounts and not keywords:
            return CollectorResult(
                items=[],
                errors=["no instagram_hashtags/accounts or keywords configured"],
                tier_used="disabled",
            )
        terms = hashtags + [a.lstrip("@") for a in accounts]
        errors: list[str] = []
        if "official_api" in self._chain() and self.access_token and self.business_id:
            result = await self._own_media_collect(hashtags, keywords, since, limit, language)
            errors.extend(result.errors)
            if result.items:
                return result
        elif "official_api" in self._chain():
            errors.append(
                "missing INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ID "
                "(Graph API covers your own business account only)"
            )
        if "provider" in self._chain() and provider_available():
            try:
                provider = get_provider()
                assert provider is not None
                items = await provider.fetch("instagram", terms or keywords, since, limit)
                if items:
                    errors.append("official API unavailable — used provider fallback")
                    return CollectorResult(
                        items=items, errors=errors, quota_used=0, tier_used="provider"
                    )
                errors.append("provider returned 0 items")
            except ProviderError as e:
                errors.append(f"provider: {e}")
        elif "provider" in self._chain():
            errors.append("PROVIDER_BASE_URL not set (no provider fallback)")
        errors.append(
            "note: hashtag search needs an approved Meta app; without one, monitor via "
            "your own account media + " + manual_hint("instagram")
        )
        return CollectorResult(items=[], errors=errors, quota_used=0, tier_used="disabled")

    def _chain(self) -> list[str]:
        if self.preferred_tier == "provider":
            return ["provider"]
        if self.preferred_tier in ("manual", "disabled"):
            return []
        return ["official_api", "provider"]

    async def _own_media_collect(
        self, hashtags: list[str], keywords: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        items: list[Item] = []
        errors: list[str] = []
        quota_used = 0
        limiter = get_limiter("instagram", self.per_min)
        needles = [h for h in hashtags] + [k for k in keywords]
        try:
            async with create_client() as client:
                resp = await polite_get(
                    client,
                    limiter,
                    f"https://graph.facebook.com/{GRAPH_VERSION}/{self.business_id}/media",
                    {
                        "fields": (
                            "id,caption,like_count,comments_count,"
                            "timestamp,permalink,media_url,media_type"
                        ),
                        "limit": min(max(limit * 3, 10), 100),
                        "access_token": self.access_token,
                    },
                )
                quota_used += 1
                if resp.status_code in (401, 403):
                    errors.append(
                        f"media: HTTP {resp.status_code} (bad/expired token or no permission)"
                    )
                    return CollectorResult(
                        items=[], errors=errors, quota_used=quota_used, tier_used="official_api"
                    )
                resp.raise_for_status()
                for media in resp.json().get("data", []):
                    if len(items) >= limit:
                        break
                    caption = str(media.get("caption", "") or "").lower()
                    if needles and not any(n in caption for n in needles if n):
                        continue
                    item = media_to_item(media, language)
                    if item is None:
                        continue
                    if item.published_at is not None and item.published_at < since:
                        continue
                    items.append(item)
        except Exception as e:  # noqa: BLE001 - never crash the run
            errors.append(f"media: {type(e).__name__}: {e}")
        if not items and not errors:
            errors.append("own account has no recent media matching niche hashtags/keywords")
        return CollectorResult(
            items=items, errors=errors, quota_used=quota_used, tier_used="official_api"
        )

    def tier_status(self) -> tuple[str, str]:
        if os.getenv("INSTAGRAM_ACCESS_TOKEN") and os.getenv("INSTAGRAM_BUSINESS_ID"):
            parts = ["official_api: token+business id present (own-account media)"]
        else:
            parts = [
                "official_api: missing INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_BUSINESS_ID"
                " (Graph API covers own business account only)"
            ]
        parts.append(
            "provider: configured"
            if provider_available()
            else "provider: PROVIDER_BASE_URL not set"
        )
        parts.append("manual: always available via --manual-file")
        return ("official_api", "; ".join(parts))
