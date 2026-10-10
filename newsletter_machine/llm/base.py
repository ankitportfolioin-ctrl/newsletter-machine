"""LLM client interface: raw JSON dicts in, retries handled by the caller."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMError(RuntimeError):
    """Transport/auth failure talking to an LLM provider."""


class LLMClient(ABC):
    live: bool = False  # True for network clients (enables validation retries)

    @abstractmethod
    async def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return the analysis as a JSON-able dict matching llm/schemas.py."""
        raise NotImplementedError
