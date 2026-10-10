"""Deploy readiness: serverless fallbacks + Postgres compat (no network)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from newsletter_machine.config import NewsletterConfig, NicheConfig


def _cfg() -> NewsletterConfig:
    return NewsletterConfig.model_validate({"name": "T"})


def test_vercel_entrypoint_reexports_app() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("vercel_entrypoint", Path("api/index.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from newsletter_machine.api.main import app

    assert module.app is app


async def test_persist_without_writable_fs(tmp_path: Path) -> None:
    from newsletter_machine.config import Settings
    from newsletter_machine.db.models import Base, Newsletter
    from newsletter_machine.db.session import get_engine, make_session_factory
    from newsletter_machine.llm.schemas import AnalysisResult
    from newsletter_machine.pipeline.compose import compose_content, persist_rendered

    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path}/t.db",  # type: ignore[call-arg]
        output_dir=str(tmp_path / "missing-parent" / "out"),
    )
    # Make the grandparent a FILE so mkdir fails deterministically on all OSes.
    blocker = tmp_path / "missing-parent"
    blocker.write_text("not a dir", encoding="utf-8")
    engine = get_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    session = make_session_factory(engine)()
    try:
        analysis = AnalysisResult(tldr=["hi"], action_today="do it", confidence_note="n/a")
        content = compose_content(
            NicheConfig(id="n", name="N"), "2026-10-10", analysis, {}, {}, 1, _cfg()
        )
        result = persist_rendered(
            session, settings, "n", "2026-10-10", content.subject, content, {}
        )
        assert result["html_path"] == "" and result["md_path"] == ""
        assert session.query(Newsletter).count() == 1  # DB row still persisted
    finally:
        session.close()


def test_preview_rerenders_from_db_when_file_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import yaml
    from fastapi.testclient import TestClient

    from newsletter_machine.api.main import create_app
    from newsletter_machine.config import clear_config_cache

    (tmp_path / "niches.yaml").write_text(yaml.safe_dump({"niches": []}), encoding="utf-8")
    (tmp_path / "sources.yaml").write_text(yaml.safe_dump({"collectors": {}}), encoding="utf-8")
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "T"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setenv("API_TOKEN", "tok")
    clear_config_cache()
    try:
        from newsletter_machine.api.deps import session_factory_for
        from newsletter_machine.config import get_settings
        from newsletter_machine.db.models import Newsletter

        factory = session_factory_for(get_settings().database_url)
        with factory() as session:
            session.add(
                Newsletter(
                    date="2026-10-10",
                    niche_id="n",
                    subject="Seeded",
                    html_path="/nonexistent/newsletter.html",
                    md_path="",
                    txt_path="",
                    content_json={
                        "analysis": {
                            "tldr": ["Seeded bullet"],
                            "top_stories": [],
                            "trends": [],
                            "platform_highlights": [],
                            "quotes": [],
                            "questions": [],
                            "opportunities": [],
                            "creator_watch": [],
                            "action_today": "Read it.",
                            "coverage": {},
                            "confidence_note": "db only.",
                        }
                    },
                    status="built",
                )
            )
            session.commit()
            nid = session.query(Newsletter).one().id
        client = TestClient(create_app())
        resp = client.get(f"/newsletters/{nid}/preview", headers={"X-API-Token": "tok"})
        assert resp.status_code == 200, resp.text[:200]
        assert "Seeded bullet" in resp.text
    finally:
        clear_config_cache()


NEEDS_POSTGRES = not bool(os.getenv("TEST_DATABASE_URL"))


@pytest.mark.skipif(NEEDS_POSTGRES, reason="Set TEST_DATABASE_URL (Supabase pooler URL) to run")
def test_postgres_roundtrip() -> None:
    """LIVE Postgres check: tables create + rows round-trip (Supabase-compatible)."""
    from newsletter_machine.db.models import Base, Item, Newsletter
    from newsletter_machine.db.session import get_engine, make_session_factory

    url = os.environ["TEST_DATABASE_URL"]
    assert url.startswith("postgresql"), "TEST_DATABASE_URL must be a postgresql:// URL"
    engine = get_engine(url)
    Base.metadata.create_all(bind=engine)
    session = make_session_factory(engine)()
    try:
        row = Item(
            platform="postgres-probe",
            external_id="p1",
            url="https://example.com/p1",
            niche_id="probe",
        )
        session.add(row)
        session.commit()
        assert session.query(Item).filter_by(platform="postgres-probe").count() >= 1
        assert session.query(Newsletter).count() >= 0
    finally:
        session.query(Item).filter_by(platform="postgres-probe").delete()
        session.commit()
        session.close()
        engine.dispose()
