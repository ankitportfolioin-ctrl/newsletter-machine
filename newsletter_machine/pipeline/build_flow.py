"""Shared per-niche build flow (CLI `build` and the daily scheduler both use it).

Window DB items -> pipeline -> LLM analysis -> diagnostics -> render+persist.
Raises ValueError/LlmError with clear messages; callers decide exit codes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from newsletter_machine.db.models import Item as ItemRow
from newsletter_machine.db.models import Run as RunRow
from newsletter_machine.llm.base import LLMClient
from newsletter_machine.logging import get_logger
from newsletter_machine.pipeline.analyze import build_analysis_input, run_analysis
from newsletter_machine.pipeline.compose import build_newsletter
from newsletter_machine.pipeline.normalize import normalize_doc
from newsletter_machine.pipeline.run import run_pipeline

log = get_logger("newsletter_machine.build")


async def build_niche_newsletter(
    session: Any,
    settings: Any,
    niche_cfg: Any,
    newsletter_cfg: Any,
    date_str: str,
    client: LLMClient,
    since_hours: int = 168,
    limit: int = 50,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build one niche's newsletter. Returns build_newsletter result + analysis stats."""
    moment = now or datetime.now(UTC)
    cutoff = moment - timedelta(hours=max(1, since_hours))
    rows = (
        session.query(ItemRow).filter(ItemRow.niche_id == niche_cfg.id).order_by(ItemRow.id).all()
    )

    def _aware(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    window = [
        r for r in rows if _aware(r.published_at) is None or _aware(r.published_at) >= cutoff
    ][:limit]
    docs = [normalize_doc(r, niche_id=niche_cfg.id) for r in window]
    report = run_pipeline(niche_cfg, docs, session, now=moment)
    payload = build_analysis_input(report, niche_cfg, date_str, now=moment)
    analysis, dropped = await run_analysis(payload, client)
    latest_run = (
        session.query(RunRow).filter_by(niche_id=niche_cfg.id).order_by(RunRow.id.desc()).first()
    )
    diagnostics = {
        "stats": dict(latest_run.stats_json) if latest_run else {},
        "errors": list(latest_run.errors_json) if latest_run else [],
        "dropped": dropped,
        "ranked": len(report.ranked),
        "llm": type(client).__name__,
    }
    key_to_db_id = {s.doc.key: s.doc.db_id for s in report.ranked if s.doc.db_id}
    result = build_newsletter(
        session, settings, niche_cfg, date_str, analysis, diagnostics, key_to_db_id, newsletter_cfg
    )
    result["niche_id"] = niche_cfg.id
    log.info(
        "newsletter_built",
        extra={"ctx_niche": niche_cfg.id, "ctx_date": date_str,
               "ctx_newsletter": result["id"], "ctx_ranked": len(report.ranked)},
    )
    return result
