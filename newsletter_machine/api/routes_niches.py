"""Niche CRUD (DB rows; YAML `init`/`collect` sync overwrites name/description)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from newsletter_machine.api.deps import db_session, require_token
from newsletter_machine.db.models import Item as ItemRow
from newsletter_machine.db.models import Niche as NicheRow

router = APIRouter(dependencies=[Depends(require_token)])


class NicheIn(BaseModel):
    id: str
    name: str
    description: str = ""


class NichePatch(BaseModel):
    name: str | None = None
    description: str | None = None


def _shape(row: NicheRow) -> dict:
    return {"id": row.id, "name": row.name, "description": row.description or ""}


@router.get("/niches")
def list_niches(session: Session = Depends(db_session)) -> dict:
    rows = session.query(NicheRow).order_by(NicheRow.id).all()
    return {"niches": [_shape(r) for r in rows]}


@router.post("/niches", status_code=201)
def upsert_niche(body: NicheIn, session: Session = Depends(db_session)) -> dict:
    row = session.get(NicheRow, body.id)
    created = row is None
    if created:
        row = NicheRow(id=body.id, name=body.name, description=body.description, config_json={})
        session.add(row)
    else:
        assert row is not None
        row.name = body.name
        row.description = body.description
    session.flush()
    return {"created": created, "niche": _shape(row)}


@router.get("/niches/{niche_id}")
def get_niche(niche_id: str, session: Session = Depends(db_session)) -> dict:
    row = session.get(NicheRow, niche_id)
    if row is None:
        raise HTTPException(status_code=404, detail="niche not found")
    items = session.query(ItemRow).filter_by(niche_id=niche_id).count()
    return {"niche": _shape(row), "item_count": items}


@router.patch("/niches/{niche_id}")
def patch_niche(niche_id: str, body: NichePatch, session: Session = Depends(db_session)) -> dict:
    row = session.get(NicheRow, niche_id)
    if row is None:
        raise HTTPException(status_code=404, detail="niche not found")
    if body.name is not None:
        row.name = body.name
    if body.description is not None:
        row.description = body.description
    session.flush()
    return {"niche": _shape(row)}


@router.delete("/niches/{niche_id}")
def delete_niche(niche_id: str, session: Session = Depends(db_session)) -> dict:
    row = session.get(NicheRow, niche_id)
    if row is None:
        raise HTTPException(status_code=404, detail="niche not found")
    items = session.query(ItemRow).filter_by(niche_id=niche_id).count()
    if items:
        raise HTTPException(
            status_code=409, detail=f"niche has {items} collected item(s); not deleted"
        )
    session.delete(row)
    session.flush()
    return {"deleted": niche_id}
