"""Transparent multi-factor scoring (all components stored for audit).

score = w1*recency + w2*engagement + w3*authority + w4*relevance + w5*novelty + w6*feedback

- recency: exponential decay, 0.5**(age_h / half_life_h), half-life 48h default.
- engagement: log1p(total engagement)/sqrt(age_h+2), then MIN-MAX NORMALIZED
  PER PLATFORM within the batch so YouTube view counts can't drown Reddit
  upvotes. No variance on a platform -> 0.5 neutral.
- authority: static per-platform base (configurable), honest proxy for source
  trust until Phase 6+ learns better priors from feedback.
- relevance: keyword match (title x2, text x1; related_terms half weight),
  any exclude-term hit -> 0.0. No keywords configured -> 0.5 neutral.
- novelty: 1.0 unless the same canonical URL was fetched in the last N days
  (DB check, session optional -> 1.0 when no session).
- feedback: platform prior from Feedback rows (up +1 / click +0.5 / down -1,
  mean mapped 0.5+clip*0.3); no feedback -> 0.5 neutral.

Total is a weights-normalized weighted sum in [0, 1], comparable against
niche.min_score. Weights merge niche.weight_overrides over DEFAULT_WEIGHTS.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from newsletter_machine.pipeline.normalize import NormalizedDoc

DEFAULT_WEIGHTS: dict[str, float] = {
    "recency": 0.25,
    "engagement": 0.25,
    "authority": 0.15,
    "relevance": 0.25,
    "novelty": 0.05,
    "feedback": 0.05,
}

PLATFORM_AUTHORITY: dict[str, float] = {
    "youtube": 0.7,
    "blogs": 0.6,
    "reddit": 0.6,
    "x": 0.5,
    "linkedin": 0.5,
    "instagram": 0.5,
    "quora": 0.5,
    "manual": 0.4,
}

ENGAGEMENT_KEYS = ("views", "likes", "comments", "shares", "upvotes")
SIGNAL_VALUES = {"up": 1.0, "click": 0.5, "down": -1.0}
RECENCY_HALF_LIFE_H = 48.0
NOVELTY_DAYS = 7


def merged_weights(overrides: dict[str, float] | None) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    for key, value in (overrides or {}).items():
        if key in weights:
            weights[key] = float(value)
    total = sum(weights.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: v / total for k, v in weights.items()}


def recency_component(published_at: datetime | None, now: datetime) -> float:
    if published_at is None:
        return 0.5
    age_h = (now - published_at).total_seconds() / 3600.0
    if age_h < 0:
        return 1.0
    return 0.5 ** (age_h / RECENCY_HALF_LIFE_H)


def engagement_raw(doc: NormalizedDoc, now: datetime) -> float:
    total = 0.0
    for key in ENGAGEMENT_KEYS:
        value = doc.metrics.get(key, 0)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and value > 0:
            total += value
    if doc.published_at is not None:
        age_h = max(0.0, (now - doc.published_at).total_seconds() / 3600.0)
    else:
        age_h = 24.0
    return math.log1p(total) / math.sqrt(age_h + 2.0)


def relevance_component(doc: NormalizedDoc, niche: Any) -> float:
    include = [str(k).lower() for k in (getattr(niche, "keywords_include", []) or [])]
    exclude = [str(k).lower() for k in (getattr(niche, "keywords_exclude", []) or [])]
    related = [str(k).lower() for k in (getattr(niche, "related_terms", []) or [])]
    title = doc.title.lower()
    text = doc.text.lower()
    if any(term and (term in title or term in text) for term in exclude):
        return 0.0
    if not include and not related:
        return 0.5
    matched = 0.0
    for term in include:
        if not term:
            continue
        if term in title:
            matched += 2.0
        elif term in text:
            matched += 1.0
    for term in related:
        if not term:
            continue
        if term in title:
            matched += 1.0
        elif term in text:
            matched += 0.5
    denominator = 2.0 * len([t for t in include if t]) + 1.0 * len([t for t in related if t])
    return min(1.0, matched / denominator) if denominator > 0 else 0.5


def novelty_component(doc: NormalizedDoc, session: Any | None, days: int = NOVELTY_DAYS) -> float:
    if session is None or not doc.canonical_url:
        return 1.0
    from newsletter_machine.db.models import Item as ItemRow

    cutoff = datetime.now(UTC) - timedelta(days=days)
    query = session.query(ItemRow).filter(
        ItemRow.canonical_url == doc.canonical_url, ItemRow.fetched_at >= cutoff
    )
    if doc.db_id is not None:
        query = query.filter(ItemRow.id != doc.db_id)
    return 0.3 if query.first() is not None else 1.0


def feedback_component(platform: str, session: Any | None) -> dict[str, float]:
    if session is None:
        return {"score": 0.5, "mean": 0.0, "count": 0}
    from newsletter_machine.db.models import Feedback as FeedbackRow
    from newsletter_machine.db.models import Item as ItemRow

    signals = (
        session.query(FeedbackRow.signal)
        .join(ItemRow, FeedbackRow.item_id == ItemRow.id)
        .filter(ItemRow.platform == platform)
        .all()
    )
    values = [SIGNAL_VALUES.get(s, 0.0) for (s,) in signals]
    if not values:
        return {"score": 0.5, "mean": 0.0, "count": 0}
    mean = sum(values) / len(values)
    clipped = max(-1.0, min(1.0, mean))
    return {"score": 0.5 + clipped * 0.3, "mean": mean, "count": len(values)}


@dataclass
class ScoredDoc:
    doc: NormalizedDoc
    components: dict[str, float] = field(default_factory=dict)
    total: float = 0.0


def score_docs(
    docs: list[NormalizedDoc],
    niche: Any,
    session: Any | None = None,
    now: datetime | None = None,
    novelty_days: int = NOVELTY_DAYS,
) -> list[ScoredDoc]:
    """Score a batch; engagement normalized per platform. Returns rank order (desc)."""
    moment = now or datetime.now(UTC)
    weights = merged_weights(getattr(niche, "weight_overrides", None))
    raws = {doc.key: engagement_raw(doc, moment) for doc in docs}
    by_platform: dict[str, list[float]] = {}
    for doc in docs:
        by_platform.setdefault(doc.platform, []).append(raws[doc.key])
    bounds = {p: (min(v), max(v)) for p, v in by_platform.items()}

    scored: list[ScoredDoc] = []
    for doc in docs:
        lo, hi = bounds[doc.platform]
        engagement = 0.5 if hi <= lo else (raws[doc.key] - lo) / (hi - lo)
        feedback = feedback_component(doc.platform, session)
        components = {
            "recency": recency_component(doc.published_at, moment),
            "engagement": engagement,
            "authority": PLATFORM_AUTHORITY.get(doc.platform, 0.4),
            "relevance": relevance_component(doc, niche),
            "novelty": novelty_component(doc, session, novelty_days),
            "feedback": feedback["score"],
        }
        total = sum(weights[k] * components[k] for k in weights)
        scored.append(ScoredDoc(doc=doc, components=components, total=round(total, 4)))
    scored.sort(key=lambda s: s.total, reverse=True)
    return scored


def persist_scores(session: Any, scored: list[ScoredDoc]) -> int:
    """Upsert one ItemScore row per doc with a DB id. Returns rows written."""
    from newsletter_machine.db.models import ItemScore as ItemScoreRow

    written = 0
    for entry in scored:
        if entry.doc.db_id is None:
            continue
        row = session.query(ItemScoreRow).filter_by(item_id=entry.doc.db_id).one_or_none()
        if row is None:
            row = ItemScoreRow(
                item_id=entry.doc.db_id, components_json=entry.components, total=entry.total
            )
            session.add(row)
        else:
            row.components_json = entry.components
            row.total = entry.total
        written += 1
    session.flush()
    return written
