"""Blogs/RSS collector: feed discovery, feedparser parsing, trafilatura full text.

Tier: rss (no credentials). Sitemap fallback: when a feed URL fails and the
niche lists blog_domains, we try <domain>/sitemap.xml and take fresh <loc>
URLs as lightweight items (title falls back to the URL).
"""

from __future__ import annotations

import hashlib
import html as html_lib
import re
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

import feedparser
import httpx

from newsletter_machine.collectors.base import BaseCollector, CollectorResult, Item
from newsletter_machine.collectors.http import create_client, get_limiter, polite_get
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text

MAX_FULLTEXT_FETCHES_PER_RUN = 10
FULLTEXT_MIN_SUMMARY_CHARS = 500


def _entry_published(entry: Any) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime.fromtimestamp(time.mktime(parsed), tz=UTC)
            except (OverflowError, OSError, ValueError):
                continue
    for key in ("published", "updated", "pubDate"):
        raw = entry.get(key, "") if isinstance(entry, dict) else getattr(entry, key, "")
        if raw:
            try:
                dt = parsedate_to_datetime(str(raw))
                if dt is not None and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except (TypeError, ValueError):
                continue
    return None


def _entry_text(entry: Any) -> str:
    summary = getattr(entry, "summary", "") or (
        entry.get("summary", "") if isinstance(entry, dict) else ""
    )
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", str(summary or "")))
    return normalize_text(text, max_chars=5000)


def _entry_media(entry: Any) -> list[str]:
    urls: list[str] = []
    for key in ("media_content", "media_thumbnail", "enclosures"):
        vals = getattr(entry, key, None) or (entry.get(key, []) if isinstance(entry, dict) else [])
        for v in vals or []:
            if isinstance(v, dict):
                u = v.get("url", "")
            else:
                u = getattr(v, "url", "") or getattr(v, "href", "")
            if u and u.startswith("http"):
                urls.append(u)
    return urls[:3]


def _entry_id(entry: Any, link: str) -> str:
    raw = getattr(entry, "id", "") or (entry.get("id", "") if isinstance(entry, dict) else "")
    if raw:
        return normalize_text(str(raw), max_chars=512)
    return hashlib.sha256(link.encode("utf-8")).hexdigest()[:32]


def extract_fulltext(html: str, url: str) -> str:
    """Extract readable text with trafilatura; '' on any failure."""
    try:
        from trafilatura import extract

        text = extract(html, include_comments=False, include_tables=False, url=url)
        return normalize_text(text or "", max_chars=20000)
    except Exception:
        return ""


def parse_sitemap_locs(xml_text: str, max_urls: int = 20) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    locs: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("loc") and elem.text:
            url = elem.text.strip()
            if url.startswith("http"):
                locs.append(url)
            if len(locs) >= max_urls:
                break
    return locs


_ASSET_EXTENSIONS = frozenset(
    {
        ".svg",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".ico",
        ".pdf",
        ".css",
        ".js",
        ".woff",
        ".woff2",
        ".mp4",
        ".zip",
        ".xml",
    }
)


def is_article_like_url(url: str) -> bool:
    """Reject sitemap entries that are clearly assets, not articles."""
    path = urlsplit(url.lower()).path
    return not any(path.endswith(ext) for ext in _ASSET_EXTENSIONS)


