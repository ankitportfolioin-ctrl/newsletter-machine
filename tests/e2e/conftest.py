"""Pytest configuration for E2E tests with Playwright."""

import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
API_URL = os.getenv("E2E_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("E2E_API_TOKEN", "change-me-dev-token")


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Session-scoped browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Function-scoped browser context with tracing on failure."""
    context = browser.new_context(
        base_url=BASE_URL,
        record_video_dir="test-results/videos" if os.getenv("CI") else None,
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Function-scoped page with trace on failure."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL for API calls."""
    return API_URL


@pytest.fixture(scope="session")
def api_token() -> str:
    """API token for authentication."""
    return API_TOKEN


@pytest.fixture(scope="function")
def authenticated_page(page: Page, api_token: str) -> Page:
    """Page with token authentication via query param."""
    # The dashboard uses ?token= query parameter
    return page


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end (require running services)")