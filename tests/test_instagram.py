"""Phase 3: Instagram adapter tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.collectors.instagram import InstagramCollector
from newsletter_machine.collectors.providers import reset_provider_cache
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)


def _niche() -> NicheConfig:
    return NicheConfig(
        id="n", name="N", targets=PlatformTargets(instagram_hashtags=["aimarketing"])
    )


@respx.mock
async def test_own_media_filtered_by_hashtag() -> None:
    payload = json.loads((FIX / "instagram_media.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r"https://graph\.facebook\.com/.*").mock(
        return_value=Response(200, json=payload)
    )
    res = await InstagramCollector(access_token="tok", business_id="biz123", per_min=0).collect(
        _niche(), SINCE, 10
    )
    assert res.tier_used == "official_api"
    assert res.errors == []
    assert len(res.items) == 1  # only the #AIMarketing caption matches
    item = res.items[0]
    assert item.external_id == "igmedia1"
    assert item.metrics == {"likes": 250, "comments": 12}
    assert item.media_urls == ["https://example.com/ig1.jpg"]


@respx.mock
async def test_expired_token_recorded() -> None:
    respx.get(url__regex=r"https://graph\.facebook\.com/.*").mock(
        return_value=Response(401, json={"error": {"message": "expired"}})
    )
    res = await InstagramCollector(access_token="old", business_id="biz", per_min=0).collect(
        _niche(), SINCE, 5
    )
    assert res.items == []
    assert any("401" in e for e in res.errors)


async def test_missing_creds_point_to_manual(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.delenv("PROVIDER_BASE_URL", raising=False)
    res = await InstagramCollector(access_token="", business_id="", per_min=0).collect(
        _niche(), SINCE, 5
    )
    assert res.items == []
    assert res.tier_used == "disabled"
    assert any("INSTAGRAM_ACCESS_TOKEN" in e for e in res.errors)
    assert any("manual-file" in e for e in res.errors)


async def test_no_targets_is_disabled() -> None:
    res = await InstagramCollector(access_token="t", business_id="b", per_min=0).collect(
        NicheConfig(id="n", name="N"), SINCE, 5
    )
    assert "no instagram_hashtags" in res.errors[0]


def test_tier_status_mentions_own_account_scope() -> None:
    _, note = InstagramCollector(access_token="", business_id="").tier_status()
    assert "own" in note and "provider" in note and "manual" in note
