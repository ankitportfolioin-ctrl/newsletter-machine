"""Phase 4: scoring tests — every component unit-checked, then ranked (no network)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from newsletter_machine.config import NicheConfig
from newsletter_machine.db.models import Base, Feedback, Item
from newsletter_machine.db.session import get_engine, make_session_factory
from newsletter_machine.pipeline.normalize import NormalizedDoc
from newsletter_machine.pipeline.scoring import (
    DEFAULT_WEIGHTS,
    engagement_raw,
    feedback_component,
    merged_weights,
    novelty_component,
    persist_scores,
    recency_component,
    relevance_component,
    score_docs,
)

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)


def _niche(**over: object) -> NicheConfig:
    return NicheConfig(
        id="ai",
        name="AI",
        description="",
        keywords_include=["AI marketing", "ChatGPT"],
        keywords_exclude=["crypto"],
        related_terms=["LLM"],
        **over,  # type: ignore[arg-type]
    )


def _doc(key: str = "blogs:a", **over: object) -> NormalizedDoc:
    platform, external = key.split(":", 1)
    base: dict = {
        "key": key,
        "db_id": None,
        "platform": platform,
        "external_id": external,
        "url": f"https://example.com/{external}",
        "canonical_url": f"https://example.com/{external}",
        "author": "",
        "title": "AI marketing tools roundup",
        "text": "ChatGPT workflows and LLM tips for teams.",
        "published_at": NOW - timedelta(hours=5),
        "fetched_at": NOW,
        "metrics": {"views": 100, "likes": 10},
        "language": "en",
        "niche_id": "ai",
    }
    base.update(over)
    return NormalizedDoc(**base)


def test_recency_half_life_math() -> None:
    assert recency_component(NOW, NOW) == 1.0
    assert recency_component(NOW - timedelta(hours=48), NOW) == 0.5
    assert recency_component(NOW - timedelta(hours=96), NOW) == 0.25
    assert recency_component(None, NOW) == 0.5
    assert recency_component(NOW + timedelta(hours=1), NOW) == 1.0


def test_relevance_exclude_kills_and_title_beats_text() -> None:
    niche = _niche()
    assert relevance_component(_doc(title="Crypto AI marketing news", text="..."), niche) == 0.0
    in_title = relevance_component(_doc(title="AI marketing wins", text="nothing"), niche)
    in_text = relevance_component(_doc(title="Weekly notes", text="AI marketing wins"), niche)
    assert 0.0 < in_text < in_title <= 1.0
    empty_niche = NicheConfig(id="x", name="X")
    assert relevance_component(_doc(), empty_niche) == 0.5


def test_weights_merge_and_renormalize() -> None:
    merged = merged_weights({"relevance": 1.0, "bogus": 5.0})
    assert abs(sum(merged.values()) - 1.0) < 1e-9
    assert merged["relevance"] > DEFAULT_WEIGHTS["relevance"]
    assert "bogus" not in merged
    assert merged_weights({k: 0.0 for k in DEFAULT_WEIGHTS}) == DEFAULT_WEIGHTS


def test_engagement_normalized_per_platform() -> None:
    niche = _niche()
    big = _doc("blogs:big", metrics={"views": 100000})
    small = _doc("blogs:small", metrics={"views": 10})
    solo = _doc("x:solo", metrics={"likes": 3})
    ranked = score_docs([big, small, solo], niche, session=None, now=NOW)
    by_key = {s.doc.key: s for s in ranked}
    assert by_key["blogs:big"].components["engagement"] == 1.0
    assert by_key["blogs:small"].components["engagement"] == 0.0
    assert by_key["x:solo"].components["engagement"] == 0.5  # no variance -> neutral
    assert engagement_raw(big, NOW) > engagement_raw(small, NOW)  # velocity favors big


def _session():
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return make_session_factory(engine)()


def test_novelty_and_feedback_with_db() -> None:
    session = _session()
    try:
        row = Item(
            platform="blogs",
            external_id="old",
            url="https://example.com/seen",
            canonical_url="https://example.com/seen",
            niche_id="ai",
        )
        session.add(row)
        session.commit()
        fresh = _doc("blogs:new", canonical_url="https://example.com/fresh")
        seen = _doc("blogs:again", canonical_url="https://example.com/seen")
        assert novelty_component(fresh, session) == 1.0
        assert novelty_component(seen, session) == 0.3
        assert novelty_component(seen, None) == 1.0
        assert feedback_component("blogs", session) == {"score": 0.5, "mean": 0.0, "count": 0}
        session.add_all(
            [
                Feedback(item_id=row.id, signal="up"),
                Feedback(item_id=row.id, signal="up"),
                Feedback(item_id=row.id, signal="down"),
            ]
        )
        session.commit()
        prior = feedback_component("blogs", session)
        assert prior["count"] == 3
        assert abs(prior["score"] - 0.6) < 1e-9  # mean 1/3 -> 0.5 + 0.1
    finally:
        session.close()


def test_scores_ranked_bounded_and_persisted() -> None:
    session = _session()
    try:
        rows = [
            Item(
                platform="blogs",
                external_id=f"e{i}",
                url=f"https://example.com/{i}",
                canonical_url=f"https://example.com/{i}",
                niche_id="ai",
            )
            for i in range(2)
        ]
        session.add_all(rows)
        session.commit()
        docs = [
            _doc(
                "blogs:e0",
                db_id=rows[0].id,
                metrics={"views": 5},
                published_at=NOW - timedelta(hours=100),
            ),
            _doc(
                "blogs:e1",
                db_id=rows[1].id,
                metrics={"views": 5000},
                published_at=NOW - timedelta(hours=1),
            ),
        ]
        ranked = score_docs(docs, _niche(), session=session, now=NOW)
        assert [s.doc.key for s in ranked] == ["blogs:e1", "blogs:e0"]
        for entry in ranked:
            assert 0.0 <= entry.total <= 1.0
            assert set(entry.components) == set(DEFAULT_WEIGHTS)
            recomputed = sum(merged_weights(None)[k] * entry.components[k] for k in DEFAULT_WEIGHTS)
            assert abs(recomputed - entry.total) < 1e-3
        assert persist_scores(session, ranked) == 2
        session.commit()
        assert persist_scores(session, ranked) == 2  # upsert, still 2 rows
        from newsletter_machine.db.models import ItemScore

        assert session.query(ItemScore).count() == 2
    finally:
        session.close()
