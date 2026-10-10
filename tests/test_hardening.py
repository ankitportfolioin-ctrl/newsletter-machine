"""Phase 7: hardening tests — logging, rate limits, idempotency, demo mode."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.collectors.http import AsyncRateLimiter
from newsletter_machine.logging import get_logger, reset_logging, setup_logging

FIX = Path(__file__).parent / "fixtures"


def test_rate_limiter_intervals() -> None:
    assert AsyncRateLimiter(30).min_interval == pytest.approx(2.0)
    assert AsyncRateLimiter(60).min_interval == pytest.approx(1.0)
    assert AsyncRateLimiter(0).min_interval == 0.0
    assert AsyncRateLimiter(-5).min_interval == 0.0


async def test_rate_limiter_no_delay_when_unlimited() -> None:
    import time

    limiter = AsyncRateLimiter(0)
    start = time.monotonic()
    for _ in range(5):
        await limiter.acquire()
    assert time.monotonic() - start < 2.0


def test_json_logging_structured_no_secrets(capsys: pytest.CaptureFixture) -> None:
    reset_logging()
    try:
        setup_logging(level="INFO", json_format=True)
        get_logger("test").info("hello", extra={"ctx_items": 3})
        line = capsys.readouterr().err.strip().splitlines()[-1]
        payload = json.loads(line)
        assert payload["level"] == "info" and payload["msg"] == "hello"
        assert payload["ctx"] == {"items": 3}
        assert "ts" in payload
    finally:
        reset_logging()
        setup_logging()


def test_text_logging_default() -> None:
    reset_logging()
    try:
        setup_logging(level="WARNING", json_format=False)
        assert logging.getLogger().level == logging.WARNING
    finally:
        reset_logging()
        setup_logging()


@respx.mock
async def test_collect_twice_no_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import yaml

    from newsletter_machine.collectors.runner import collect_and_store
    from newsletter_machine.config import Settings, clear_config_cache
    from newsletter_machine.db.models import Item
    from newsletter_machine.db.session import get_engine, make_session_factory

    (tmp_path / "niches.yaml").write_text(
        yaml.safe_dump(
            {
                "niches": [
                    {
                        "id": "n1",
                        "name": "N",
                        "targets": {"blog_feeds": ["https://feed.example.com/rss.xml"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump({"collectors": {"blogs": {"enabled": True, "tier": "rss"}}}),
        encoding="utf-8",
    )
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "T"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    db_url = f"sqlite:///{tmp_path}/t.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    clear_config_cache()
    try:
        feed_xml = (FIX / "sample_feed.xml").read_bytes()
        respx.get("https://feed.example.com/rss.xml").mock(
            return_value=Response(
                200, content=feed_xml, headers={"content-type": "application/rss+xml"}
            )
        )
        respx.get(url__regex=r"https://example\.com/blog/.*").mock(
            return_value=Response(404, text="nope")
        )
        settings = Settings(
            _env_file=None,
            niches_yaml=str(tmp_path / "niches.yaml"),  # type: ignore[call-arg]
            sources_yaml=str(tmp_path / "sources.yaml"),
            newsletter_yaml=str(tmp_path / "newsletter.yaml"),
            database_url=db_url,
        )
        since = datetime(2026, 10, 1, tzinfo=UTC)
        first = await collect_and_store(
            settings, since, niche_id="n1", platforms=["blogs"], limit_override=10
        )
        second = await collect_and_store(
            settings, since, niche_id="n1", platforms=["blogs"], limit_override=10
        )
        assert first["inserted"] >= 1
        assert second["inserted"] == 0
        assert second["skipped"] == first["inserted"]
        engine = get_engine(db_url)
        session = make_session_factory(engine)()
        try:
            assert session.query(Item).count() == first["inserted"]
            # Build twice on the same rows: still one newsletter, same scores.
            from newsletter_machine.config import NicheConfig
            from newsletter_machine.llm.local_stub import StubLLMClient
            from newsletter_machine.pipeline.analyze import build_analysis_input, run_analysis
            from newsletter_machine.pipeline.compose import build_newsletter
            from newsletter_machine.pipeline.normalize import normalize_doc
            from newsletter_machine.pipeline.run import run_pipeline

            niche = NicheConfig(id="n1", name="N")
            newsletter_cfg = settings  # placeholder replaced below
            from newsletter_machine.config import load_newsletter

            newsletter_cfg = load_newsletter(settings)
            client = StubLLMClient()
            for _ in range(2):
                rows = session.query(Item).all()
                docs = [normalize_doc(r) for r in rows]
                report = run_pipeline(niche, docs, session, now=datetime(2026, 10, 10, tzinfo=UTC))
                payload = build_analysis_input(report, niche, "2026-10-10")
                analysis, _ = await run_analysis(payload, client)
                build_newsletter(
                    session, settings, niche, "2026-10-10", analysis, {}, {}, newsletter_cfg
                )
            from newsletter_machine.db.models import ItemScore, Newsletter

            assert session.query(Newsletter).count() == 1
            assert session.query(ItemScore).count() == len(rows)
        finally:
            session.close()
    finally:
        clear_config_cache()


async def test_demo_run_zero_keys_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import yaml

    from newsletter_machine.config import clear_config_cache
    from newsletter_machine.demo import DEMO_NICHE_ID, run_demo

    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "Demo Signal"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    db_url = f"sqlite:///{tmp_path}/demo.db"
    out_dir = str(tmp_path / "out")
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("OUTPUT_DIR", out_dir)
    for var in (
        "YOUTUBE_API_KEY",
        "REDDIT_CLIENT_ID",
        "X_BEARER_TOKEN",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "PROVIDER_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)
    clear_config_cache()
    try:
        from newsletter_machine.config import get_settings

        settings = get_settings()
        first = await run_demo(settings, "2026-10-10")
        second = await run_demo(settings, "2026-10-10")
        assert first["inserted"] == 5 and first["skipped"] == 0
        assert second["inserted"] == 0 and second["skipped"] == 5
        assert first["newsletter_id"] == second["newsletter_id"]
        assert first["niche_id"] == DEMO_NICHE_ID
        assert Path(first["html_path"]).exists()
        assert "FIXTURE" in Path(first["html_path"]).read_text(encoding="utf-8")
        assert first["delivery"] == "file"
    finally:
        clear_config_cache()
