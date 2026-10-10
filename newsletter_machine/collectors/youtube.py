"""YouTube collector: Data API v3 search + video stats, RSS fallback for channels.

Official API (needs YOUTUBE_API_KEY):
  search.list (per query / channelId) -> videoIds, then videos.list (50/batch)
  for snippet + statistics. quota_used tracks ~100 units per search call + 1
  per videos.list call (documented estimates, not live quota balances).

No key? If the niche lists channel IDs starting with "UC", we fall back to the
public channel RSS feeds (https://www.youtube.com/feeds/videos.xml) and report
tier_used="rss". Otherwise we degrade gracefully with tier_used="disabled".

Transcripts: the Data API has no transcript endpoint, so we store the video
description as text and never fabricate captions.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import feedparser

from newsletter_machine.collectors.base import BaseCollector, CollectorResult, Item
from newsletter_machine.collectors.http import create_client, get_limiter, polite_get
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
CHANNEL_RSS = "https://www.youtube.com/feeds/videos.xml"


def _parse_yt_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _to_int(value: Any) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


class YouTubeCollector(BaseCollector):
    platform = "youtube"

    def __init__(self, api_key: str | None = None, per_min: int = 30) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("YOUTUBE_API_KEY", "")
        self.per_min = per_min

    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        targets = getattr(niche, "targets", None)
        queries = list(getattr(targets, "youtube_queries", []) or [])
        channels = list(getattr(targets, "youtube_channels", []) or [])
        language = getattr(niche, "language", "en") or "en"
        if not queries and not channels:
            return CollectorResult(
                items=[], errors=["no youtube_queries/channels configured"], tier_used="disabled"
            )

        if not self.api_key:
            channel_ids = [c for c in channels if c.startswith("UC")]
            if channel_ids:
                return await self._rss_fallback(channel_ids, since, limit, language)
            return CollectorResult(
                items=[],
                errors=["missing YOUTUBE_API_KEY (set it, or list UC… channel IDs for RSS)"],
                tier_used="disabled",
            )
        try:
            return await self._api_collect(queries, channels, since, limit, language)
        except Exception as e:  # noqa: BLE001 - contract: never crash
            return CollectorResult(
                items=[], errors=[f"youtube: {type(e).__name__}: {e}"], tier_used="official_api"
            )

    async def _api_collect(
        self, queries: list[str], channels: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        items: list[Item] = []
        errors: list[str] = []
        quota_used = 0
        limiter = get_limiter("youtube", self.per_min)
        since_rfc = since.astimezone(UTC).isoformat().replace("+00:00", "Z")
        video_ids: list[str] = []

        async with create_client() as client:
            searches: list[dict[str, Any]] = [{"q": q} for q in queries]
            for ch in channels:
                if ch.startswith("UC"):
                    searches.append({"channelId": ch})
                else:
                    searches.append({"q": ch})
            per_search = max(1, min(25, max(1, limit // max(1, len(searches)))))
            for params in searches:
                if len(video_ids) >= limit:
                    break
                try:
                    resp = await polite_get(
                        client,
                        limiter,
                        SEARCH_URL,
                        {
                            "key": self.api_key,
                            "part": "snippet",
                            "type": "video",
                            "order": "date",
                            "maxResults": per_search,
                            "publishedAfter": since_rfc,
                            **params,
                        },
                    )
                    quota_used += 100
                    if resp.status_code == 403:
                        errors.append(f"search {params}: HTTP 403 (key invalid or quota exceeded)")
                        continue
                    resp.raise_for_status()
                    for entry in resp.json().get("items", []):
                        vid = (entry.get("id") or {}).get("videoId", "")
                        if vid and vid not in video_ids:
                            video_ids.append(vid)
                except Exception as e:  # noqa: BLE001 - one bad search never kills the run
                    errors.append(f"search {params}: {type(e).__name__}: {e}")

            # Stats in batches of 50
            details: dict[str, dict] = {}
            for i in range(0, len(video_ids[:limit]), 50):
                batch = video_ids[i : i + 50]
                try:
                    resp = await polite_get(
                        client,
                        limiter,
                        VIDEOS_URL,
                        {"key": self.api_key, "part": "snippet,statistics", "id": ",".join(batch)},
                    )
                    quota_used += 1
                    resp.raise_for_status()
                    for entry in resp.json().get("items", []):
                        details[entry.get("id", "")] = entry
                except Exception as e:  # noqa: BLE001
                    errors.append(f"videos.list batch: {type(e).__name__}: {e}")

            for vid in video_ids[:limit]:
                entry = details.get(vid, {})
                snippet = entry.get("snippet", {}) or {}
                stats = entry.get("statistics", {}) or {}
                url = f"https://www.youtube.com/watch?v={vid}"
                published = _parse_yt_dt(snippet.get("publishedAt"))
                if published is not None and published < since:
                    continue
                items.append(
                    Item(
                        platform="youtube",
                        external_id=vid,
                        url=url,
                        canonical_url=canonicalize_url(url),
                        author=normalize_text(snippet.get("channelTitle", ""), max_chars=512),
                        title=normalize_text(snippet.get("title", "") or vid, max_chars=1000),
                        text=normalize_text(snippet.get("description", ""), max_chars=5000),
                        media_urls=[
                            f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                        ],
                        published_at=published,
                        metrics={
                            "views": _to_int(stats.get("viewCount")),
                            "likes": _to_int(stats.get("likeCount")),
                            "comments": _to_int(stats.get("commentCount")),
                        },
                        language=language,
                        raw={"search": True},
                    )
                )
        return CollectorResult(
            items=items, errors=errors, quota_used=quota_used, tier_used="official_api"
        )

    async def _rss_fallback(
        self, channel_ids: list[str], since: datetime, limit: int, language: str
    ) -> CollectorResult:
        items: list[Item] = []
        errors = ["YOUTUBE_API_KEY missing — used public channel RSS fallback (no view counts)"]
        quota_used = 0
        limiter = get_limiter("youtube-rss", 30)
        async with create_client() as client:
            for cid in channel_ids:
                if len(items) >= limit:
                    break
                try:
                    resp = await polite_get(client, limiter, CHANNEL_RSS, {"channel_id": cid})
                    quota_used += 1
                    if resp.status_code >= 400:
                        errors.append(f"channel {cid}: HTTP {resp.status_code}")
                        continue
                    for entry in feedparser.parse(resp.content).entries:
                        if len(items) >= limit:
                            break
                        vid = getattr(entry, "yt_videoid", "") or ""
                        link = getattr(entry, "link", "") or ""
                        if not vid and "v=" in link:
                            vid = link.split("v=")[-1].split("&")[0]
                        if not vid:
                            continue
                        url = f"https://www.youtube.com/watch?v={vid}"
                        items.append(
                            Item(
                                platform="youtube",
                                external_id=vid,
                                url=url,
                                canonical_url=canonicalize_url(url),
                                author=normalize_text(getattr(entry, "author", ""), max_chars=512),
                                title=normalize_text(
                                    getattr(entry, "title", "") or vid, max_chars=1000
                                ),
                                text=normalize_text(getattr(entry, "summary", ""), max_chars=5000),
                                published_at=_parse_yt_dt(getattr(entry, "published", None)),
                                metrics={},
                                language=language,
                                raw={"via": "channel-rss"},
                            )
                        )
                except Exception as e:  # noqa: BLE001
                    errors.append(f"channel {cid}: {type(e).__name__}: {e}")
        return CollectorResult(items=items, errors=errors, quota_used=quota_used, tier_used="rss")

    def tier_status(self) -> tuple[str, str]:
        if os.getenv("YOUTUBE_API_KEY"):
            return ("official_api", "API key present; RSS fallback for UC… channels")
        return ("official_api", "missing YOUTUBE_API_KEY (RSS fallback needs UC… channel IDs)")
