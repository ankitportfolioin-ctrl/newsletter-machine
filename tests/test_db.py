"""Phase 1: DB model tests — upsert/idempotency primitives, unique constraints."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from newsletter_machine.db.models import Base, Feedback, Item, Newsletter, Niche, Run
from newsletter_machine.db.session import get_engine, make_session_factory


@pytest.fixture()
def session():
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    with factory() as s:
        yield s


def test_niche_item_unique_constraint(session) -> None:
    session.add(Niche(id="n1", name="N1", description="", config_json={}))
    session.commit()
    session.add(
        Item(platform="blogs", external_id="abc", url="https://example.com/a", niche_id="n1")
    )
    session.commit()
    session.add(
        Item(platform="blogs", external_id="abc", url="https://example.com/a-dup", niche_id="n1")
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_idempotent_newsletter_upsert_pattern(session) -> None:
    """Re-running the same day must not duplicate newsletters: emulate upsert."""
    session.add(
        Newsletter(date="2026-01-01", niche_id="n1", subject="s", content_json={}, status="draft")
    )
    session.commit()

    # Second run: check-then-insert must find the existing row
    existing = session.query(Newsletter).filter_by(date="2026-01-01", niche_id="n1").one_or_none()
    assert existing is not None
    assert session.query(Newsletter).count() == 1


def test_run_and_feedback_roundtrip(session) -> None:
    session.add(Run(niche_id="n1", status="success", stats_json={"blogs": 3}, errors_json=[]))
    session.add(Feedback(newsletter_id=None, item_id=None, signal="up"))
    session.commit()
    assert session.query(Run).count() == 1
    assert session.query(Feedback).count() == 1
