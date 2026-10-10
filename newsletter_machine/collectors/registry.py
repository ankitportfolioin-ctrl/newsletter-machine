"""Collector registry: discovers/enables collectors from sources.yaml."""

from __future__ import annotations

from newsletter_machine.collectors.base import BaseCollector


def _late_import(path: str, cls: str) -> type[BaseCollector] | None:
    try:
        mod = __import__(path, fromlist=[cls])
        return getattr(mod, cls)
    except Exception:
        return None


_COLLECTOR_PATHS: dict[str, tuple[str, str]] = {
    "youtube": ("newsletter_machine.collectors.youtube", "YouTubeCollector"),
    "reddit": ("newsletter_machine.collectors.reddit", "RedditCollector"),
    "x": ("newsletter_machine.collectors.x_twitter", "XTwitterCollector"),
    "linkedin": ("newsletter_machine.collectors.linkedin", "LinkedInCollector"),
    "instagram": ("newsletter_machine.collectors.instagram", "InstagramCollector"),
    "quora": ("newsletter_machine.collectors.quora", "QuoraCollector"),
    "blogs": ("newsletter_machine.collectors.blogs", "BlogsCollector"),
}


def available_collectors() -> dict[str, type[BaseCollector]]:
    found: dict[str, type[BaseCollector]] = {}
    for name, (path, cls) in _COLLECTOR_PATHS.items():
        klass = _late_import(path, cls)
        if klass is not None:
            found[name] = klass
    return found


def enabled_collectors(sources_config) -> dict[str, type[BaseCollector]]:
    all_c = available_collectors()
    enabled: dict[str, type[BaseCollector]] = {}
    for name, klass in all_c.items():
        cfg = sources_config.collectors.get(name)
        if cfg is None or cfg.enabled:
            enabled[name] = klass
    return enabled
