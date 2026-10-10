"""Feedback intake (POST JSON for API clients, GET for email links) + stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from newsletter_machine.api.deps import db_session, require_token
from newsletter_machine.db.models import Feedback as FeedbackRow
from newsletter_machine.db.models import Item as ItemRow
from newsletter_machine.db.models import Newsletter as NewsletterRow

SIGNALS = ("up", "down", "click")

router = APIRouter(dependencies=[Depends(require_token)])


class FeedbackIn(BaseModel):
    newsletter_id: int | None = None
    item_id: int | None = None
    signal: str


def _check_refs(session: Session, newsletter_id: int | None, item_id: int | None) -> None:
    if newsletter_id is not None and session.get(NewsletterRow, newsletter_id) is None:
        raise HTTPException(status_code=404, detail="newsletter not found")
    if item_id is not None and session.get(ItemRow, item_id) is None:
        raise HTTPException(status_code=404, detail="item not found")


def _record(session: Session, newsletter_id: int | None, item_id: int | None, signal: str) -> dict:
    if signal not in SIGNALS:
        raise HTTPException(status_code=422, detail=f"signal must be one of {SIGNALS}")
    _check_refs(session, newsletter_id, item_id)
    row = FeedbackRow(newsletter_id=newsletter_id, item_id=item_id, signal=signal)
    session.add(row)
    session.flush()
    return {"id": row.id, "signal": signal}


@router.post("/feedback", status_code=201)
def post_feedback(body: FeedbackIn, session: Session = Depends(db_session)) -> dict:
    return _record(session, body.newsletter_id, body.item_id, body.signal)


@router.get("/feedback", response_class=HTMLResponse)
def get_feedback(
    newsletter_id: int | None = None,
    item_id: int | None = None,
    signal: str = "up",
    session: Session = Depends(db_session),
) -> HTMLResponse:
    """Email-link friendly intake: records the vote, returns a thanks page."""
    try:
        result = _record(session, newsletter_id, item_id, signal)
    except HTTPException as e:
        return HTMLResponse(
            content=f"<p>Thanks — vote not recorded ({e.detail}).</p>", status_code=e.status_code
        )
    word = {"up": "useful", "down": "not useful", "click": "clicked"}.get(result["signal"], "noted")
    return HTMLResponse(
        content=f"<html><body><p>Thanks — marked {word} (vote #{result['id']}).</p></body></html>"
    )


@router.get("/feedback/stats")
def feedback_stats(
    newsletter_id: int | None = None, session: Session = Depends(db_session)
) -> dict:
    query = session.query(FeedbackRow)
    if newsletter_id is not None:
        query = query.filter_by(newsletter_id=newsletter_id)
    rows = query.all()
    by_signal: dict[str, int] = {}
    by_newsletter: dict[str, dict[str, int]] = {}
    for row in rows:
        by_signal[row.signal] = by_signal.get(row.signal, 0) + 1
        bucket = by_newsletter.setdefault(str(row.newsletter_id), {})
        bucket[row.signal] = bucket.get(row.signal, 0) + 1
    return {"total": len(rows), "by_signal": by_signal, "by_newsletter": by_newsletter}
