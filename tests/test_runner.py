"""Phase 2: runner tests — idempotent upsert + never-crash (no network)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from newsletter_machine.collectors.base import BaseCollector, CollectorResult, Item
from newsletter_machine.collectors.runner import run_collectors, upsert_items
from newsletter_machine.config import NicheConfig, Settings, SourcesConfig
from newsletter_machine.db.models import Base
from newsletter_machine.db.session import get_engine, make_session_factory


def _item(ext: str = "a1") -> Item:
    return Item(
        platform="blogs", external_id=ext, url=f"https://example.com/{ext}", title=f"T {ext}"
    )


def test_upsert_is_idempotent() -> None:
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    with factory() as s:
        ins, skp = upsert_items(s, [_item("a1"), _item("a2")], "n1")
        s.commit()
        assert (ins, skp) == (2, 0)
        ins2, skp2 = upsert_items(s, [_item("a1"), _item("a2")], "n1")
        s.commit()
        assert (ins2, skp2) == (0, 2)
        from newsletter_machine.db.models import Item as ItemRow

        assert s.query(ItemRow).count() == 2


class _Boom(BaseCollector):
    platform = "boom"

    async def collect(self, niche, since, limit):  # noqa: ANN001, ANN202
        raise RuntimeError("boom")


async def test_runner_never_crashes(monkeypatch: pytest.MonkeyPatch) -> None:
    import newsletter_machine.collectors.runner as runner_mod

    async def fake_collect(self, niche, since, limit):  # noqa: ANN001, ANN202
        return CollectorResult(items=[_item("ok1")], errors=[], quota_used=1, tier_used="rss")

    class _Ok(BaseCollector):
        platform = "ok"

        collect = fake_collect

    monkeypatch.setattr(runner_mod, "available_collectors", lambda: {"boom": _Boom, "ok": _Ok})
    niche = NicheConfig(id="n", name="N")
    sources = SourcesConfig.model_validate(
        {"collectors": {"boom": {"enabled": True}, "ok": {"enabled": True}}}
    )
    settings = Settings(_env_file=None, database_url="sqlite:///:memory:")  # type: ignore[call-arg]
    results = await run_collectors(niche, sources, settings, datetime.now(UTC), None, 5)
    assert set(results) == {"boom", "ok"}
    assert results["boom"].items == [] and results["boom"].errors
    assert len(results["ok"].items) == 1
