"""Phase 4 orchestration: normalize -> dedupe -> score -> cluster.

run_pipeline takes already-normalized docs (callers load them from the DB or
from fixtures), runs every stage, persists ItemScore/Cluster rows when a
session is given, and returns a PipelineReport. Phase 5's composer consumes
the report; the CLI `build` command will call this per niche per day.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from newsletter_machine.pipeline.cluster import (
    DEFAULT_THRESHOLD as CLUSTER_THRESHOLD,
)
from newsletter_machine.pipeline.cluster import (
    TopicCluster,
    cluster_docs,
    persist_clusters,
)
from newsletter_machine.pipeline.dedupe import DedupeResult, dedupe_docs
from newsletter_machine.pipeline.normalize import NormalizedDoc
from newsletter_machine.pipeline.scoring import (
    NOVELTY_DAYS,
    ScoredDoc,
    persist_scores,
    score_docs,
)


@dataclass
class PipelineReport:
    niche_id: str
    total_in: int = 0
    unique_count: int = 0
    dedupe: DedupeResult = field(default_factory=DedupeResult)
    ranked: list[ScoredDoc] = field(default_factory=list)
    clusters: list[TopicCluster] = field(default_factory=list)
    scores_written: int = 0
    clusters_written: int = 0
    above_threshold: list[ScoredDoc] = field(default_factory=list)


def run_pipeline(
    niche: Any,
    docs: list[NormalizedDoc],
    session: Any | None = None,
    run_id: int | None = None,
    now: datetime | None = None,
    novelty_days: int = NOVELTY_DAYS,
    sim_threshold: int = 8,
    cluster_threshold: float = CLUSTER_THRESHOLD,
) -> PipelineReport:
    """Full pass over one niche's docs. Pure except optional persistence."""
    moment = now or datetime.now(UTC)
    niche_id = str(getattr(niche, "id", "") or "")
    min_score = float(getattr(niche, "min_score", 0.0) or 0.0)
    report = PipelineReport(niche_id=niche_id, total_in=len(docs))
    report.dedupe = dedupe_docs(docs, hamming_threshold=sim_threshold)
    unique = report.dedupe.unique
    report.unique_count = len(unique)
    report.ranked = score_docs(
        unique, niche, session=session, now=moment, novelty_days=novelty_days
    )
    # Threshold gate: total >= min_score AND relevance > 0. The second clause is
    # deliberate — an item matching nothing in the niche definition (excluded or
    # off-topic) must not pass on heat alone. Ranked keeps everyone for audit.
    report.above_threshold = [
        s for s in report.ranked if s.total >= min_score and s.components["relevance"] > 0
    ]
    report.clusters = cluster_docs(unique, threshold=cluster_threshold)
    if session is not None:
        report.scores_written = persist_scores(session, report.ranked)
        key_to_db_id = {s.doc.key: s.doc.db_id for s in report.ranked if s.doc.db_id is not None}
        report.clusters_written = persist_clusters(
            session, niche_id, report.clusters, key_to_db_id, run_id
        )
        session.commit()
    return report
