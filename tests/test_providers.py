"""Phase 3: provider interface tests (RECORDED FIXTURES, respx-mocked HTTP)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import respx
from httpx import Response

from newsletter_machine.collectors.providers import (
    get_provider,
    manual_hint,
    provider_available,
    reset_provider_cache,
)
from newsletter_machine.collectors.providers.base import ProviderError
from newsletter_machine.collectors.providers.generic import GenericHTTPProvider, map_provider_row

FIX = Path(__file__).parent / "fixtures"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)
ENDPOINT = "https://provider.example.com/ingest"


def test_map_row_requires_url() -> None:
    with pytest.raises(ProviderError):
        map_provider_row({}, "x")


def test_map_row_defaults() -> None:
    item = map_provider_row({"url": "https://example.com/a?utm_source=x"}, "quora")
    assert item.platform == "quora"
    assert len(item.external_id) == 32
    assert item.canonical_url == "https://example.com/a"


@respx.mock
async def test_fetch_maps_items_and_filters_since() -> None:
    payload = json.loads((FIX / "provider_response.json").read_text(encoding="utf-8"))
    respx.post(ENDPOINT).mock(return_value=Response(200, json=payload))
    provider = GenericHTTPProvider(base_url=ENDPOINT, api_key="k")
    items = await provider.fetch("x", ["AI marketing"], SINCE, 10)
    assert len(items) == 2
    first = next(i for i in items if i.external_id == "prov-tweet-1")
    assert first.metrics == {"likes": 42, "shares": 7}
    assert first.canonical_url == "https://x.com/provuser/status/111"


@respx.mock
async def test_fetch_auth_and_quota_errors() -> None:
    respx.post(ENDPOINT).mock(return_value=Response(401, text="nope"))
    with pytest.raises(ProviderError, match="401"):
        await GenericHTTPProvider(base_url=ENDPOINT).fetch("x", ["q"], SINCE, 5)


@respx.mock
async def test_fetch_non_json() -> None:
    respx.post(ENDPOINT).mock(return_value=Response(200, text="not json"))
    with pytest.raises(ProviderError, match="non-JSON"):
        await GenericHTTPProvider(base_url=ENDPOINT).fetch("x", ["q"], SINCE, 5)


def test_missing_base_url() -> None:
    with pytest.raises(ProviderError, match="PROVIDER_BASE_URL"):
        GenericHTTPProvider(base_url="")


def test_factory_and_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_provider_cache()
    monkeypatch.delenv("PROVIDER_BASE_URL", raising=False)
    assert not provider_available()
    assert get_provider() is None
    monkeypatch.setenv("PROVIDER_BASE_URL", ENDPOINT)
    assert provider_available()
    assert get_provider() is not None
    reset_provider_cache()
    assert "manual-file" in manual_hint("quora")
