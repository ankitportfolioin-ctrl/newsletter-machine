"""Phase 4 end-to-end: seeded RECORDED-FIXTURE dataset through the full pipeline."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from newsletter_machine.config import NicheConfig
from newsletter_machine.db.models import Base, Cluster, Feedback, Item, ItemScore
from newsletter_machine.db.session import get_engine, make_session_factory
from newsletter_machine.pipeline.normalize import normalize_doc
from newsletter_machine.pipeline.run import run_pipeline

FIX = Path(__file__).parent / "fixtures" / "pipeline_items.json"
NOW = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
AI_KEYS = {"youtube:yt1", "blogs:blog1", "reddit:r1", "x:x1", "quora:q1", "linkedin:li1"}


def _niche() -> NicheConfig:
    return NicheConfig(
        id="ai-tools-marketers",
        name="AI tools for marketers",
        description="",
        keywords_include=["AI marketing", "ChatGPT", "marketing automation"],
        keywords_exclude=["crypto", "giveaway"],
        related_terms=["LLM", "copywriting"],
        min_score=0.3,
    )


def _seeded_session():
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    session = factory()
    rows = json.loads(FIX.read_text(encoding="utf-8"))
    for row in rows:
        session.add(
            Item(
                platform=row["platform"],
                external_id=row["external_id"],
                url=row["url"],
                canonical_url=row["url"],
                author=row.get("author", ""),
                title=row["title"],
                text=row["text"],
                published_at=NOW - timedelta(hours=row["age_hours"]),
                metrics_json=row.get("metrics", {}),
                language="en",
                niche_id="ai-tools-marketers",
            )
        )
    session.commit()
    yt = session.query(Item).filter_by(platform="youtube", external_id="yt1").one()
    session.add(Feedback(newsletter_id=None, item_id=yt.id, signal="up"))
    session.commit()
    return session


def test_pipeline_fixture_end_to_end() -> None:
    session = _seeded_session()
    try:
        rows = session.query(Item).all()
        docs = [normalize_doc(r, niche_id="ai-tools-marketers") for r in rows]
        assert all(d.db_id is not None for d in docs)
        report = run_pipeline(_niche(), docs, session, now=NOW)

        # Dedupe: near-dupe twin + cross-platform canonical repost removed
        assert report.total_in == 13
        assert report.unique_count == 11
        removed_keys = {d.key for d, _, _ in report.dedupe.removed}
        assert removed_keys == {"blogs:blog1b", "reddit:dupurl"}

        # Ranking: recent + engaged + relevant on top, stale gem last
        order = [s.doc.key for s in report.ranked]
        assert order[0] in {"youtube:yt1", "reddit:r1", "x:x1"}
        assert order[-1] == "blogs:old1"
        assert order[-2] == "manual:noise1"
        assert report.ranked[0].components["relevance"] >= 0.5
        assert report.ranked[-2].components["relevance"] == 0.0

        # Threshold: relevance-0 items (spam AND off-topic heat) never pass,
        # even above min_score; stale gem fails on score
        kept = {s.doc.key for s in report.above_threshold}
        assert "manual:noise1" not in kept
        assert "blogs:t1" not in kept and "blogs:t2" not in kept
        assert "blogs:old1" not in kept
        assert {"youtube:yt1", "reddit:r1"} <= kept

        # Clusters: travel pair together, AI majority together, noise elsewhere
        by_key = {}
        for cluster in report.clusters:
            for key in cluster.member_keys:
                by_key[key] = cluster.label
        assert by_key["blogs:t1"] == by_key["blogs:t2"]
        ai_labels = [by_key[k] for k in AI_KEYS]
        assert max(ai_labels.count(label) for label in set(ai_labels)) >= 4
        assert by_key["manual:noise1"] != by_key["youtube:yt1"]
        assert len(report.clusters) >= 3

        # Persistence: scores + clusters stored, components transparent
        assert report.scores_written == 11
        assert report.clusters_written == len(report.clusters)
        assert session.query(ItemScore).count() == 11
        assert session.query(Cluster).count() == len(report.clusters)
        top = report.ranked[0]
        stored = session.query(ItemScore).filter_by(item_id=top.doc.db_id).one()
        assert set(stored.components_json) == {
            "recency",
            "engagement",
            "authority",
            "relevance",
            "novelty",
            "feedback",
        }
        assert stored.total == top.total
    finally:
        session.close()
