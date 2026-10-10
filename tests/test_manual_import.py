"""Phase 2: manual import tests (RECORDED FIXTURES on disk)."""

from pathlib import Path

import pytest

from newsletter_machine.collectors.manual_import import load_manual_items

FIX = Path(__file__).parent / "fixtures"


def test_csv_import() -> None:
    items = load_manual_items(str(FIX / "manual.csv"))
    assert len(items) == 2
    assert items[0].external_id == "csv-1"
    assert items[0].metrics == {"views": 100, "likes": 5}
    assert items[0].canonical_url == "https://example.com/csv-1"  # tracking stripped
    assert items[1].platform == "x"  # per-row platform kept
    assert len(items[1].external_id) == 32  # derived sha256


def test_json_import() -> None:
    items = load_manual_items(str(FIX / "manual.json"))
    assert len(items) == 1
    assert items[0].title == "Json Title"


def test_urllist_import_with_platform_override() -> None:
    items = load_manual_items(str(FIX / "urllist.txt"), platform="quora")
    assert len(items) == 2
    assert all(i.platform == "quora" for i in items)
    assert items[0].canonical_url == "https://example.com/url-1"


def test_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_manual_items(str(FIX / "does-not-exist.csv"))


def test_bad_extension(tmp_path: Path) -> None:
    bad = tmp_path / "data.xml"
    bad.write_text("<x/>", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported extension"):
        load_manual_items(str(bad))


def test_csv_missing_url_header(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("title\nhello\n", encoding="utf-8")
    with pytest.raises(ValueError, match="including 'url'"):
        load_manual_items(str(bad))
