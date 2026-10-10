"""Phase 3: X adapter tier tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.collectors.providers import reset_provider_cache
from newsletter_machine.collectors.x_twitter import XTwitterCollector
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)
PROVIDER_URL = "https://provider.example.com/ingest"


def _niche() -> NicheConfig:
    return NicheConfig(
        id="n",
        name="N",
        targets=PlatformTargets(x_queries=["AI marketing tools"], x_accounts=["somehandle"]),
    )


@respx.mock
async def test_official_search_maps_tweets() -> None:
    payload = json.loads((FIX / "x_search.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r"https://api\.x\.com/2/tweets/search/recent.*").mock(
        return_value=Response(200, json=payload)
    )
    res = await XTwitterCollector(bearer_token="tok", per_min=0).collect(_niche(), SINCE, 10)
    assert res.tier_used == "official_api"
    assert res.errors == []
    assert len(res.items) == 2  # same 2 tweets match both queries; deduped by id
    first = next(i for i in res.items if i.external_id == "fixtureTweet1")
    assert first.url == "https://x.com/fixturemarketer/status/fixtureTweet1"
    assert first.author == "@fixturemarketer"
    assert first.metrics == {"likes": 120, "shares": 15, "comments": 8, "views": 5000}


@respx.mock
async def test_paywall_falls_through_to_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reset_provider_cache()
    monkeypatch.setenv("PROVIDER_BASE_URL", PROVIDER_URL)
    try:
        respx.get(url__regex=r"https://api\.x\.com/2/tweets/search/recent.*").mock(
            return_value=Response(402, text="paywalled")
        )
        payload = json.loads((FIX / "provider_response.json").read_text(encoding="utf-8"))
        respx.post(PROVIDER_URL).mock(return_value=Response(200, json=payload))
        res = await XTwitterCollector(bearer_token="free-tier-tok", per_min=0).collect(
            _niche(), SINCE, 10
        )
        assert res.tier_used == "provider"
        assert any("402" in e for e in res.errors)
        assert len(res.items) == 2
    finally:
        reset_provider_cache()


async def test_no_token_no_provider_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.delenv("PROVIDER_BASE_URL", raising=False)
    monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
    res = await XTwitterCollector(bearer_token="", per_min=0).collect(_niche(), SINCE, 5)
    assert res.items == []
    assert res.tier_used == "disabled"
    assert any("X_BEARER_TOKEN" in e for e in res.errors)
    assert any("manual-file" in e for e in res.errors)


async def test_no_queries_is_disabled() -> None:
    res = await XTwitterCollector(bearer_token="tok", per_min=0).collect(
        NicheConfig(id="n", name="N"), SINCE, 5
    )
    assert res.items == []
    assert "no x_queries" in res.errors[0]


def test_tier_status_mentions_all_tiers(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.delenv("PROVIDER_BASE_URL", raising=False)
    tier, note = XTwitterCollector(bearer_token="").tier_status()
    assert tier == "official_api"
    assert "X_BEARER_TOKEN" in note and "provider" in note and "manual" in note
