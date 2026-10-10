"""Newsletter archive + HTML preview + build trigger."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from newsletter_machine.api.deps import current_settings, db_session, require_token
from newsletter_machine.config import Settings, load_newsletter, load_niches
from newsletter_machine.db.models import Newsletter as NewsletterRow

router = APIRouter(dependencies=[Depends(require_token)])


def _shape(row: NewsletterRow) -> dict:
    return {
        "id": row.id,
        "date": row.date,
        "niche_id": row.niche_id,
        "subject": row.subject,
        "status": row.status,
        "html_path": row.html_path,
        "md_path": row.md_path,
        "txt_path": row.txt_path,
    }


@router.get("/newsletters")
def list_newsletters(
    niche_id: str | None = None,
    date: str | None = None,
    limit: int = 20,
    session: Session = Depends(db_session),
) -> dict:
    query = session.query(NewsletterRow).order_by(NewsletterRow.id.desc())
    if niche_id:
        query = query.filter_by(niche_id=niche_id)
    if date:
        query = query.filter_by(date=date)
    return {"newsletters": [_shape(r) for r in query.limit(max(1, min(limit, 100)))]}


@router.get("/newsletters/{newsletter_id}")
def get_newsletter(newsletter_id: int, session: Session = Depends(db_session)) -> dict:
    row = session.get(NewsletterRow, newsletter_id)
    if row is None:
        raise HTTPException(status_code=404, detail="newsletter not found")
    return {"newsletter": _shape(row)}


@router.get("/newsletters/{newsletter_id}/preview", response_class=HTMLResponse)
def preview_newsletter(newsletter_id: int, session: Session = Depends(db_session)) -> HTMLResponse:
    row = session.get(NewsletterRow, newsletter_id)
    if row is None:
        raise HTTPException(status_code=404, detail="newsletter not found")
    if row.html_path and Path(row.html_path).exists():
        return HTMLResponse(content=Path(row.html_path).read_text(encoding="utf-8"))
    # Serverless fallback: re-render from the stored analysis (files may not persist).
    try:
        from types import SimpleNamespace

        from newsletter_machine.llm.schemas import AnalysisResult
        from newsletter_machine.pipeline.compose import compose_content, render_html

        analysis = AnalysisResult.model_validate((row.content_json or {})["analysis"])
        niche = SimpleNamespace(id=row.niche_id, name=row.niche_id)
        content = compose_content(niche, row.date, analysis, {}, {}, row.id, None)
        return HTMLResponse(content=render_html(content))
    except Exception as e:  # noqa: BLE001 - no file and no renderable analysis
        raise HTTPException(status_code=404, detail=f"no preview available: {e}") from e


class BuildTrigger(BaseModel):
    niche: str | None = None
    date: str | None = None
    since_hours: int = 168
    limit: int = 50
    llm: str | None = None


@router.post("/newsletters/build", status_code=201)
async def trigger_build(
    body: BuildTrigger,
    settings: Settings = Depends(current_settings),
    session: Session = Depends(db_session),
) -> dict:
    """Run pipeline + analysis + render for one/all niches (powers daily automation)."""
    from newsletter_machine.llm.base import LLMError
    from newsletter_machine.llm.factory import get_llm_client
    from newsletter_machine.pipeline.build_flow import build_niche_newsletter

    try:
        niches = load_niches(settings)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if body.niche:
        niches = [n for n in niches if n.id == body.niche]
        if not niches:
            raise HTTPException(status_code=404, detail=f"unknown niche {body.niche!r}")
    date_str = body.date or datetime.now(UTC).strftime("%Y-%m-%d")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"bad date {date_str!r}, want YYYY-MM-DD"
        ) from None
    try:
        client = get_llm_client(settings, override=body.llm or None)
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    newsletter_cfg = load_newsletter(settings)
    built: list[dict] = []
    for niche_cfg in niches:
        try:
            built.append(
                await build_niche_newsletter(
                    session,
                    settings,
                    niche_cfg,
                    newsletter_cfg,
                    date_str,
                    client,
                    since_hours=body.since_hours,
                    limit=body.limit,
                )
            )
        except Exception as e:  # noqa: BLE001 - one niche never stops the batch
            built.append({"niche_id": niche_cfg.id, "error": f"{type(e).__name__}: {e}"})
    return {"date": date_str, "built": built}
