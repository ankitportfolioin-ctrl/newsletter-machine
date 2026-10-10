"""LIVE smoke tests (need real credentials + network). Skipped clearly when absent.

Everything else uses RECORDED FIXTURES. With keys set, run tiny live calls:
  YOUTUBE_API_KEY=... REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... pytest -v
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

from newsletter_machine.collectors.reddit import RedditCollector
from newsletter_machine.collectors.youtube import YouTubeCollector
from newsletter_machine.config import NicheConfig, PlatformTargets

NEEDS_YOUTUBE = not bool(os.getenv("YOUTUBE_API_KEY"))
NEEDS_REDDIT = not (os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"))
SINCE = datetime.now(UTC) - timedelta(hours=72)


@pytest.mark.skipif(NEEDS_YOUTUBE, reason="LIVE: set YOUTUBE_API_KEY to run")
async def test_live_youtube_search() -> None:
    niche = NicheConfig(
        id="live", name="live", targets=PlatformTargets(youtube_queries=["AI marketing tools"])
    )
    res = await YouTubeCollector(per_min=0).collect(niche, SINCE, 2)
    assert res.tier_used == "official_api"
    assert isinstance(res.items, list)  # may be empty on quota failure, but must not crash
    print(f"\nLIVE youtube: {len(res.items)} items, errors={res.errors}")


@pytest.mark.skipif(NEEDS_REDDIT, reason="LIVE: set REDDIT_CLIENT_ID/SECRET to run")
async def test_live_reddit_hot() -> None:
    niche = NicheConfig(id="live", name="live", targets=PlatformTargets(subreddits=["marketing"]))
    res = await RedditCollector(per_min=0).collect(niche, SINCE, 2)
    assert res.tier_used in ("official_api", "public_json")
    print(f"\nLIVE reddit: {len(res.items)} items, errors={res.errors}")


@pytest.mark.skipif(False, reason="LIVE-optional: public RSS needs network")
async def test_live_blogs_rss() -> None:
    import os as _os

    if _os.getenv("SKIP_LIVE_RSS"):
        pytest.skip("SKIP_LIVE_RSS set")
    from newsletter_machine.collectors.blogs import BlogsCollector

    niche = NicheConfig(
        id="live",
        name="live",
        targets=PlatformTargets(blog_feeds=["https://marketingaiinstitute.com/blog/rss"]),
    )
    res = await BlogsCollector(per_min=0, fulltext_budget=0).collect(niche, SINCE, 3)
    print(f"\nLIVE blogs: {len(res.items)} items, errors={res.errors}")
    assert res.tier_used == "rss"
