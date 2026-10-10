"""Shared polite-HTTP helpers: rate limiting, retries with backoff, client factory.

Every collector uses these so we respect ToS/rate limits by construction:
- per-platform minimum interval between requests (from sources.yaml)
- exponential-backoff retries on transient failures (429 / 5xx / transport)
- a single honest User-Agent identifying the bot
"""

from __future__ import annotations

import asyncio
import time

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

USER_AGENT = "newsletter-machine/0.1 (+https://github.com/newsletter-machine)"


class AsyncRateLimiter:
    """Minimum-interval rate limiter. `per_min <= 0` means 'no delay'."""

    def __init__(self, per_min: int = 30) -> None:
        self.min_interval = 60.0 / per_min if per_min and per_min > 0 else 0.0
        self._lock = asyncio.Lock()
        self._last: float = 0.0

    async def acquire(self) -> None:
        if self.min_interval <= 0:
            return
        async with self._lock:
            now = time.monotonic()
            wait = self._last + self.min_interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


_limiters: dict[str, AsyncRateLimiter] = {}


def get_limiter(name: str, per_min: int = 30) -> AsyncRateLimiter:
    key = f"{name}:{per_min}"
    limiter = _limiters.get(key)
    if limiter is None:
        limiter = AsyncRateLimiter(per_min)
        _limiters[key] = limiter
    return limiter


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code == 429 or 500 <= exc.response.status_code < 600
    return False


def create_client(
    headers: dict[str, str] | None = None, timeout: float = 20.0
) -> httpx.AsyncClient:
    merged = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        merged.update(headers)
    return httpx.AsyncClient(headers=merged, timeout=timeout, follow_redirects=True)


@retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _get_with_retry(
    client: httpx.AsyncClient, url: str, params: dict | None = None
) -> httpx.Response:
    resp = await client.get(url, params=params)
    if resp.status_code == 429 or 500 <= resp.status_code < 600:
        raise httpx.HTTPStatusError(
            f"transient HTTP {resp.status_code} for {url}",
            request=resp.request,
            response=resp,
        )
    return resp


async def polite_get(
    client: httpx.AsyncClient,
    limiter: AsyncRateLimiter,
    url: str,
    params: dict | None = None,
) -> httpx.Response:
    """Rate-limit, then GET with backoff retries. Raises on final failure."""
    await limiter.acquire()
    return await _get_with_retry(client, url, params)
