"""Phase 1: CLI + API smoke tests (no network)."""

from __future__ import annotations

from datetime import UTC

from typer.testing import CliRunner

from newsletter_machine.api.main import app as fastapi_app
from newsletter_machine.cli import app as cli_app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    assert "newsletter-machine" in result.output.lower() or "Usage" in result.output


def test_doctor_runs_without_keys(tmp_path, monkeypatch) -> None:
    import yaml

    (tmp_path / "niches.yaml").write_text(
        yaml.safe_dump({"niches": [{"id": "n", "name": "N"}]}), encoding="utf-8"
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
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from newsletter_machine.config import clear_config_cache

    clear_config_cache()
    try:
        result = runner.invoke(cli_app, ["doctor"])
        assert result.exit_code == 0, result.output
        assert "doctor" in result.output.lower()
    finally:
        clear_config_cache()


def test_health_endpoint() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(fastapi_app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_collector_contract_never_crashes() -> None:
    import asyncio
    from datetime import datetime

    from newsletter_machine.collectors.registry import available_collectors

    async def go() -> None:
        for klass in available_collectors().values():
            res = await klass().collect(None, datetime.now(UTC), 5)
            assert isinstance(res.errors, list)
            assert isinstance(res.tier_used, str)

    asyncio.run(go())
