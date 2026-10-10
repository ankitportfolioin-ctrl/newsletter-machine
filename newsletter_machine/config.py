"""Pydantic-settings + YAML configuration loading.

Env (.env) holds secrets. YAML holds niches / sources / newsletter structure.
All YAML paths are configurable via env vars so tests can point at fixtures.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

TierName = Literal["official_api", "rss", "provider", "manual", "disabled"]


class PlatformTargets(BaseModel):
    subreddits: list[str] = Field(default_factory=list)
    youtube_channels: list[str] = Field(default_factory=list)
    youtube_queries: list[str] = Field(default_factory=list)
    x_accounts: list[str] = Field(default_factory=list)
    x_queries: list[str] = Field(default_factory=list)
    linkedin_queries: list[str] = Field(default_factory=list)
    linkedin_companies: list[str] = Field(default_factory=list)
    instagram_hashtags: list[str] = Field(default_factory=list)
    instagram_accounts: list[str] = Field(default_factory=list)
    quora_topics: list[str] = Field(default_factory=list)
    blog_feeds: list[str] = Field(default_factory=list)
    blog_domains: list[str] = Field(default_factory=list)


class NicheConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    keywords_include: list[str] = Field(default_factory=list)
    keywords_exclude: list[str] = Field(default_factory=list)
    related_terms: list[str] = Field(default_factory=list)
    targets: PlatformTargets = Field(default_factory=PlatformTargets)
    language: str = "en"
    min_score: float = 0.0
    weight_overrides: dict[str, float] = Field(default_factory=dict)


class CollectorTierConfig(BaseModel):
    enabled: bool = True
    tier: TierName = "official_api"
    credential_env_vars: list[str] = Field(default_factory=list)
    rate_limit_per_min: int = 30
    item_cap_per_run: int = 50


class SourcesConfig(BaseModel):
    collectors: dict[str, CollectorTierConfig] = Field(default_factory=dict)


class NewsletterSectionConfig(BaseModel):
    enabled: bool = True
    max_items: int = 5


class NewsletterConfig(BaseModel):
    name: str = "Newsletter Machine"
    tagline: str = ""
    tone: str = "concise, practical"
    sections_order: list[str] = Field(
        default_factory=lambda: [
            "tldr",
            "top_stories",
            "trend_radar",
            "platform_highlights",
            "voices",
            "questions",
            "opportunities",
            "action",
            "coverage",
        ]
    )
    sections: dict[str, NewsletterSectionConfig] = Field(default_factory=dict)
    recipients: list[str] = Field(default_factory=list)
    send_time: str = "07:00"
    timezone: str = "UTC"
    delivery_method: Literal["file", "smtp", "resend", "webhook", "none"] = "file"
    subject_style: str = "{date} — {niche}: top stories"


class Settings(BaseSettings):
    """Process environment. Secrets live here, never hardcoded."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./newsletter_machine.db"
    api_token: str = "change-me-dev-token"

    niches_yaml: str = "config/niches.yaml"
    sources_yaml: str = "config/sources.yaml"
    newsletter_yaml: str = "config/newsletter.yaml"
    output_dir: str = "output/newsletters"

    # Platform credentials (all optional in Phase 1 / demo mode)
    youtube_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "newsletter-machine/0.1"
    x_bearer_token: str = ""
    linkedin_access_token: str = ""
    instagram_access_token: str = ""
    instagram_business_id: str = ""

    # Provider fallback (pluggable third-party, e.g. Apify-style)
    provider_api_key: str = ""
    provider_base_url: str = ""

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "stub"  # stub | anthropic | openai

    # Delivery
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    resend_api_key: str = ""
    delivery_webhook_url: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def _yaml_path(configured: str) -> Path:
    p = Path(configured)
    if not p.is_absolute():
        p = Path(os.getcwd()) / p
    return p


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_niches(settings: Settings | None = None) -> list[NicheConfig]:
    settings = settings or get_settings()
    data = _load_yaml(_yaml_path(settings.niches_yaml))
    raw = data.get("niches", data if isinstance(data, list) else [])
    if isinstance(data, list):
        raw = data
    return [NicheConfig.model_validate(n) for n in raw]


def load_sources(settings: Settings | None = None) -> SourcesConfig:
    settings = settings or get_settings()
    data = _load_yaml(_yaml_path(settings.sources_yaml))
    collectors = data.get("collectors", data if isinstance(data, dict) else {})
    return SourcesConfig.model_validate({"collectors": collectors})


def load_newsletter(settings: Settings | None = None) -> NewsletterConfig:
    settings = settings or get_settings()
    data = _load_yaml(_yaml_path(settings.newsletter_yaml))
    newsletter = data.get("newsletter", data if isinstance(data, dict) else {})
    return NewsletterConfig.model_validate(newsletter)


def clear_config_cache() -> None:
    get_settings.cache_clear()
