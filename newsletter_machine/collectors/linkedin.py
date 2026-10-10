"""LinkedIn collector with honest tier chain.

Hard truth this module is built around: LinkedIn's official API exposes NO
public/keyword post search. What it does offer is identity verification
(OpenID `/v2/userinfo`) and organization content APIs that need an org URN and
special permissions — out of scope for a niche monitor.

Tiers:
  official_api — verifies LINKEDIN_ACCESS_TOKEN via /v2/userinfo (proves the
      credential works; quota_used=1) and reports that content search is
      unavailable, so the diagnostics footer tells the truth.
  provider     — third-party snapshots via the provider interface.
  manual       — guidance: --manual-file … --manual-platform linkedin.

ToS: official endpoints only; no profile/post scraping.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from newsletter_machine.collectors.base import BaseCollector, CollectorResult
from newsletter_machine.collectors.http import create_client, get_limiter, polite_get
from newsletter_machine.collectors.providers import get_provider, manual_hint, provider_available
from newsletter_machine.collectors.providers.base import ProviderError

USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


class LinkedInCollector(BaseCollector):
    platform = "linkedin"

    def __init__(
        self,
        access_token: str | None = None,
        per_min: int = 15,
        preferred_tier: str | None = None,
    ) -> None:
        self.access_token = (
            access_token if access_token is not None else os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        )
        self.per_min = per_min
        self.preferred_tier = preferred_tier or os.getenv("LINKEDIN_TIER", "official_api")

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        targets = getattr(niche, "targets", None)
        queries = list(getattr(targets, "linkedin_queries", []) or [])
        companies = list(getattr(targets, "linkedin_companies", []) or [])
        if not queries and not companies:
            return CollectorResult(
                items=[],
                errors=["no linkedin_queries or linkedin_companies configured"],
                tier_used="disabled",
            )
        terms = queries + companies
        errors: list[str] = []
        quota_used = 0
        official_attempted = "official_api" in self._chain() and bool(self.access_token)
        if official_attempted:
            valid, note, used = await self._verify_token()
            quota_used += used
            if valid:
                errors.append(
                    "token valid (verified via /v2/userinfo) but the official API has no "
                    "public/keyword post search — configure a provider or use manual import"
                )
            else:
                errors.append(note)
        elif "official_api" in self._chain():
            errors.append("missing LINKEDIN_ACCESS_TOKEN")
        if "provider" in self._chain() and provider_available():
            try:
                provider = get_provider()
                assert provider is not None
                items = await provider.fetch("linkedin", terms, since, limit)
                if items:
                    errors.append("official API has no post search — used provider fallback")
                    return CollectorResult(
                        items=items, errors=errors, quota_used=quota_used, tier_used="provider"
                    )
                errors.append("provider returned 0 items")
            except ProviderError as e:
                errors.append(f"provider: {e}")
        elif "provider" in self._chain():
            errors.append("PROVIDER_BASE_URL not set (no provider fallback)")
        errors.append(manual_hint("linkedin"))
        tier_used = "official_api" if official_attempted else "disabled"
        return CollectorResult(items=[], errors=errors, quota_used=quota_used, tier_used=tier_used)

    def _chain(self) -> list[str]:
        if self.preferred_tier == "provider":
            return ["provider"]
        if self.preferred_tier in ("manual", "disabled"):
            return []
        return ["official_api", "provider"]

    async def _verify_token(self) -> tuple[bool, str, int]:
        """Verify the token against OpenID userinfo. Returns (valid, note, quota)."""
        limiter = get_limiter("linkedin", self.per_min)
        try:
            async with create_client(
                headers={"Authorization": f"Bearer {self.access_token}"}
            ) as client:
                resp = await polite_get(client, limiter, USERINFO_URL)
                if resp.status_code in (401, 403):
                    return False, f"token check: HTTP {resp.status_code} (bad/revoked token)", 1
                resp.raise_for_status()
                return True, "token valid", 1
        except Exception as e:  # noqa: BLE001 - verification failure is data, not a crash
            return False, f"token check: {type(e).__name__}: {e}", 0

    def tier_status(self) -> tuple[str, str]:
        parts = [
            "official_api: token present (verifies identity; NO post search endpoint)"
            if os.getenv("LINKEDIN_ACCESS_TOKEN")
            else "official_api: missing LINKEDIN_ACCESS_TOKEN (and API has no post search anyway)"
        ]
        parts.append(
            "provider: configured"
            if provider_available()
            else "provider: PROVIDER_BASE_URL not set"
        )
        parts.append("manual: always available via --manual-file")
        return ("official_api", "; ".join(parts))
