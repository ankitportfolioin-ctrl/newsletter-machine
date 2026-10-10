"""Provider registry: one factory, honest availability checks."""

from __future__ import annotations

import os

from newsletter_machine.collectors.providers.base import DataProvider

_configured_provider: DataProvider | None = None


def provider_available() -> bool:
    """True when a provider endpoint is configured (key optional for local mocks)."""
    return bool(os.getenv("PROVIDER_BASE_URL", "").strip())


def get_provider() -> DataProvider | None:
    """Return the configured provider, or None when PROVIDER_BASE_URL is unset."""
    from newsletter_machine.collectors.providers.generic import GenericHTTPProvider

    if not provider_available():
        return None
    global _configured_provider  # noqa: PLW0603 - intentional process-wide cache
    if _configured_provider is None:
        _configured_provider = GenericHTTPProvider()
    return _configured_provider


def reset_provider_cache() -> None:
    global _configured_provider  # noqa: PLW0603
    _configured_provider = None


def manual_hint(platform: str) -> str:
    return (
        f"no {platform} API/provider data — import manually: "
        f"newsletter-machine collect --manual-file FILE.csv --manual-platform {platform}"
    )
