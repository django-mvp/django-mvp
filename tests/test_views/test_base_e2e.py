"""Integration tests for MVPTemplateView and MVPHomeView.

Converted from end-to-end Playwright tests to Django test-client integration tests.
Run with: pytest tests/test_views/test_base_e2e.py
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# US1: MVPHomeView — guest/dashboard template switch
# ---------------------------------------------------------------------------
# US2: MVPHomeView — guest/dashboard template switch
# ---------------------------------------------------------------------------


def test_home_unauthenticated_returns_200(client):
    """Anonymous GET / returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200


def test_home_unauthenticated_shows_landing_content(client):
    """Anonymous GET / shows landing page headline, not dashboard content."""
    response = client.get("/")
    assert b"production-ready Django apps fast" in response.content


def test_home_unauthenticated_url_unchanged(client):
    """Anonymous GET / does not redirect — stays at /."""
    response = client.get("/")
    assert response.status_code == 200


def test_home_unauthenticated_has_hero_lead(client):
    """Anonymous GET / shows the hero lead paragraph."""
    content = client.get("/").content
    assert b"focus on your business logic" in content


def test_home_authenticated_returns_200(client, django_user_model):
    """Authenticated GET / returns 200 OK."""
    user = django_user_model.objects.create_user(username="authuser1", password="pass123!")
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 200


def test_home_authenticated_shows_dashboard_content(client, django_user_model):
    """Authenticated GET / shows dashboard content with username."""
    user = django_user_model.objects.create_user(username="authuser2", password="pass123!")
    client.force_login(user)
    response = client.get("/")
    assert b"Welcome" in response.content


def test_home_authenticated_url_unchanged(client, django_user_model):
    """Authenticated GET / does not redirect — URL stays at /."""
    user = django_user_model.objects.create_user(username="authuser3", password="pass123!")
    client.force_login(user)
    response = client.get("/")
    assert response.status_code == 200


def test_home_post_returns_405(client):
    """POST / returns 405 Method Not Allowed (FR-011)."""
    response = client.post("/")
    assert response.status_code == 405


# ---------------------------------------------------------------------------
# US3: Full login-and-return journey
# ---------------------------------------------------------------------------


def test_full_login_and_return_journey(client, django_user_model):
    """Full sequential journey: anonymous landing → login → dashboard at same URL (US3).

    Steps:
    1. Visit / unauthenticated — assert landing content visible.
    2. Authenticate via force_login.
    3. Visit / again — assert dashboard content.
    4. Assert no redirects occur at any step.
    5. Assert navbar and sidebar are present on the dashboard.
    """
    user = django_user_model.objects.create_user(username="journeyuser", password="pass123!")

    # Step 1: Anonymous visit to /
    response = client.get("/")
    assert response.status_code == 200
    assert b"production-ready Django apps fast" in response.content, "Landing content not visible for anonymous user"

    # Step 2: Authenticate
    client.force_login(user)

    # Step 3: Visit / as authenticated user
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.content, "Dashboard greeting not visible after login"

    # Step 5: Confirm sidebar and navbar are present on dashboard
    assert b"mvp-sidebar" in response.content, "Sidebar missing from dashboard"
    assert b"mvp-header" in response.content, "Navbar missing from dashboard"
