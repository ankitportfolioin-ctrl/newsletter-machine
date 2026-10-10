"""Server-rendered dashboard (Jinja2 + HTMX for the stats fragment).

Auth matches the API (X-API-Token / Bearer / ?token=); templates propagate
the token via query strings and hidden form fields. The run trigger is a
plain POST form (works without JS); HTMX progressively enhances the feedback
stats box with polling.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from newsletter_machine.api.deps import current_settings, db_session, require_token
from newsletter_machine.api.routes_feedback import feedback_stats
from newsletter_machine.api.routes_runs import list_runs
from newsletter_machine.api.routes_sources import list_sources
from newsletter_machine.config import Settings
from newsletter_machine.db.models import Feedback as FeedbackRow
from newsletter_machine.db.models import Item as ItemRow
from newsletter_machine.db.models import Newsletter as NewsletterRow
from newsletter_machine.db.models import Niche as NicheRow
from newsletter_machine.db.models import Run as RunRow

router = APIRouter(dependencies=[Depends(require_token)])
TEMPLATES = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates" / "dashboard"))
)


def _render(name: str, **ctx: Any) -> HTMLResponse:
    return HTMLResponse(content=TEMPLATES.get_template(name).render(**ctx))


def _token(request: Request) -> str:
    return request.headers.get("x-api-token", "") or request.query_params.get("token", "")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_index(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    counts = {
        "niches": session.query(NicheRow).count(),
        "items": session.query(ItemRow).count(),
        "runs": session.query(RunRow).count(),
        "newsletters": session.query(NewsletterRow).count(),
        "feedback": session.query(FeedbackRow).count(),
    }
    return _render("index.html", token=_token(request), counts=counts)


@router.get("/dashboard/niches", response_class=HTMLResponse)
def dashboard_niches(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    niches = session.query(NicheRow).order_by(NicheRow.id).all()
    return _render("niches.html", token=_token(request), niches=niches)


@router.post("/dashboard/niches")
def dashboard_niche_upsert(
    request: Request,
    id: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    session: Session = Depends(db_session),
) -> RedirectResponse:
    row = session.get(NicheRow, id.strip())
    if row is None:
        session.add(
            NicheRow(
                id=id.strip(), name=name.strip(), description=description.strip(), config_json={}
            )
        )
    else:
        row.name = name.strip()
        row.description = description.strip()
    session.commit()
    token = _token(request)
    return RedirectResponse(url=f"/dashboard/niches?token={token}", status_code=303)


@router.post("/dashboard/niches/{niche_id}/delete")
def dashboard_niche_delete(
    niche_id: str, request: Request, session: Session = Depends(db_session)
) -> RedirectResponse:
    row = session.get(NicheRow, niche_id)
    token = _token(request)
    if row is not None:
        if session.query(ItemRow).filter_by(niche_id=niche_id).count():
            raise HTTPException(status_code=409, detail="niche has items; not deleted")
        session.delete(row)
        session.commit()
    return RedirectResponse(url=f"/dashboard/niches?token={token}", status_code=303)


@router.get("/dashboard/sources", response_class=HTMLResponse)
def dashboard_sources(
    request: Request, settings: Settings = Depends(current_settings)
) -> HTMLResponse:
    return _render("sources.html", token=_token(request), sources=list_sources(settings)["sources"])


@router.get("/dashboard/runs", response_class=HTMLResponse)
def dashboard_runs(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    return _render(
        "runs.html", token=_token(request), runs=list_runs(limit=20, session=session)["runs"]
    )


@router.post("/dashboard/runs/trigger")
def dashboard_trigger(
    request: Request,
    niche: str = Form(""),
    platforms: str = Form(""),
    settings: Settings = Depends(current_settings),
) -> RedirectResponse:
    from newsletter_machine.collectors.runner import collect_and_store

    plats = [p.strip().lower() for p in platforms.split(",") if p.strip()] or None
    asyncio.run(
        collect_and_store(
            settings,
            datetime.now(UTC) - timedelta(hours=48),
            niche_id=niche or None,
            platforms=plats,
        )
    )
    token = _token(request)
    return RedirectResponse(url=f"/dashboard/runs?token={token}", status_code=303)


@router.get("/dashboard/newsletters", response_class=HTMLResponse)
def dashboard_newsletters(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    rows = session.query(NewsletterRow).order_by(NewsletterRow.id.desc()).limit(50).all()
    return _render("newsletters.html", token=_token(request), newsletters=rows)


@router.get("/dashboard/newsletters/{newsletter_id}", response_class=HTMLResponse)
def dashboard_newsletter_detail(
    newsletter_id: int, request: Request, session: Session = Depends(db_session)
) -> HTMLResponse:
    row = session.get(NewsletterRow, newsletter_id)
    if row is None:
        raise HTTPException(status_code=404, detail="newsletter not found")
    return _render("newsletter_detail.html", token=_token(request), newsletter=row)


@router.get("/dashboard/feedback", response_class=HTMLResponse)
def dashboard_feedback(request: Request, session: Session = Depends(db_session)) -> HTMLResponse:
    return _render(
        "feedback.html",
        token=_token(request),
        stats=feedback_stats(session=session),
        partial=False,
    )


@router.get("/dashboard/feedback/partial", response_class=HTMLResponse)
def dashboard_feedback_partial(session: Session = Depends(db_session)) -> HTMLResponse:
    return _render("feedback_partial.html", stats=feedback_stats(session=session))
