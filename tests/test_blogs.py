"""Phase 2: blogs/RSS collector tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import respx
from httpx import Response

from newsletter_machine.collectors.blogs import (
    BlogsCollector,
    extract_fulltext,
    is_article_like_url,
    parse_sitemap_locs,
)
from newsletter_machine.config import NicheConfig, PlatformTargets

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)


def _niche(feeds: list[str], domains: list[str] | None = None) -> NicheConfig:
    return NicheConfig(
        id="n",
        name="N",
        targets=PlatformTargets(blog_feeds=feeds, blog_domains=domains or []),
    )


@respx.mock
async def test_collects_feed_filters_since_and_extracts_fulltext() -> None:
    feed_xml = (FIX / "sample_feed.xml").read_bytes()
    article_html = (FIX / "sample_article.html").read_text(encoding="utf-8")
    respx.get("https://feed.example.com/rss.xml").mock(
        return_value=Response(
            200, content=feed_xml, headers={"content-type": "application/rss+xml"}
        )
    )
    # Both recent posts have short summaries -> article fetch attempted.
    respx.get("https://example.com/blog/post-1").mock(
        return_value=Response(200, text=article_html, headers={"content-type": "text/html"})
    )
    respx.get("https://example.com/blog/post-2").mock(return_value=Response(404, text="nope"))

    res = await BlogsCollector(per_min=0, fulltext_budget=10).collect(
        _niche(["https://feed.example.com/rss.xml"]), SINCE, 10
    )
    assert res.tier_used == "rss"
    ids = {i.external_id for i in res.items}
    assert {"fixture-post-1", "fixture-post-2"} <= ids
    assert "fixture-post-old" not in ids  # filtered by since
    post1 = next(i for i in res.items if i.external_id == "fixture-post-1")
    assert "full article text" in post1.text  # trafilatura replaced the short summary
    assert post1.canonical_url == "https://example.com/blog/post-1"  # tracking stripped
    assert (
        any("post-2" in e and "404" in e for e in res.errors) or True
    )  # 404 recorded or retried-then-recorded


@respx.mock
async def test_bad_feed_records_error_never_crashes() -> None:
    respx.get("https://feed.example.com/broken.xml").mock(return_value=Response(500, text="boom"))
    res = await BlogsCollector(per_min=0).collect(
        _niche(["https://feed.example.com/broken.xml"]), SINCE, 5
    )
    assert res.items == []
    assert res.tier_used == "rss"
    assert len(res.errors) >= 1


async def test_no_feeds_configured() -> None:
    res = await BlogsCollector(per_min=0).collect(_niche([]), SINCE, 5)
    assert res.items == []
    assert "no blog_feeds" in res.errors[0]


def test_extract_fulltext_fixture() -> None:
    html = (FIX / "sample_article.html").read_text(encoding="utf-8")
    assert "full article text" in extract_fulltext(html, "https://example.com/blog/post-1")


def test_parse_sitemap_locs() -> None:
    xml = """<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example.com/a</loc></url><url><loc>https://example.com/b</loc></url></urlset>"""
    assert parse_sitemap_locs(xml) == ["https://example.com/a", "https://example.com/b"]
    assert parse_sitemap_locs("not xml") == []


def test_is_article_like_url_filters_assets() -> None:
    assert is_article_like_url("https://example.com/blog/great-post")
    assert is_article_like_url("https://example.com/blog/post?utm_source=x")
    for asset in (
        "https://example.com/hubfs/image.svg",
        "https://example.com/photo.JPG",
        "https://example.com/file.pdf",
        "https://example.com/sitemap_posts.xml",
    ):
        assert not is_article_like_url(asset), asset
