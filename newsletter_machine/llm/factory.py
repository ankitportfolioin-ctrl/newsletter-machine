"""Client factory: settings.llm_provider selects stub | anthropic | openai."""

from __future__ import annotations

from typing import Any

from newsletter_machine.llm.base import LLMClient, LLMError


def get_llm_client(settings: Any | None = None, override: str | None = None) -> LLMClient:
    from newsletter_machine.config import get_settings
    from newsletter_machine.llm.anthropic_client import AnthropicClient
    from newsletter_machine.llm.local_stub import StubLLMClient
    from newsletter_machine.llm.openai_client import OpenAIClient

    settings = settings or get_settings()
    provider = str(override or getattr(settings, "llm_provider", "stub") or "stub").lower()
    if provider == "stub":
        return StubLLMClient()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    raise LLMError(f"unknown llm_provider {provider!r} (use stub | anthropic | openai)")
