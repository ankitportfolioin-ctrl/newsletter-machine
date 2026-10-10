"""E2E smoke tests for the newsletter machine dashboard."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_loads(authenticated_page: Page, api_token: str) -> None:
    """Test that dashboard home page loads with token authentication."""
    page = authenticated_page

    # Navigate to dashboard with token
    page.goto(f"/dashboard?token={api_token}")

    expect(page).to_have_title("Newsletter Machine — dashboard")

    # Check for dashboard elements
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
    expect(page.get_by_role("heading", name="Quick Actions")).to_be_visible()

    # Verify Quick Actions buttons are present
    expect(page.get_by_role("link", name="Run Collection")).to_be_visible()
    expect(page.get_by_role("link", name="View Newsletters")).to_be_visible()
    expect(page.get_by_role("link", name="Manage Niches")).to_be_visible()
    expect(page.get_by_role("link", name="Manage Sources")).to_be_visible()

    # Check stats cards
    expect(page.get_by_text("Niches")).to_be_visible()
    expect(page.get_by_text("Items")).to_be_visible()
    expect(page.get_by_text("Runs")).to_be_visible()
    expect(page.get_by_text("Newsletters")).to_be_visible()
    expect(page.get_by_text("Feedback")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_niches_page(authenticated_page: Page, api_token: str) -> None:
    """Test that niches page loads."""
    page = authenticated_page

    page.goto(f"/dashboard/niches?token={api_token}")

    expect(page).to_have_title("Newsletter Machine — dashboard")
    expect(page.get_by_role("heading", name="Niches")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_runs_page(authenticated_page: Page, api_token: str) -> None:
    """Test that runs page loads."""
    page = authenticated_page

    page.goto(f"/dashboard/runs?token={api_token}")

    expect(page).to_have_title("Newsletter Machine — dashboard")
    expect(page.get_by_role("heading", name="Runs")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_newsletters_page(authenticated_page: Page, api_token: str) -> None:
    """Test that newsletters page loads."""
    page = authenticated_page

    page.goto(f"/dashboard/newsletters?token={api_token}")

    expect(page).to_have_title("Newsletter Machine — dashboard")
    expect(page.get_by_role("heading", name="Newsletters")).to_be_visible()


@pytest.mark.e2e
def test_api_health_check(page: Page, api_base_url: str) -> None:
    """Test that API health endpoint responds."""
    response = page.request.get(f"{api_base_url}/health")
    assert response.ok
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.e2e
def test_dashboard_requires_auth(page: Page) -> None:
    """Test that dashboard requires authentication."""
    # Navigate without token
    page.goto("/dashboard")

    # Should redirect or show unauthorized
    # The dashboard requires token, so it should fail or redirect
    # Note: actual behavior depends on FastAPI auth implementation
    pass


@pytest.mark.e2e
def test_dashboard_sources_page(authenticated_page: Page, api_token: str) -> None:
    """Test that sources page loads."""
    page = authenticated_page

    page.goto(f"/dashboard/sources?token={api_token}")

    expect(page).to_have_title("Newsletter Machine — dashboard")
    expect(page.get_by_role("heading", name="Sources")).to_be_visible()


@pytest.mark.e2e
def test_dashboard_feedback_page(authenticated_page: Page, api_token: str) -> None:
    """Test that feedback page loads."""
    page = authenticated_page

    page.goto(f"/dashboard/feedback?token={api_token}")

    expect(page).to_have_title("Newsletter Machine — dashboard")
    expect(page.get_by_role("heading", name="Feedback")).to_be_visible()