"""OpenAI client (httpx, no SDK dependency). Runs live only with a key."""

from __future__ import annotations

import os
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from newsletter_machine.collectors.http import USER_AGENT
from newsletter_machine.llm.base import LLMClient, LLMError
from newsletter_machine.llm.prompts import SYSTEM_PROMPT, build_user_prompt, parse_json_object

CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


def _transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or 500 <= exc.response.status_code < 600
    return False


class OpenAIClient(LLMClient):
    live = True

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        if not self.api_key:
            raise LLMError("OPENAI_API_KEY is not set")

    @retry(
        retry=retry_if_exception(_transient),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _post(self, body: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=120.0, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.post(
                CHAT_URL, headers={"Authorization": f"Bearer {self.api_key}"}, json=body
            )
        if resp.status_code == 401:
            raise LLMError("OpenAI: HTTP 401 (bad API key)")
        if resp.status_code == 402:
            raise LLMError("OpenAI: HTTP 402 (billing / out of credit)")
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            raise httpx.HTTPStatusError(
                f"transient {resp.status_code}", request=resp.request, response=resp
            )
        if resp.status_code >= 400:
            raise LLMError(f"OpenAI: HTTP {resp.status_code}: {resp.text[:200]}")
        return resp

    async def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._post(
                {
                    "model": self.model,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(payload)},
                    ],
                }
            )
        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenAI request failed: {e}") from e
        except httpx.TransportError as e:
            raise LLMError(f"OpenAI transport error: {e}") from e
        try:
            text = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(f"OpenAI: unexpected response shape: {e}") from e
        try:
            return parse_json_object(text)
        except ValueError as e:
            raise LLMError(f"OpenAI returned invalid JSON: {e}") from e
