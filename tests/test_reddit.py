"""Phase 2: Reddit collector tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import respx
from httpx import Response

from newsletter_machine.collectors.reddit import RedditCollector
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2020, 1, 1, tzinfo=UTC)


def _niche() -> NicheConfig:
    return NicheConfig(
        id="n",
        name="N",
        keywords_include=["AI marketing"],
        targets=PlatformTargets(subreddits=["marketing"]),
    )


@respx.mock
async def test_oauth_collect_maps_posts() -> None:
    token = json.loads((FIX / "reddit_token.json").read_text(encoding="utf-8"))
    listing = json.loads((FIX / "reddit_hot.json").read_text(encoding="utf-8"))
    respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(200, json=token)
    )
    respx.get(url__regex=r"https://oauth\.reddit\.com/.*").mock(
        return_value=Response(200, json=listing)
    )
    res = await RedditCollector(client_id="id", client_secret="sec", per_min=0).collect(
        _niche(), SINCE, 10
    )
    assert res.tier_used == "official_api"
    assert res.errors == []
    assert len(res.items) >= 2
    first = next(i for i in res.items if i.external_id == "fix001")
    assert first.metrics["upvotes"] == 1234
    assert first.metrics["comments"] == 56
    assert first.url == "https://example.com/fixture-one"
    assert res.quota_used >= 1


@respx.mock
async def test_oauth_bad_credentials_recorded() -> None:
    respx.post("https://www.reddit.com/api/v1/access_token").mock(
        return_value=Response(401, text="unauth")
    )
    res = await RedditCollector(client_id="bad", client_secret="bad", per_min=0).collect(
        _niche(), SINCE, 5
    )
    assert res.items == []
    assert res.tier_used == "official_api"
    assert any("401" in e for e in res.errors)


@respx.mock
async def test_public_fallback_without_credentials() -> None:
    listing = json.loads((FIX / "reddit_hot.json").read_text(encoding="utf-8"))
    respx.get(url__regex=r"https://www\.reddit\.com/r/marketing/hot\.json.*").mock(
        return_value=Response(200, json=listing)
    )
    res = await RedditCollector(client_id="", client_secret="", per_min=0).collect(
        _niche(), SINCE, 10
    )
    assert res.tier_used == "public_json"
    assert len(res.items) == 2
    assert any("fallback" in e for e in res.errors)


async def test_no_targets_is_disabled() -> None:
    niche = NicheConfig(id="n", name="N")
    res = await RedditCollector(client_id="id", client_secret="sec", per_min=0).collect(
        niche, SINCE, 5
    )
    assert res.items == []
    assert "no subreddits" in res.errors[0]
