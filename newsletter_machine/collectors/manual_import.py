"""Manual import: CSV / JSON / URL-list files for any platform.

CSV columns (case-insensitive header required: url):
  platform, external_id, url*, title, text, author, published_at (ISO),
  language, views, likes, comments, shares, upvotes
  (* required; external_id defaults to sha256(url) when absent)

JSON: a list, or {"items": [...]} with the same keys.

TXT / URL-list: one URL per line, '#' comments + blanks ignored; every row
  uses the given platform (default "manual") with title=url.

Returns collector `Item` objects so the runner can upsert them like any
other collector result. Raises FileNotFoundError / ValueError with clear
messages on bad input.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from newsletter_machine.collectors.base import Item
from newsletter_machine.pipeline.normalize import canonicalize_url, normalize_text

METRIC_KEYS = ("views", "likes", "comments", "shares", "upvotes")


def _parse_dt(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    try:
        dt = datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def row_to_item(row: dict[str, Any], default_platform: str = "manual") -> Item:
    lowered = {(k or "").strip().lower(): v for k, v in row.items()}
    url = str(lowered.get("url", "") or "").strip()
    if not url:
        raise ValueError("row is missing required 'url'")
    platform = str(lowered.get("platform", "") or default_platform).strip() or default_platform
    external_id = str(lowered.get("external_id", "") or "").strip()
    if not external_id:
        external_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    metrics = {}
    for key in METRIC_KEYS:
        parsed = _to_int(lowered.get(key))
        if parsed is not None:
            metrics[key] = parsed
    return Item(
        platform=platform,
        external_id=external_id,
        url=url,
        canonical_url=canonicalize_url(url),
        author=normalize_text(str(lowered.get("author", "") or ""), max_chars=512),
        title=normalize_text(str(lowered.get("title", "") or url), max_chars=1000),
        text=normalize_text(str(lowered.get("text", "") or ""), max_chars=20000),
        published_at=_parse_dt(lowered.get("published_at")),
        metrics=metrics,
        language=str(lowered.get("language", "") or "en").strip() or "en",
        raw={"via": "manual_import"},
    )


def parse_csv(path: Path, default_platform: str = "manual") -> list[Item]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "url" not in [h.strip().lower() for h in reader.fieldnames]:
            raise ValueError(f"{path}: CSV needs a header row including 'url'")
        items: list[Item] = []
        for lineno, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            try:
                items.append(row_to_item(row, default_platform))
            except ValueError as e:
                raise ValueError(f"{path} line {lineno}: {e}") from e
    return items


def parse_json(path: Path, default_platform: str = "manual") -> list[Item]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"{path}: JSON must be a list or {{'items': [...]}}")
    items: list[Item] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path} item {i}: must be an object")
        try:
            items.append(row_to_item(row, default_platform))
        except ValueError as e:
            raise ValueError(f"{path} item {i}: {e}") from e
    return items


def parse_urllist(path: Path, default_platform: str = "manual") -> list[Item]:
    items: list[Item] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith("http"):
            raise ValueError(f"{path} line {lineno}: not a URL: {stripped!r}")
        items.append(row_to_item({"url": stripped}, default_platform))
    return items


def load_manual_items(path: str, platform: str = "manual") -> list[Item]:
    """Load a CSV / JSON / TXT file into collector Items (fixtures welcome)."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"Manual import file not found: {path}")
    suffix = file.suffix.lower()
    if suffix == ".csv":
        return parse_csv(file, platform)
    if suffix == ".json":
        return parse_json(file, platform)
    if suffix in (".txt", ".urls", ".list") or suffix == "":
        return parse_urllist(file, platform)
    raise ValueError(f"{path}: unsupported extension {suffix!r} (use .csv / .json / .txt)")
