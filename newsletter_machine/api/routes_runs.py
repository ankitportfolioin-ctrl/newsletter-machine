"""Run history + triggering collection via the API (runs inline, returns summary)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from newsletter_machine.api.deps import current_settings, db_session, require_token
from newsletter_machine.config import Settings
from newsletter_machine.db.models import Run as RunRow

router = APIRouter(dependencies=[Depends(require_token)])


class RunTrigger(BaseModel):
    niche: str | None = None
    platforms: list[str] | None = None
    since_hours: int = 48
    limit: int | None = None


def _shape(row: RunRow) -> dict:
    return {
        "id": row.id,
        "niche_id": row.niche_id,
        "status": row.status,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "stats": row.stats_json or {},
        "errors": row.errors_json or [],
    }


@router.get("/runs")
def list_runs(
    niche_id: str | None = None, limit: int = 20, session: Session = Depends(db_session)
) -> dict:
    query = session.query(RunRow).order_by(RunRow.id.desc())
    if niche_id:
        query = query.filter_by(niche_id=niche_id)
    return {"runs": [_shape(r) for r in query.limit(max(1, min(limit, 100)))]}


@router.get("/runs/{run_id}")
def get_run(run_id: int, session: Session = Depends(db_session)) -> dict:
    row = session.get(RunRow, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run": _shape(row)}


@router.post("/runs")
def trigger_run(body: RunTrigger, settings: Settings = Depends(current_settings)) -> dict:
    from newsletter_machine.collectors.runner import collect_and_store

    since = datetime.now(UTC) - timedelta(hours=max(1, body.since_hours))
    try:
        summary = asyncio.run(
            collect_and_store(
                settings,
                since,
                niche_id=body.niche,
                platforms=body.platforms,
                limit_override=body.limit,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return summary
