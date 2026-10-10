"""Shared prompt + JSON extraction for the real LLM clients."""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are the analyst for a daily niche newsletter. Given ranked items
and topic clusters, produce a single JSON object matching the required schema exactly.

Hard rules (violations are dropped by the validator, so follow them):
- Every top story, trend, highlight, quote, question, opportunity and creator
  entry must reference item_keys copied VERBATIM from the provided items list.
  Never invent keys, URLs, authors or numbers.
- Quotes must be verbatim substrings of the referenced item's text (20+ chars).
  If no good quote exists, return fewer quotes — never fabricate.
- Summaries stay close to the source text. No claims about items you were not given.
- Use the provided momentum labels for trends as-is.
- tldr: 1-5 bullets. opportunities: 5-10 entries, each with angle + format + hook.
- Reply with ONLY the JSON object (no fences, no commentary)."""

SCHEMA_SKETCH = """{
  "tldr": ["bullet (1-5)"],
  "top_stories": [{"title": "", "summary": "2-3 sentences", "why_it_matters": "",
                   "sources": [{"item_key": "", "platform": "", "url": ""}]}],
  "trends": [{"label": "", "momentum": "rising|steady|fading", "note": "", "item_keys": [""]}],
  "platform_highlights": [{"platform": "", "item_keys": [""], "note": ""}],
  "quotes": [{"text": "verbatim 20+ chars", "author": "", "item_key": "", "url": ""}],
  "questions": [{"question": "", "item_key": "", "url": "", "platform": ""}],
  "opportunities": [{"title": "", "angle": "", "format": "", "hook": "", "item_keys": [""]}],
  "creator_watch": [{"name": "", "platform": "", "note": "", "item_keys": [""]}],
  "action_today": "one actionable takeaway",
  "coverage": {"blogs": 3},
  "confidence_note": "how many items per platform were analyzed"
}"""


def build_user_prompt(payload: dict[str, Any]) -> str:
    items = payload.get("items", [])
    lines = [
        f"Niche: {payload.get('niche', {}).get('name', '')} "
        f"({payload.get('niche', {}).get('id', '')})",
        f"Date: {payload.get('date', '')}",
        f"Items ({len(items)}), ranked by score:",
    ]
    for entry in items:
        lines.append(
            f"- key={entry.get('key')} platform={entry.get('platform')} "
            f"score={entry.get('score', 0):.2f} cluster={entry.get('cluster', '')}\n"
            f"  title: {entry.get('title', '')}\n"
            f"  author: {entry.get('author', '')} url: {entry.get('url', '')}\n"
            f"  text: {(entry.get('text', '') or '')[:1200]}"
        )
    lines.append("Clusters:")
    for cluster in payload.get("clusters", []):
        lines.append(
            f"- {cluster.get('label')} (momentum={cluster.get('momentum')}, "
            f"keys={cluster.get('keys', [])})"
        )
    lines.append(f"Coverage: {payload.get('coverage', {})}")
    lines.append("Return this schema (JSON object only):")
    lines.append(SCHEMA_SKETCH)
    return "\n".join(lines)


def parse_json_object(text: str) -> dict[str, Any]:
    """Strip code fences and parse one JSON object. Raises ValueError."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in model output")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("model output is not a JSON object")
    return parsed
