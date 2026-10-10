"""Anthropic client (httpx, no SDK dependency). Runs live only with a key."""

from __future__ import annotations

import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from newsletter_machine.collectors.http import USER_AGENT
from newsletter_machine.llm.base import LLMClient, LLMError
from newsletter_machine.llm.prompts import SYSTEM_PROMPT, build_user_prompt, parse_json_object

MESSAGES_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-3-5-haiku-20241022"


def _transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or 500 <= exc.response.status_code < 600
    return False


class AnthropicClient(LLMClient):
    live = True

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
        if not self.api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")

    @retry(
        retry=retry_if_exception(_transient),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _post(self, body: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=120.0, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.post(
                MESSAGES_URL,
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json=body,
            )
        if resp.status_code == 401:
            raise LLMError("Anthropic: HTTP 401 (bad API key)")
        if resp.status_code == 402:
            raise LLMError("Anthropic: HTTP 402 (billing / out of credit)")
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            raise httpx.HTTPStatusError(
                f"transient {resp.status_code}", request=resp.request, response=resp
            )
        if resp.status_code >= 400:
            raise LLMError(f"Anthropic: HTTP {resp.status_code}: {resp.text[:200]}")
        return resp

    async def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._post(
                {
                    "model": self.model,
                    "max_tokens": 4000,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": build_user_prompt(payload)}],
                }
            )
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Anthropic request failed: {e}") from e
        except httpx.TransportError as e:
            raise LLMError(f"Anthropic transport error: {e}") from e
        blocks = resp.json().get("content", [])
        text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
        try:
            return parse_json_object(text)
        except ValueError as e:
            raise LLMError(f"Anthropic returned invalid JSON: {e}") from e
