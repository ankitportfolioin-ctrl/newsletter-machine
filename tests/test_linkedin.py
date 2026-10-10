"""Phase 3: LinkedIn adapter tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.collectors.linkedin import LinkedInCollector
from newsletter_machine.collectors.providers import reset_provider_cache
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)
PROVIDER_URL = "https://provider.example.com/ingest"


def _niche() -> NicheConfig:
    return NicheConfig(id="n", name="N", targets=PlatformTargets(linkedin_queries=["AI marketing"]))


@respx.mock
async def test_valid_token_reports_no_search_endpoint() -> None:
    userinfo = json.loads((FIX / "linkedin_userinfo.json").read_text(encoding="utf-8"))
    respx.get("https://api.linkedin.com/v2/userinfo").mock(
        return_value=Response(200, json=userinfo)
    )
    res = await LinkedInCollector(access_token="good", per_min=0).collect(_niche(), SINCE, 5)
    assert res.items == []
    assert res.tier_used == "official_api"
    assert res.quota_used == 1
    assert any("no public/keyword post search" in e for e in res.errors)
    assert any("manual-file" in e for e in res.errors)


@respx.mock
async def test_bad_token_recorded() -> None:
    respx.get("https://api.linkedin.com/v2/userinfo").mock(return_value=Response(401, text="bad"))
    res = await LinkedInCollector(access_token="bad", per_min=0).collect(_niche(), SINCE, 5)
    assert res.items == []
    assert any("401" in e for e in res.errors)


@respx.mock
async def test_provider_fallback_after_honest_official_note(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_provider_cache()
    monkeypatch.setenv("PROVIDER_BASE_URL", PROVIDER_URL)
    try:
        userinfo = json.loads((FIX / "linkedin_userinfo.json").read_text(encoding="utf-8"))
        respx.get("https://api.linkedin.com/v2/userinfo").mock(
            return_value=Response(200, json=userinfo)
        )
        payload = json.loads((FIX / "provider_response.json").read_text(encoding="utf-8"))
        respx.post(PROVIDER_URL).mock(return_value=Response(200, json=payload))
        res = await LinkedInCollector(access_token="good", per_min=0).collect(_niche(), SINCE, 5)
        assert res.tier_used == "provider"
        assert len(res.items) == 2
        assert any("no post search" in e for e in res.errors)
    finally:
        reset_provider_cache()


async def test_no_token_no_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.delenv("PROVIDER_BASE_URL", raising=False)
    res = await LinkedInCollector(access_token="", per_min=0).collect(_niche(), SINCE, 5)
    assert res.items == []
    assert any("missing LINKEDIN_ACCESS_TOKEN" in e for e in res.errors)
    assert any("manual-file" in e for e in res.errors)


def test_tier_status_is_explicit() -> None:
    tier, note = LinkedInCollector(access_token="").tier_status()
    assert tier == "official_api"
    assert "NO post search" in note or "no post search" in note
