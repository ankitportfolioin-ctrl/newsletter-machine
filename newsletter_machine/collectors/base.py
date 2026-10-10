"""Collector contract. Every collector must never crash a run."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Item(BaseModel):
    """Normalized item returned by every collector."""

    platform: str
    external_id: str
    url: str
    canonical_url: str = ""
    author: str = ""
    title: str = ""
    text: str = ""
    media_urls: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    raw: dict[str, Any] = Field(default_factory=dict)


class CollectorResult(BaseModel):
    items: list[Item] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    quota_used: int = 0
    tier_used: str = "disabled"


class BaseCollector(ABC):
    platform: str = "base"

    @abstractmethod
    async def collect(self, niche: Any, since: datetime, limit: int) -> CollectorResult:
        """Collect items for a niche. Must catch internal errors and record them."""
        raise NotImplementedError

    def tier_status(self) -> tuple[str, str]:
        """Return (tier, human-readable availability note) for `doctor`."""
        return ("disabled", "not configured (Phase 1 skeleton)")
