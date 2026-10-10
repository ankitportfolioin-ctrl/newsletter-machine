"""Phase 2: YouTube collector tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import respx
from httpx import Response

from newsletter_machine.collectors.youtube import VIDEOS_URL, YouTubeCollector
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)


@respx.mock
async def test_api_collect_maps_stats_and_quota() -> None:
    search = json.loads((FIX / "youtube_search.json").read_text(encoding="utf-8"))
    videos = json.loads((FIX / "youtube_videos.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r"https://www\.googleapis\.com/youtube/v3/search.*").mock(
        return_value=Response(200, json=search)
    )
    respx.get(url__regex=r"https://www\.googleapis\.com/youtube/v3/videos.*").mock(
        return_value=Response(200, json=videos)
    )
    niche = NicheConfig(
        id="n", name="N", targets=PlatformTargets(youtube_queries=["AI marketing tools"])
    )
    res = await YouTubeCollector(api_key="fixture-key", per_min=0).collect(niche, SINCE, 10)
    assert res.tier_used == "official_api"
    assert res.errors == []
    assert len(res.items) == 2
    first = next(i for i in res.items if i.external_id == "fixtureVid1")
    assert first.url == "https://www.youtube.com/watch?v=fixtureVid1"
    assert first.metrics == {"views": 12345, "likes": 678, "comments": 90}
    assert first.author == "Fixture Channel"
    assert res.quota_used == 101  # ~100 search + 1 videos.list
    assert VIDEOS_URL.startswith("https://")


@respx.mock
async def test_api_quota_error_degrades_gracefully() -> None:
    respx.get(url__regex=r"https://www\.googleapis\.com/youtube/v3/search.*").mock(
        return_value=Response(403, json={"error": {"errors": [{"reason": "quotaExceeded"}]}})
    )
    niche = NicheConfig(id="n", name="N", targets=PlatformTargets(youtube_queries=["x"]))
    res = await YouTubeCollector(api_key="bad-key", per_min=0).collect(niche, SINCE, 5)
    assert res.items == []
    assert res.tier_used == "official_api"
    assert any("403" in e for e in res.errors)


async def test_missing_key_without_channels_is_disabled() -> None:
    niche = NicheConfig(id="n", name="N", targets=PlatformTargets(youtube_queries=["x"]))
    res = await YouTubeCollector(api_key="", per_min=0).collect(niche, SINCE, 5)
    assert res.items == []
    assert res.tier_used == "disabled"
    assert any("YOUTUBE_API_KEY" in e for e in res.errors)


@respx.mock
async def test_rss_fallback_for_channel_ids() -> None:
    rss = (FIX / "youtube_rss.xml").read_bytes()
    respx.get(url__regex=r"https://www\.youtube\.com/feeds/videos\.xml.*").mock(
        return_value=Response(200, content=rss, headers={"content-type": "application/xml"})
    )
    niche = NicheConfig(
        id="n", name="N", targets=PlatformTargets(youtube_channels=["UCfixture123"])
    )
    res = await YouTubeCollector(api_key="", per_min=0).collect(niche, SINCE, 10)
    assert res.tier_used == "rss"
    assert {i.external_id for i in res.items} == {"fixtureVid1", "fixtureVid2"}
    assert any("fallback" in e for e in res.errors)
