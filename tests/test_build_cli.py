"""Phase 5: CLI build end to end (temp DB + temp output dir, stub LLM)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from typer.testing import CliRunner

from newsletter_machine.cli import app as cli_app
from newsletter_machine.config import clear_config_cache

runner = CliRunner()


def _write_configs(tmp_path: Path, niches: list[dict]) -> None:
    import yaml

    (tmp_path / "niches.yaml").write_text(
        yaml.safe_dump({"niches": niches}), encoding="utf-8"
    )
    (tmp_path / "sources.yaml").write_text(
        yaml.safe_dump({"collectors": {"blogs": {"enabled": True, "tier": "rss"}}}),
        encoding="utf-8",
    )
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "Test Signal"}}), encoding="utf-8"
    )


def test_build_writes_newsletter_files(tmp_path: Path, monkeypatch) -> None:
    _write_configs(tmp_path, [{"id": "n1", "name": "Niche One"}])
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    clear_config_cache()
    try:
        from newsletter_machine.config import get_settings
        from newsletter_machine.db.models import Base, Item
        from newsletter_machine.db.session import get_engine, make_session_factory

        settings = get_settings()
        engine = get_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)
        session = make_session_factory(engine)()
        session.add(
            Item(
                platform="blogs",
                external_id="e1",
                url="https://example.com/e1",
                canonical_url="https://example.com/e1",
                title="Seeded story",
                text="Seeded body with enough words to analyze properly today.",
                published_at=datetime.now(UTC),
                metrics_json={"views": 10},
                niche_id="n1",
            )
        )
        session.commit()
        session.close()

        result = runner.invoke(cli_app, ["build", "--niche", "n1", "--date", "2026-10-10"])
        assert result.exit_code == 0, result.output
        html = tmp_path / "out" / "2026-10-10" / "n1" / "newsletter.html"
        md = tmp_path / "out" / "2026-10-10" / "n1" / "newsletter.md"
        txt = tmp_path / "out" / "2026-10-10" / "n1" / "newsletter.txt"
        assert html.exists() and md.exists() and txt.exists()
        assert "Seeded story" in html.read_text(encoding="utf-8")
        assert "Built 1 newsletter(s)" in result.output

        # Rebuild is idempotent (same Newsletter row, files overwritten)
        again = runner.invoke(cli_app, ["build", "--niche", "n1", "--date", "2026-10-10"])
        assert again.exit_code == 0, again.output
        session = make_session_factory(engine)()
        from newsletter_machine.db.models import Newsletter

        assert session.query(Newsletter).count() == 1
        session.close()
    finally:
        clear_config_cache()


def test_build_digest_merges_two_niches(tmp_path: Path, monkeypatch) -> None:
    _write_configs(tmp_path, [{"id": "n1", "name": "Niche One"}, {"id": "n2", "name": "Niche Two"}])
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    clear_config_cache()
    try:
        from newsletter_machine.config import get_settings
        from newsletter_machine.db.models import Base, Item
        from newsletter_machine.db.session import get_engine, make_session_factory

        settings = get_settings()
        engine = get_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)
        session = make_session_factory(engine)()
        for niche_id, title in (("n1", "First story"), ("n2", "Second story")):
            session.add(
                Item(platform="blogs", external_id=niche_id, url=f"https://example.com/{niche_id}",
                     canonical_url=f"https://example.com/{niche_id}", title=title,
                     text=f"{title} body with enough words to analyze properly today.",
                     published_at=datetime.now(UTC), niche_id=niche_id)
            )
        session.commit()
        session.close()

        result = runner.invoke(cli_app, ["build", "--date", "2026-10-10", "--digest"])
        assert result.exit_code == 0, result.output
        digest_html = tmp_path / "out" / "2026-10-10" / "digest" / "newsletter.html"
        assert digest_html.exists()
        text = digest_html.read_text(encoding="utf-8")
        assert "First story" in text and "Second story" in text
        assert "[Niche Two]" in text
    finally:
        clear_config_cache()


def test_build_unknown_niche_fails(tmp_path: Path, monkeypatch) -> None:
    import yaml

    (tmp_path / "niches.yaml").write_text(yaml.safe_dump({"niches": []}), encoding="utf-8")
    (tmp_path / "sources.yaml").write_text(yaml.safe_dump({"collectors": {}}), encoding="utf-8")
    (tmp_path / "newsletter.yaml").write_text(
        yaml.safe_dump({"newsletter": {"name": "T"}}), encoding="utf-8"
    )
    monkeypatch.setenv("NICHES_YAML", str(tmp_path / "niches.yaml"))
    monkeypatch.setenv("SOURCES_YAML", str(tmp_path / "sources.yaml"))
    monkeypatch.setenv("NEWSLETTER_YAML", str(tmp_path / "newsletter.yaml"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    clear_config_cache()
    try:
        result = runner.invoke(cli_app, ["build", "--niche", "ghost"])
        assert result.exit_code == 1
        assert "unknown niche" in result.output
    finally:
        clear_config_cache()
