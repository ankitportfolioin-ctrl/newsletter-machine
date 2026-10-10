"""Phase 1: config loading tests (YAML fixtures, no network)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from newsletter_machine.config import Settings, load_newsletter, load_niches, load_sources


@pytest.fixture()
def cfg_dir(tmp_path: Path) -> Path:
    niches = {
        "niches": [
            {
                "id": "test-niche",
                "name": "Test Niche",
                "description": "desc",
                "keywords_include": ["ai"],
                "targets": {"subreddits": ["test"]},
            }
        ]
    }
    sources = {"collectors": {"blogs": {"enabled": True, "tier": "rss"}}}
    newsletter = {"newsletter": {"name": "Test", "delivery_method": "file"}}
    (tmp_path / "niches.yaml").write_text(yaml.safe_dump(niches), encoding="utf-8")
    (tmp_path / "sources.yaml").write_text(yaml.safe_dump(sources), encoding="utf-8")
    (tmp_path / "newsletter.yaml").write_text(yaml.safe_dump(newsletter), encoding="utf-8")
    return tmp_path


def _settings(cfg_dir: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        niches_yaml=str(cfg_dir / "niches.yaml"),
        sources_yaml=str(cfg_dir / "sources.yaml"),
        newsletter_yaml=str(cfg_dir / "newsletter.yaml"),
        database_url="sqlite:///:memory:",
    )


def test_load_niches(cfg_dir: Path) -> None:
    niches = load_niches(_settings(cfg_dir))
    assert len(niches) == 1
    assert niches[0].id == "test-niche"
    assert niches[0].targets.subreddits == ["test"]


def test_load_sources(cfg_dir: Path) -> None:
    sources = load_sources(_settings(cfg_dir))
    assert sources.collectors["blogs"].tier == "rss"
    assert sources.collectors["blogs"].enabled is True


def test_load_newsletter(cfg_dir: Path) -> None:
    nl = load_newsletter(_settings(cfg_dir))
    assert nl.name == "Test"
    assert nl.delivery_method == "file"


def test_missing_yaml_raises(tmp_path: Path) -> None:
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        niches_yaml=str(tmp_path / "nope.yaml"),
        sources_yaml=str(tmp_path / "nope.yaml"),
        newsletter_yaml=str(tmp_path / "nope.yaml"),
    )
    with pytest.raises(FileNotFoundError):
        load_niches(s)
