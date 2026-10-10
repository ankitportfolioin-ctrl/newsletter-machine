"""Analysis orchestration: payload building, momentum, validation + grounding.

Pipeline: build_analysis_input(report, niche, date) -> run_analysis(payload,
client) -> AnalysisResult. Grounding rules (spec hard rules):
- schema validated with pydantic; live clients get up to 3 attempts on
  invalid JSON/schema (stub gets 1 — it is deterministic).
- every item_key must exist in the payload; entries without a valid source
  are dropped (top stories, trends, highlights, questions, creators,
  opportunities), never kept.
- quotes must additionally be verbatim substrings (normalized) of the cited
  item's title+text, else dropped. Counts of dropped claims are returned for
  the diagnostics footer.
Momentum is computed deterministically from member ages (median <24h rising,
<72h steady, else fading) — the LLM writes notes, never the label.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from newsletter_machine.llm.base import LLMClient, LLMError
from newsletter_machine.llm.schemas import AnalysisResult


def compute_momentum(ages_hours: list[float]) -> str:
    if not ages_hours:
        return "steady"
    median = sorted(ages_hours)[len(ages_hours) // 2]
    if median < 24:
        return "rising"
    if median < 72:
        return "steady"
    return "fading"


def build_analysis_input(
    report: Any, niche: Any, date_str: str, now: datetime | None = None, max_items: int = 25
) -> dict[str, Any]:
    """Flatten a PipelineReport into the LLM payload (texts truncated)."""
    moment = now or datetime.now(UTC)
    items: list[dict[str, Any]] = []
    key_to_cluster: dict[str, str] = {}
    for cluster in report.clusters:
        for key in cluster.member_keys:
            key_to_cluster.setdefault(key, cluster.label)
    for entry in report.ranked[:max_items]:
        doc = entry.doc
        items.append(
            {
                "key": doc.key,
                "platform": doc.platform,
                "url": doc.url,
                "title": doc.title,
                "text": (doc.text or "")[:1500],
                "author": doc.author,
                "score": entry.total,
                "cluster": key_to_cluster.get(doc.key, "general"),
            }
        )
    clusters = []
    for cluster in report.clusters:
        ages: list[float] = []
        for entry in report.ranked:
            if entry.doc.key in cluster.member_keys and entry.doc.published_at is not None:
                ages.append((moment - entry.doc.published_at).total_seconds() / 3600.0)
        clusters.append(
            {
                "label": cluster.label,
                "momentum": compute_momentum(ages),
                "keys": list(cluster.member_keys),
            }
        )
    coverage: dict[str, int] = {}
    for entry in report.ranked:
        coverage[entry.doc.platform] = coverage.get(entry.doc.platform, 0) + 1
    return {
        "niche": {
            "id": str(getattr(niche, "id", "")),
            "name": str(getattr(niche, "name", "")),
            "description": str(getattr(niche, "description", "") or ""),
        },
        "date": date_str,
        "items": items,
        "clusters": clusters,
        "coverage": coverage,
        "total_items": len(report.ranked),
    }


def _normalize_span(text: str) -> str:
    return " ".join((text or "").lower().split())


def ground_analysis(
    raw: dict[str, Any], payload: dict[str, Any]
) -> tuple[AnalysisResult, dict[str, int]]:
    """Validate + ground. Returns (result, dropped_counts). Raises ValidationError."""
    # Ensure tldr is never empty (OpenRouter models sometimes return empty)
    if not raw.get("tldr"):
        # Try to build a fallback from top stories or items
        fallback = []
        for entry in payload.get("items", [])[:5]:
            fallback.append(entry.get("title", ""))
            if len(fallback) >= 3:
                break
        if fallback:
            raw["tldr"] = fallback[:5]
        else:
            raw["tldr"] = ["No summary available for this edition."]
    
    result = AnalysisResult.model_validate(raw)
    valid_keys = {entry["key"] for entry in payload.get("items", [])}
    texts = {
        entry["key"]: _normalize_span(f"{entry.get('title', '')} {entry.get('text', '')}")
        for entry in payload.get("items", [])
    }
    dropped: dict[str, int] = {}

    def keep_keys(keys: list[str]) -> list[str]:
        return [k for k in keys if k in valid_keys]

    kept_stories = [
        s for s in result.top_stories if any(r.item_key in valid_keys for r in s.sources)
    ]
    dropped["top_stories"] = len(result.top_stories) - len(kept_stories)
    result.top_stories = [
        s.model_copy(update={"sources": [r for r in s.sources if r.item_key in valid_keys]})
        for s in kept_stories
    ]
    kept_trends = [t for t in result.trends if keep_keys(t.item_keys)]
    dropped["trends"] = len(result.trends) - len(kept_trends)
    result.trends = kept_trends
    kept_highlights = [h for h in result.platform_highlights if keep_keys(h.item_keys)]
    dropped["platform_highlights"] = len(result.platform_highlights) - len(kept_highlights)
    result.platform_highlights = kept_highlights
    kept_quotes = []
    for quote in result.quotes:
        source_text = texts.get(quote.item_key, "")
        if (
            quote.item_key in valid_keys
            and len(_normalize_span(quote.text)) >= 20
            and (_normalize_span(quote.text) in source_text)
        ):
            kept_quotes.append(quote)
    dropped["quotes"] = len(result.quotes) - len(kept_quotes)
    result.quotes = kept_quotes
    kept_questions = [q for q in result.questions if q.item_key in valid_keys]
    dropped["questions"] = len(result.questions) - len(kept_questions)
    result.questions = kept_questions
    kept_opps = [o for o in result.opportunities if keep_keys(o.item_keys)]
    dropped["opportunities"] = len(result.opportunities) - len(kept_opps)
    result.opportunities = kept_opps[:10]
    kept_creators = [c for c in result.creator_watch if keep_keys(c.item_keys)]
    dropped["creator_watch"] = len(result.creator_watch) - len(kept_creators)
    result.creator_watch = kept_creators
    return result, dropped


async def run_analysis(
    payload: dict[str, Any], client: LLMClient, max_attempts: int | None = None
) -> tuple[AnalysisResult, dict[str, int]]:
    """Call the client, validate + ground. Retries live clients on bad output."""
    attempts = max_attempts or (3 if getattr(client, "live", False) else 1)
    last_error: Exception | None = None
    for _ in range(max(1, attempts)):
        try:
            raw = await client.analyze(payload)
            if not isinstance(raw, dict):
                raise LLMError("client did not return a JSON object")
            return ground_analysis(raw, payload)
        except ValidationError as e:
            last_error = e
            continue
        except (LLMError, ValueError) as e:
            last_error = e
            if not getattr(client, "live", False):
                break
            continue
    raise LLMError(f"analysis failed after {attempts} attempt(s): {last_error}")
