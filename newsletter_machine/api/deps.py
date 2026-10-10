"""Shared API dependencies: settings, DB sessions, simple token auth.

Auth is deliberately simple (dev/small-team grade): every non-/health endpoint
requires the configured API_TOKEN via `X-API-Token` header, `Authorization:
Bearer`, or `?token=` (the latter so dashboard links/iframes work in a
browser). Secrets are compared with hmac.compare_digest. This is documented
as NOT sufficient for hostile multi-user exposure — put it behind a proxy
with TLS for anything beyond localhost.
"""

from __future__ import annotations

import hmac
from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, sessionmaker

from newsletter_machine.config import Settings, get_settings


def current_settings() -> Settings:
    return get_settings()


_factories: dict[str, sessionmaker[Session]] = {}


def session_factory_for(database_url: str) -> sessionmaker[Session]:
    factory = _factories.get(database_url)
    if factory is None:
        from newsletter_machine.db.models import Base
        from newsletter_machine.db.session import get_engine, make_session_factory

        engine = get_engine(database_url)
        Base.metadata.create_all(bind=engine)
        factory = make_session_factory(engine)
        _factories[database_url] = factory
    return factory


def db_session(settings: Settings = Depends(current_settings)) -> Iterator[Session]:
    session = session_factory_for(settings.database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _presented_token(request: Request) -> str:
    header = request.headers.get("x-api-token", "")
    if header:
        return header
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.query_params.get("token", "")


def require_token(request: Request, settings: Settings = Depends(current_settings)) -> None:
    presented = _presented_token(request) or ""
    expected = settings.api_token or ""
    if not expected or not hmac.compare_digest(presented, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing API token"
        )
