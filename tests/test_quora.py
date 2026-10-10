"""Phase 3: Quora adapter tests (RECORDED FIXTURES, respx-mocked HTTP).

Ground truth baked into these tests: Quora has no official API and no public
topic RSS, so the default path must degrade to provider/manual gracefully.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.collectors.providers import reset_provider_cache
from newsletter_machine.collectors.quora import QuoraCollector
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)
PROVIDER_URL = "https://provider.example.com/ingest"


def _niche() -> NicheConfig:
    return NicheConfig(id="n", name="N", targets=PlatformTargets(quora_topics=["Marketing"]))


async def test_default_degrades_to_manual_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.delenv("PROVIDER_BASE_URL", raising=False)
    res = await QuoraCollector(per_min=0).collect(_niche(), SINCE, 5)
    assert res.items == []
    assert res.tier_used == "disabled"
    assert any("no official API" in e for e in res.errors)
    assert any("manual-file" in e for e in res.errors)


@respx.mock
async def test_provider_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.setenv("PROVIDER_BASE_URL", PROVIDER_URL)
    try:
        payload = json.loads((FIX / "provider_response.json").read_text(encoding="utf-8"))
        respx.post(PROVIDER_URL).mock(return_value=Response(200, json=payload))
        res = await QuoraCollector(per_min=0).collect(_niche(), SINCE, 5)
        assert res.tier_used == "provider"
        assert len(res.items) == 2
    finally:
        reset_provider_cache()


@respx.mock
async def test_explicit_rss_tier_fails_gracefully() -> None:
    respx.get(url__regex=r"https://www\.quora\.com/topic/.*").mock(
        return_value=Response(403, text="blocked")
    )
    res = await QuoraCollector(per_min=0, preferred_tier="rss").collect(_niche(), SINCE, 5)
    assert res.items == []
    assert res.tier_used == "disabled"  # provider unset, so nothing produced items
    assert any("403" in e and "expected" in e for e in res.errors)


async def test_no_topics_is_disabled() -> None:
    res = await QuoraCollector(per_min=0).collect(NicheConfig(id="n", name="N"), SINCE, 5)
    assert "no quora_topics" in res.errors[0]


def test_tier_status_states_no_official_api() -> None:
    tier, note = QuoraCollector(per_min=0).tier_status()
    assert tier == "manual"
    assert "no official API" in note
