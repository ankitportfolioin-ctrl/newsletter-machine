"""Validated schema for the LLM analysis layer.

Every claim-carrying entry references collected items by key; the grounding
step (pipeline/analyze.py) drops anything pointing at unknown items, and
quotes must additionally match the source text verbatim. Lists may be empty
(thin days produce light editions, not crashes).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    item_key: str
    platform: str = ""
    url: str = ""


class TopStory(BaseModel):
    title: str
    summary: str
    why_it_matters: str = ""
    sources: list[SourceRef] = Field(min_length=1)


class Trend(BaseModel):
    label: str
    momentum: Literal["rising", "steady", "fading"] = "steady"
    note: str = ""
    item_keys: list[str] = Field(default_factory=list)


class PlatformHighlight(BaseModel):
    platform: str
    item_keys: list[str] = Field(default_factory=list)
    note: str = ""


class Quote(BaseModel):
    text: str
    author: str = ""
    item_key: str = ""
    url: str = ""


class Question(BaseModel):
    question: str
    item_key: str = ""
    url: str = ""
    platform: str = ""


class Opportunity(BaseModel):
    title: str
    angle: str = ""
    format: str = ""
    hook: str = ""
    item_keys: list[str] = Field(default_factory=list)


class CreatorEntry(BaseModel):
    name: str
    platform: str = ""
    note: str = ""
    item_keys: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    tldr: list[str] = Field(min_length=1, max_length=5)
    top_stories: list[TopStory] = Field(default_factory=list)
    trends: list[Trend] = Field(default_factory=list)
    platform_highlights: list[PlatformHighlight] = Field(default_factory=list)
    quotes: list[Quote] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    opportunities: list[Opportunity] = Field(default_factory=list, max_length=10)
    creator_watch: list[CreatorEntry] = Field(default_factory=list)
    action_today: str = Field(min_length=1)
    coverage: dict[str, int] = Field(default_factory=dict)
    confidence_note: str = Field(min_length=1)
