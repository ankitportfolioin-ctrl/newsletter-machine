"""URL canonicalization + item normalization for the pipeline.

Phase 2 gave us canonicalize_url/normalize_text; Phase 4 adds NormalizedDoc —
one clean, source-agnostic record that dedupe/scoring/clustering all consume.
Language detection is deliberately out of scope: collectors set language, we
just lowercase/default it (documented, not pretended).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_EXACT = frozenset(
    {
        "fbclid",
        "gclid",
        "dclid",
        "msclkid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "si",
        "spm",
        "ref",
        "ref_src",
        "ref_url",
    }
)


def _is_tracking_param(name: str) -> bool:
    lowered = name.lower()
    return lowered in _TRACKING_EXACT or lowered.startswith("utm_")


def canonicalize_url(url: str) -> str:
    """Return a stable canonical form of *url* for dedupe/upsert.

    - adds https:// when the scheme is missing
    - lowercases scheme + host, drops default ports and fragments
    - strips tracking query params (utm_*, fbclid, gclid, si, …)
    - sorts remaining query params, drops trailing slash (except root)
    """
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or "").lower()
    if not host:
        return raw
    port = parts.port
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        host = f"{host}:{port}"
    # userinfo is dropped deliberately (never part of canonical identity)
    path = parts.path or ""
    if len(path) > 1:
        path = path.rstrip("/")
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not _is_tracking_param(k)
    ]
    query_pairs.sort()
    query = urlencode(query_pairs, doseq=True)
    return urlunsplit((scheme, host, path, query, ""))


def normalize_text(value: str, max_chars: int = 20000) -> str:
    """Collapse whitespace and cap length. Never raises on bad input."""
    if not value:
        return ""
    collapsed = " ".join(str(value).split())
    return collapsed[:max_chars]


@dataclass
class NormalizedDoc:
    """Clean record for one collected item. `key` is unique within a batch."""

    key: str  # f"{platform}:{external_id}"
    db_id: int | None
    platform: str
    external_id: str
    url: str
    canonical_url: str
    author: str
    title: str
    text: str
    published_at: datetime | None
    fetched_at: datetime | None
    metrics: dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    niche_id: str = ""


def _as_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    try:
        dt = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def normalize_doc(source: Any, niche_id: str = "", default_language: str = "en") -> NormalizedDoc:
    """Build a NormalizedDoc from a collector Item or a DB Item row (duck-typed).

    Collector Items carry `.metrics`; DB rows carry `.metrics_json`. Both work.
    Missing title falls back to the URL; missing language to `default_language`.
    """
    platform = str(getattr(source, "platform", "") or "")
    external_id = str(getattr(source, "external_id", "") or "")
    url = str(getattr(source, "url", "") or "")
    canonical = str(getattr(source, "canonical_url", "") or "") or canonicalize_url(url)
    metrics = getattr(source, "metrics", None)
    if metrics is None:
        metrics = getattr(source, "metrics_json", None) or {}
    return NormalizedDoc(
        key=f"{platform}:{external_id}",
        db_id=getattr(source, "id", None) if hasattr(source, "__table__") else None,
        platform=platform,
        external_id=external_id,
        url=url,
        canonical_url=canonical,
        author=normalize_text(getattr(source, "author", "") or "", max_chars=512),
        title=normalize_text(getattr(source, "title", "") or url, max_chars=1000),
        text=normalize_text(getattr(source, "text", "") or "", max_chars=20000),
        published_at=_as_dt(getattr(source, "published_at", None)),
        fetched_at=_as_dt(getattr(source, "fetched_at", None)),
        metrics=dict(metrics) if isinstance(metrics, dict) else {},
        language=(str(getattr(source, "language", "") or default_language).strip().lower() or "en"),
        niche_id=str(getattr(source, "niche_id", "") or niche_id),
    )
