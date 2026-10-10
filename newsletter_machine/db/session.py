"""Engine + session helpers. SQLite default; Postgres via DATABASE_URL."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from newsletter_machine.db.models import Base


def get_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def init_db(database_url: str) -> Engine:
    """Create all tables (used by CLI init + tests). Alembic handles upgrades later."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine


@contextmanager
def session_scope(database_url: str) -> Iterator[Session]:
    engine = get_engine(database_url)
    factory = make_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
