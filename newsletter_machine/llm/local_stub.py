"""Deterministic extractive stub (no network): builds schema-valid analysis.

Every sentence comes from the payload items — titles, first sentences, real
quoted spans — so the stub obeys the same grounding rules as the real LLMs
and the same tests cover both. Templated and plainly labeled, never magic.
"""

from __future__ import annotations

import re
from typing import Any

from newsletter_machine.llm.base import LLMClient

_QUOTE_RE = re.compile(r'"([^"]{20,280})"')
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]")
_FORMATS = ["deep-dive post", "short video", "checklist", "comparison", "Q&A thread"]


def _first_sentences(text: str, count: int = 2) -> str:
    sentences = [s.strip() for s in _SENTENCE_RE.findall(text or "") if s.strip()]
    return " ".join(sentences[:count]) or (text or "")[:200]


class StubLLMClient(LLMClient):
    live = False

    async def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        items: list[dict] = list(payload.get("items", []))
        clusters: list[dict] = list(payload.get("clusters", []))
        coverage: dict = dict(payload.get("coverage", {}))
        niche_name = str(payload.get("niche", {}).get("name", "your niche"))
        total = int(payload.get("total_items", len(items)))

        if not items:
            return {
                "tldr": [
                    f"No items were collected for {niche_name} today — check source health below."
                ],
                "top_stories": [],
                "trends": [],
                "platform_highlights": [],
                "quotes": [],
                "questions": [],
                "opportunities": [],
                "creator_watch": [],
                "action_today": "Add a feed or import links so tomorrow's edition has coverage.",
                "coverage": {},
                "confidence_note": "No items analyzed; coverage is empty.",
            }

        top = items[:7]
        tldr = [f"{entry['title']} [{entry['platform']}]" for entry in items[:5]]
        top_stories = [
            {
                "title": entry["title"],
                "summary": _first_sentences(entry.get("text", "")) or entry["title"],
                "why_it_matters": (
                    f"Ranked #{rank} (score {entry.get('score', 0):.2f}) in topic "
                    f"'{entry.get('cluster', 'general')}'."
                ),
                "sources": [
                    {
                        "item_key": entry["key"],
                        "platform": entry["platform"],
                        "url": entry["url"],
                    }
                ],
            }
            for rank, entry in enumerate(top, start=1)
        ]
        trends = [
            {
                "label": cluster["label"],
                "momentum": cluster.get("momentum", "steady"),
                "note": (
                    f"{len(cluster.get('keys', []))} items; "
                    f"momentum {cluster.get('momentum', 'steady')} by member recency."
                ),
                "item_keys": list(cluster.get("keys", []))[:8],
            }
            for cluster in clusters[:5]
            if cluster.get("keys")
        ]
        by_platform: dict[str, list[dict]] = {}
        for entry in items:
            by_platform.setdefault(entry["platform"], []).append(entry)
        platform_highlights = [
            {
                "platform": platform,
                "item_keys": [e["key"] for e in entries[:2]],
                "note": f"{len(entries)} item(s) from {platform}.",
            }
            for platform, entries in sorted(by_platform.items())
        ]
        quotes = []
        for entry in items:
            for span in _QUOTE_RE.findall(entry.get("text", "") or ""):
                quotes.append(
                    {
                        "text": span.strip(),
                        "author": entry.get("author", ""),
                        "item_key": entry["key"],
                        "url": entry["url"],
                    }
                )
                if len(quotes) >= 5:
                    break
            if len(quotes) >= 5:
                break
        questions = [
            {
                "question": entry["title"],
                "item_key": entry["key"],
                "url": entry["url"],
                "platform": entry["platform"],
            }
            for entry in items
            if entry["platform"] in ("reddit", "quora") and "?" in entry["title"]
        ][:5]
        opportunities = []
        for i, cluster in enumerate(clusters[:5]):
            keys = list(cluster.get("keys", []))[:3]
            if not keys:
                continue
            anchor = next((e for e in items if e["key"] in keys), items[0])
            opportunities.append(
                {
                    "title": f"Create a {_FORMATS[i % len(_FORMATS)]} about {cluster['label']}",
                    "angle": f"Go deeper than '{anchor['title'][:80]}'.",
                    "format": _FORMATS[i % len(_FORMATS)],
                    "hook": anchor["title"],
                    "item_keys": keys,
                }
            )
        while len(opportunities) < min(5, len(items)):
            anchor = items[len(opportunities) % len(items)]
            opportunities.append(
                {
                    "title": f"React to '{anchor['title'][:70]}' with your own take",
                    "angle": "Add data or a counter-example the thread missed.",
                    "format": _FORMATS[len(opportunities) % len(_FORMATS)],
                    "hook": anchor["title"],
                    "item_keys": [anchor["key"]],
                }
            )
        authors: dict[str, dict] = {}
        for entry in items:
            name = (entry.get("author") or "").strip()
            if not name:
                continue
            bucket = authors.setdefault(name, {"platforms": set(), "count": 0, "keys": []})
            bucket["platforms"].add(entry["platform"])
            bucket["count"] += 1
            bucket["keys"].append(entry["key"])
        creator_watch = [
            {
                "name": name,
                "platform": sorted(info["platforms"])[0],
                "note": f"{info['count']} item(s) in today's batch.",
                "item_keys": info["keys"][:3],
            }
            for name, info in sorted(authors.items(), key=lambda kv: -kv[1]["count"])[:3]
        ]
        best = items[0]
        platforms = ", ".join(f"{p}: {c}" for p, c in sorted(coverage.items()))
        return {
            "tldr": tldr,
            "top_stories": top_stories,
            "trends": trends,
            "platform_highlights": platform_highlights,
            "quotes": quotes,
            "questions": questions,
            "opportunities": opportunities[:10],
            "creator_watch": creator_watch,
            "action_today": f"Read the top-ranked story first: {best['title']} ({best['url']})",
            "coverage": coverage,
            "confidence_note": (
                f"Stub analysis of {total} items across {len(coverage)} platform(s) "
                f"({platforms}). Extractive only — no generated claims."
            ),
        }
