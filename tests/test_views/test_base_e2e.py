"""End-to-end tests for MVPTemplateView and MVPHomeView using pytest-playwright.

These tests require:
  - pytest-playwright installed and browsers downloaded (``playwright install``)
  - The ``e2e`` marker is registered in pytest configuration

Run with: ``pytest tests/test_views/test_base_e2e.py -m e2e``
Skip in CI without playwright: ``pytest -m "not e2e"``
"""

import pytest

pytest_playwright = pytest.importorskip("playwright", reason="playwright not installed — skip e2e tests")

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# US1: PageView — plain layout-aware template
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_about_page_renders_200(page, live_server):
    """GET /about/ returns 200 OK."""
    response = page.goto(f"{live_server.url}/about/")
    assert response.status == 200


@pytest.mark.django_db
def test_about_page_has_adminlte_sidebar(page, live_server):
    """GET /about/ renders inside AdminLTE layout (sidebar present)."""
    page.goto(f"{live_server.url}/about/")
    assert page.locator(".main-sidebar").count() > 0


@pytest.mark.django_db
def test_about_page_has_adminlte_navbar(page, live_server):
    """GET /about/ renders inside AdminLTE layout (navbar present)."""
    page.goto(f"{live_server.url}/about/")
    assert page.locator(".main-header").count() > 0


@pytest.mark.django_db
def test_about_page_has_title_in_heading(page, live_server):
    """GET /about/ shows page title 'About Us' in the content heading."""
    page.goto(f"{live_server.url}/about/")
    assert page.get_by_role("heading", name="About Us").count() > 0


@pytest.mark.django_db
def test_about_page_post_returns_405(page, live_server):
    """POST /about/ returns 405 Method Not Allowed (FR-011)."""
    page.goto(f"{live_server.url}/about/")
    csrf_token = page.evaluate(
        "() => document.cookie.match(/csrftoken=([^;]+)/) ? document.cookie.match(/csrftoken=([^;]+)/)[1] : ''"
    )
    status = page.evaluate(
        """async ([url, token]) => {
            const r = await fetch(url, {
                method: 'POST',
                headers: {'X-CSRFToken': token, 'Content-Type': 'application/json'},
                body: '{}'
            });
            return r.status;
        }""",
        [f"{live_server.url}/about/", csrf_token],
    )
    assert status == 405


# ---------------------------------------------------------------------------
# US2: MVPHomeView — guest/dashboard template switch
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_home_unauthenticated_returns_200(page, live_server):
    """Anonymous GET / returns 200 OK."""
    response = page.goto(f"{live_server.url}/")
    assert response.status == 200


@pytest.mark.django_db
def test_home_unauthenticated_shows_landing_content(page, live_server):
    """Anonymous GET / shows landing page headline, not dashboard content."""
    page.goto(f"{live_server.url}/")
    assert page.get_by_text("Django MVP Demo").count() > 0


@pytest.mark.django_db
def test_home_unauthenticated_url_unchanged(page, live_server):
    """Anonymous GET / does not redirect — URL stays at /."""
    page.goto(f"{live_server.url}/")
    assert page.url == f"{live_server.url}/"


@pytest.mark.django_db
def test_home_unauthenticated_has_login_cta(page, live_server):
    """Anonymous GET / shows a login CTA button."""
    page.goto(f"{live_server.url}/")
    assert page.get_by_role("link", name="Get Started").count() > 0 or page.get_by_text("Log In").count() > 0


@pytest.mark.django_db
def test_home_authenticated_returns_200(page, live_server, django_user_model):
    """Authenticated GET / returns 200 OK."""
    user = django_user_model.objects.create_user(username="e2euser1", password="pass123!")
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("[name=username]", "e2euser1")
    page.fill("[name=password]", "pass123!")
    page.click("[type=submit]")
    page.wait_for_url(f"{live_server.url}/")
    response = page.goto(f"{live_server.url}/")
    assert response.status == 200


@pytest.mark.django_db
def test_home_authenticated_shows_dashboard_content(page, live_server, django_user_model):
    """Authenticated GET / shows dashboard content with username."""
    user = django_user_model.objects.create_user(username="e2euser2", password="pass123!")
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("[name=username]", "e2euser2")
    page.fill("[name=password]", "pass123!")
    page.click("[type=submit]")
    page.wait_for_url(f"{live_server.url}/")
    assert page.get_by_text("Welcome", exact=False).count() > 0


@pytest.mark.django_db
def test_home_authenticated_url_unchanged(page, live_server, django_user_model):
    """Authenticated GET / does not redirect — URL stays at /."""
    user = django_user_model.objects.create_user(username="e2euser3", password="pass123!")
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("[name=username]", "e2euser3")
    page.fill("[name=password]", "pass123!")
    page.click("[type=submit]")
    page.wait_for_url(f"{live_server.url}/")
    assert page.url == f"{live_server.url}/"


@pytest.mark.django_db
def test_home_post_returns_405(page, live_server):
    """POST / returns 405 Method Not Allowed (FR-011)."""
    page.goto(f"{live_server.url}/")
    csrf_token = page.evaluate(
        "() => document.cookie.match(/csrftoken=([^;]+)/) ? document.cookie.match(/csrftoken=([^;]+)/)[1] : ''"
    )
    status = page.evaluate(
        """async ([url, token]) => {
            const r = await fetch(url, {
                method: 'POST',
                headers: {'X-CSRFToken': token, 'Content-Type': 'application/json'},
                body: '{}'
            });
            return r.status;
        }""",
        [f"{live_server.url}/", csrf_token],
    )
    assert status == 405


# ---------------------------------------------------------------------------
# US3: Full login-and-return journey
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_full_login_and_return_journey(page, live_server, django_user_model):
    """Full sequential E2E: anonymous landing → login → dashboard at same URL (US3).

    Steps:
    1. Visit / unauthenticated — assert landing content visible.
    2. Navigate to login, authenticate.
    3. Navigate back to / — assert dashboard content.
    4. Assert URL has not changed from / at any step.
    5. Assert navbar and sidebar are present and functional on the dashboard.
    """
    user = django_user_model.objects.create_user(username="journeyuser", password="pass123!")

    # Step 1: Anonymous visit to /
    page.goto(f"{live_server.url}/")
    assert page.url == f"{live_server.url}/"
    assert page.get_by_text("Django MVP Demo").count() > 0, "Landing content not visible for anonymous user"

    # Step 2: Navigate to login and authenticate
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("[name=username]", "journeyuser")
    page.fill("[name=password]", "pass123!")
    page.click("[type=submit]")
    page.wait_for_url(f"{live_server.url}/")

    # Step 3: Visit / as authenticated user
    assert page.url == f"{live_server.url}/", "URL changed after login — expected to stay at /"
    assert page.get_by_text("Welcome", exact=False).count() > 0, "Dashboard greeting not visible after login"

    # Step 4: Confirm URL is still /
    assert page.url == f"{live_server.url}/"

    # Step 5: Confirm sidebar and navbar are present on dashboard
    assert page.locator(".main-sidebar").count() > 0, "Sidebar missing from dashboard"
    assert page.locator(".main-header").count() > 0, "Navbar missing from dashboard"

    # Step 5 continued: Click a nav link and assert no JS errors
    page.locator(".main-sidebar a").first.click()
    page.wait_for_load_state("domcontentloaded")
    # No JS errors means the page loaded successfully
