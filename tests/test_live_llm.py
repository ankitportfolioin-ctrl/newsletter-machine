"""LIVE LLM test (needs ANTHROPIC_API_KEY or OPENAI_API_KEY). Skipped otherwise.

Single tiny run (2 items) proving the real-client path validates end to end.
Set one key and run: pytest tests/test_live_llm.py -v
"""

from __future__ import annotations

import os

import pytest

from newsletter_machine.llm.factory import get_llm_client
from newsletter_machine.pipeline.analyze import run_analysis

HAS_KEY = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
PROVIDER = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"


@pytest.mark.skipif(not HAS_KEY, reason="LIVE: set ANTHROPIC_API_KEY or OPENAI_API_KEY to run")
async def test_live_llm_analysis() -> None:
    from newsletter_machine.config import Settings

    settings = Settings(_env_file=None, llm_provider=PROVIDER)  # type: ignore[call-arg]
    client = get_llm_client(settings)
    payload = {
        "niche": {"id": "ai", "name": "AI tools"},
        "date": "2026-10-10",
        "items": [
            {
                "key": "blogs:a",
                "platform": "blogs",
                "url": "https://example.com/a",
                "title": "AI marketing tools roundup",
                "text": "A practical roundup of tools.",
                "author": "Jane",
                "score": 0.8,
                "cluster": "ai marketing",
            },
            {
                "key": "blogs:b",
                "platform": "blogs",
                "url": "https://example.com/b",
                "title": "ChatGPT workflows",
                "text": "How teams use prompts daily.",
                "author": "Bob",
                "score": 0.5,
                "cluster": "ai marketing",
            },
        ],
        "clusters": [
            {"label": "ai marketing", "momentum": "rising", "keys": ["blogs:a", "blogs:b"]}
        ],
        "coverage": {"blogs": 2},
        "total_items": 2,
    }
    result, dropped = await run_analysis(payload, client)
    print(f"\nLIVE {PROVIDER}: {len(result.top_stories)} stories, dropped={dropped}")
    assert result.tldr
