"""Phase 5: analysis payload, stub, grounding, retries (no network)."""

from __future__ import annotations

import pytest

from newsletter_machine.config import NicheConfig
from newsletter_machine.llm.base import LLMError
from newsletter_machine.llm.factory import get_llm_client
from newsletter_machine.llm.local_stub import StubLLMClient
from newsletter_machine.llm.prompts import parse_json_object
from newsletter_machine.llm.schemas import AnalysisResult
from newsletter_machine.pipeline.analyze import (
    build_analysis_input,
    compute_momentum,
    ground_analysis,
    run_analysis,
)


def _payload() -> dict:
    return {
        "niche": {"id": "ai", "name": "AI tools"},
        "date": "2026-10-10",
        "items": [
            {
                "key": "blogs:a",
                "platform": "blogs",
                "url": "https://example.com/a",
                "title": "AI marketing tools roundup",
                "text": (
                    'Jane said "exact quoted span for testing purposes here" '
                    "about tools. More context follows."
                ),
                "author": "Jane",
                "score": 0.8,
                "cluster": "ai marketing",
            },
            {
                "key": "reddit:q",
                "platform": "reddit",
                "url": "https://example.com/q",
                "title": "Which AI marketing tool is best?",
                "text": "Trying to pick one this week.",
                "author": "user1",
                "score": 0.6,
                "cluster": "ai marketing",
            },
        ],
        "clusters": [
            {"label": "ai marketing", "momentum": "rising", "keys": ["blogs:a", "reddit:q"]}
        ],
        "coverage": {"blogs": 1, "reddit": 1},
        "total_items": 2,
    }


async def _stub_result(payload: dict) -> AnalysisResult:
    raw = await StubLLMClient().analyze(payload)
    return AnalysisResult.model_validate(raw)


def test_compute_momentum() -> None:
    assert compute_momentum([]) == "steady"
    assert compute_momentum([1.0, 5.0, 30.0]) == "rising"
    assert compute_momentum([30.0, 50.0]) == "steady"
    assert compute_momentum([80.0, 200.0]) == "fading"


def test_parse_json_object() -> None:
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('noise {"a": 1} tail') == {"a": 1}
    with pytest.raises(ValueError):
        parse_json_object("no json here")


async def test_stub_output_is_schema_valid_and_grounded() -> None:
    payload = _payload()
    result = await _stub_result(payload)
    assert len(result.tldr) >= 1
    assert result.top_stories[0].sources[0].item_key == "blogs:a"
    assert result.questions and result.questions[0].item_key == "reddit:q"
    assert result.action_today and result.confidence_note
    assert result.coverage == {"blogs": 1, "reddit": 1}


async def test_stub_quotes_only_real_spans() -> None:
    result = await _stub_result(_payload())
    assert len(result.quotes) == 1
    quote = result.quotes[0]
    assert quote.text == "exact quoted span for testing purposes here"
    assert quote.item_key == "blogs:a" and quote.author == "Jane"


async def test_stub_empty_items_light_edition() -> None:
    payload = _payload()
    payload["items"] = []
    payload["clusters"] = []
    result = await _stub_result(payload)
    assert result.top_stories == [] and len(result.tldr) == 1


async def test_grounding_drops_fabrications() -> None:
    payload = _payload()
    raw = await StubLLMClient().analyze(payload)
    raw["top_stories"].append(
        {"title": "Invented", "summary": "x", "sources": [{"item_key": "nope:0", "url": ""}]}
    )
    raw["quotes"].append({"text": "totally invented words here", "item_key": "blogs:a", "url": ""})
    raw["quotes"].append(
        {"text": "exact quoted span for testing purposes here", "item_key": "ghost:1", "url": ""}
    )
    raw["opportunities"].append({"title": "No source idea", "item_keys": []})
    result, dropped = ground_analysis(raw, payload)
    assert dropped["top_stories"] == 1
    assert dropped["quotes"] == 2  # invented text + unknown key
    assert dropped["opportunities"] == 1
    assert all(s.sources for s in result.top_stories)


async def test_run_analysis_retries_live_client() -> None:
    from newsletter_machine.llm.base import LLMClient

    calls = {"n": 0}

    class Flaky(LLMClient):
        live = True

        async def analyze(self, payload: dict) -> dict:
            calls["n"] += 1
            if calls["n"] < 3:
                return {"bogus": True}  # schema-invalid
            return await StubLLMClient().analyze(payload)

    result, _ = await run_analysis(_payload(), Flaky())
    assert calls["n"] == 3
    assert result.top_stories


async def test_run_analysis_gives_up_and_stub_fails_fast() -> None:
    from newsletter_machine.llm.base import LLMClient

    class Bad(LLMClient):
        live = True

        async def analyze(self, payload: dict) -> dict:
            return {"bogus": True}

    with pytest.raises(LLMError, match="3 attempt"):
        await run_analysis(_payload(), Bad(), max_attempts=3)

    class BadStub(LLMClient):
        live = False

        async def analyze(self, payload: dict) -> dict:
            return {"bogus": True}

    with pytest.raises(LLMError, match="1 attempt"):
        await run_analysis(_payload(), BadStub())


def test_build_analysis_input_truncates_and_counts() -> None:
    from newsletter_machine.pipeline.normalize import NormalizedDoc

    long_text = "x" * 5000
    doc = NormalizedDoc(
        key="blogs:a",
        db_id=1,
        platform="blogs",
        external_id="a",
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        author="",
        title="T",
        text=long_text,
        published_at=None,
        fetched_at=None,
    )
    from newsletter_machine.pipeline.scoring import ScoredDoc

    class FakeReport:
        ranked = [ScoredDoc(doc=doc, components={}, total=0.5)]
        clusters = []

    payload = build_analysis_input(FakeReport(), NicheConfig(id="ai", name="AI"), "2026-10-10")
    assert len(payload["items"][0]["text"]) == 1500
    assert payload["coverage"] == {"blogs": 1}
    assert payload["total_items"] == 1


def test_factory() -> None:
    from newsletter_machine.config import Settings

    assert isinstance(get_llm_client(Settings(_env_file=None, llm_provider="stub")), StubLLMClient)  # type: ignore[call-arg]
    with pytest.raises(LLMError, match="unknown llm_provider"):
        get_llm_client(Settings(_env_file=None, llm_provider="nope"))  # type: ignore[call-arg]
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        get_llm_client(Settings(_env_file=None, llm_provider="anthropic"))  # type: ignore[call-arg]
