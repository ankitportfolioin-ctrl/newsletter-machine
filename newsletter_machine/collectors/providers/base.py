"""Pluggable third-party provider interface.

A "provider" is any HTTP service (e.g. an Apify actor, Bright Data, or an
in-house scraper API) that returns social/blog content as JSON. Collectors try
their official API first and fall back to a provider when one is configured::

    PROVIDER_BASE_URL=https://api.apify.com/v2/acts/my-org~my-actor/run-sync-get-dataset-items
    PROVIDER_API_KEY=...

Wire any service behind this interface by matching the request/response schema
documented on GenericHTTPProvider. Nothing here bypasses logins or CAPTCHAs —
providers must source data lawfully; this code only maps their JSON.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from newsletter_machine.collectors.base import Item


class ProviderError(RuntimeError):
    """Raised when a provider is misconfigured or its request fails."""


class DataProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch(
        self, platform: str, queries: list[str], since: datetime, limit: int
    ) -> list[Item]:
        """Return normalized items for *platform*. Raise ProviderError on failure."""
        raise NotImplementedError