class BlogsCollector(BaseCollector):
    platform = "blogs"

    def __init__(
        self, per_min: int = 60, fulltext_budget: int = MAX_FULLTEXT_FETCHES_PER_RUN
    ) -> None:
        self.per_min = per_min
        self.fulltext_budget = fulltext_budget

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        items: list[Item] = []
        errors: list[str] = []
        quota_used = 0
        feeds = list(getattr(getattr(niche, "targets", None), "blog_feeds", []) or [])
        domains = list(getattr(getattr(niche, "targets", None), "blog_domains", []) or [])
        language = getattr(niche, "language", "en") or "en"
        if not feeds and not domains:
            return CollectorResult(
                items=[], errors=["no blog_feeds or blog_domains configured"], tier_used="rss"
            )

        limiter = get_limiter("blogs", self.per_min)
        per_feed = max(1, limit // max(1, len(feeds))) if feeds else limit
        fulltext_left = self.fulltext_budget

        try:
            async with create_client() as client:
                for feed_url in feeds:
                    if len(items) >= limit:
                        break
                    feed_count = 0
                    try:
                        resp = await polite_get(client, limiter, feed_url)
                        quota_used += 1
                        if resp.status_code >= 400:
                            errors.append(f"feed {feed_url}: HTTP {resp.status_code}")
                            continue
                        parsed = feedparser.parse(resp.content)
                        if parsed.bozo and not parsed.entries:
                            errors.append(f"feed {feed_url}: unparseable ({parsed.bozo_exception})")
                            continue
                        for entry in parsed.entries:
                            if len(items) >= limit or feed_count >= per_feed:
                                break
                            link = getattr(entry, "link", "") or ""
                            if not link:
                                continue
                            published = _entry_published(entry)
                            if published is not None and published < since:
                                continue
                            summary = _entry_text(entry)
                            title = normalize_text(
                                getattr(entry, "title", "") or "", max_chars=1000
                            )
                            fulltext = ""
                            if len(summary) < FULLTEXT_MIN_SUMMARY_CHARS and fulltext_left > 0:
                                fulltext_left -= 1
                                try:
                                    art = await polite_get(client, limiter, link)
                                    quota_used += 1
                                    if art.status_code < 400 and "text/html" in art.headers.get(
                                        "content-type", "text/html"
                                    ):
                                        fulltext = extract_fulltext(art.text, link)
                                except Exception as e:  # noqa: BLE001 - article fetch is best-effort
                                    errors.append(f"article {link}: {type(e).__name__}")
                            text = fulltext or summary
                            canonical = canonicalize_url(link)
                            feed_count += 1
                            items.append(
                                Item(
                                    platform="blogs",
                                    external_id=_entry_id(entry, link),
                                    url=link,
                                    canonical_url=canonical,
                                    author=normalize_text(
                                        getattr(entry, "author", "") or "", max_chars=512
                                    ),
                                    title=title or canonical,
                                    text=text,
                                    media_urls=_entry_media(entry),
                                    published_at=published,
                                    metrics={"feed": feed_url},
                                    language=language,
                                    raw={"feed": feed_url, "summary": summary[:2000]},
                                )
                            )
                    except Exception as e:  # noqa: BLE001 - one bad feed never kills the run
                        errors.append(f"feed {feed_url}: {type(e).__name__}: {e}")
                        # Sitemap fallback for this feed's domain
                        try:
                            host = urlsplit(feed_url).hostname or ""
                            locs = await self._sitemap_fallback(
                                client, limiter, host, limit - len(items)
                            )
                            for loc in locs:
                                canonical = canonicalize_url(loc)
                                items.append(
                                    Item(
                                        platform="blogs",
                                        external_id=hashlib.sha256(loc.encode()).hexdigest()[:32],
                                        url=loc,
                                        canonical_url=canonical,
                                        title=canonical,
                                        language=language,
                                        raw={"via": "sitemap-fallback"},
                                    )
                                )
                            if locs:
                                quota_used += 1
                        except Exception as inner:  # noqa: BLE001
                            errors.append(f"sitemap fallback {feed_url}: {inner}")

                # Domain-level sitemap fallback when no feeds configured (or all failed)
                if not items and domains:
                    for domain in domains:
                        if len(items) >= limit:
                            break
                        try:
                            locs = await self._sitemap_fallback(
                                client, limiter, domain, limit - len(items)
                            )
                            quota_used += 1
                            for loc in locs:
                                canonical = canonicalize_url(loc)
                                items.append(
                                    Item(
                                        platform="blogs",
                                        external_id=hashlib.sha256(loc.encode()).hexdigest()[:32],
                                        url=loc,
                                        canonical_url=canonical,
                                        title=canonical,
                                        language=language,
                                        raw={"via": "sitemap-fallback"},
                                    )
                                )
                        except Exception as e:  # noqa: BLE001
                            errors.append(f"sitemap {domain}: {type(e).__name__}: {e}")
        except Exception as e:  # noqa: BLE001 - collector contract: never crash
            errors.append(f"blogs collector fatal: {type(e).__name__}: {e}")

        # per-feed cap already enforced via per_feed intent; hard cap here
        return CollectorResult(
            items=items[:limit], errors=errors, quota_used=quota_used, tier_used="rss"
        )

    async def _sitemap_fallback(
        self, client: httpx.AsyncClient, limiter: Any, domain_or_host: str, limit: int
    ) -> list[str]:
        host = (domain_or_host or "").strip().strip("/")
        if not host:
            return []
        if "://" in host:
            host = urlsplit(host).hostname or host
        for candidate in (f"https://{host}/sitemap.xml", f"http://{host}/sitemap.xml"):
            try:
                resp = await polite_get(client, limiter, candidate)
                if resp.status_code >= 400 or "<loc" not in resp.text:
                    continue
                # Sitemap index? Follow the first child sitemaps instead of storing them.
                if "sitemapindex" in resp.text[:2000]:
                    collected: list[str] = []
                    for child in parse_sitemap_locs(resp.text, max_urls=2):
                        try:
                            sub = await polite_get(client, limiter, child)
                            if sub.status_code < 400:
                                for loc in parse_sitemap_locs(sub.text, max_urls=limit):
                                    if is_article_like_url(loc):
                                        collected.append(loc)
                                    if len(collected) >= limit:
                                        break
                        except Exception:
                            continue
                        if len(collected) >= limit:
                            break
                    return collected[: max(1, limit)]
                return [
                    u
                    for u in parse_sitemap_locs(resp.text, max_urls=limit * 2)
                    if is_article_like_url(u)
                ][: max(1, limit)]
            except Exception:
                continue
        return []

    def tier_status(self) -> tuple[str, str]:
        return ("rss", "RSS needs no credentials; ready")
