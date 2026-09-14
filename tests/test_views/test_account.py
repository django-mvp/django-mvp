"""Tests for ``mvp.views.account`` — the Account Center's landing page.

Source: mvp/views/account.py, mvp/urls.py, mvp/templates/mvp/account/*.html

Mounted here through a purpose-built urlconf (mirroring
``tests/test_views/test_extra.py``'s ``_urlconf``) rather than through
``demo/urls.py``: T011 mounts the area in the demo app so a human has
something to look at, but this package's own URLconf (``mvp/urls.py``,
decision D2) is the contract this test exercises, independent of where a
project chooses to mount it.
"""

import re
from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.urls import include, path, reverse

ACCOUNT_BASE_TEMPLATE = (
    Path(__file__).resolve().parent.parent.parent
    / "mvp"
    / "templates"
    / "mvp"
    / "account"
    / "base.html"
)


def _render(template_name):
    """Render a template with full request context (anonymous user)."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return render_to_string(template_name, request=request)


def _urlconf():
    """The demo site's URLs, with the Account Center mounted under ``account/``."""
    patterns = [
        path("account/", include("mvp.urls")),
        path("", include("demo.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


def _fixture_urlconf():
    """``mvp.urls`` and the Account Center fixture app's own URLs, plus
    ``demo.urls``: the shell's sidebar renders ``AppMenu``, and
    ``demo/menus.py`` resolves several entries against ``demo.urls`` — a
    urlconf missing it 500s on any full-page render, not just this story's."""
    patterns = [
        path("account/", include("mvp.urls")),
        path("testapp-account/", include("tests.testapp_account.urls")),
        path("", include("demo.urls")),
    ]
    return type("_FixtureURLConf", (), {"urlpatterns": patterns})


ACCOUNT_FIXTURE_URLCONF = _fixture_urlconf()


@pytest.mark.django_db
class TestAccountCenterView:
    """The landing page: who it lets in, and what it shows once they're in."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_anonymous_request_is_redirected_to_sign_in(self, client):
        response = client.get(reverse("account-center"))
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    def test_signed_in_request_renders_inside_the_shell(
        self, client, django_user_model
    ):
        """The area changes nothing about the sidebar, navbar or dock (FR-005)."""
        user = django_user_model.objects.create_user(
            username="accountcenteruser1", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert "mvp-sidebar" in content
        assert "mvp-header" in content

    def test_signed_in_request_shows_the_navigation_panel(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="accountcenteruser2", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert 'aria-label="Account navigation"' in content

    def test_signed_in_request_shows_no_cards(self, client, django_user_model):
        """No app has contributed a card, so the card region renders empty
        rather than falling back to listing the menu (D5, FR-019)."""
        user = django_user_model.objects.create_user(
            username="accountcenteruser3", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert re.search(r'<div id="account-center-cards"[^>]*>\s*</div>', content), (
            "the card region must render present but empty, not a fallback menu "
            "listing and not omitted entirely"
        )

    def test_response_carries_the_heading(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="accountcenteruser4", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert "Account Center" in content

    def test_response_carries_the_introduction(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="accountcenteruser5", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert "Manage your account" in content

    def test_response_carries_a_single_unlinked_breadcrumb(
        self, client, django_user_model
    ):
        """The landing page declares its own trail through ``PageMixin`` —
        no mixin resolves it from the menu (Refined 2026-09-14)."""
        user = django_user_model.objects.create_user(
            username="accountcenteruser6", password="pass123!"
        )
        client.force_login(user)
        response = client.get(reverse("account-center"))
        assert response.context["page"]["breadcrumbs"] == [{"text": "Account Center"}]


class TestAccountLayout:
    """``mvp/account/base.html`` — the layout a page in the area extends
    (FR-012, FR-013)."""

    def test_page_content_renders_beside_the_navigation_panel(self):
        html = _render("tests/account_layout_content.html")
        assert "account-layout-test-content" in html
        assert 'aria-label="Account navigation"' in html

    def test_the_layout_extends_the_projects_own_base_not_the_shell_directly(self):
        """Extends ``base.html`` — the unqualified name a project owns — not
        ``mvp/base.html`` directly, so a project's own base override still
        applies underneath the account layout."""
        source = ACCOUNT_BASE_TEMPLATE.read_text()
        extends_line = next(
            line for line in source.splitlines() if "{% extends" in line
        )
        assert extends_line.strip() == '{% extends "base.html" %}'


@pytest.mark.django_db
class TestAccountMenuCurrentItem:
    """The menu marks the entry matching the current page (FR-014). A page's
    own trail is its own affair — declared with ``breadcrumbs`` on the view,
    like any other page built on ``PageMixin`` (Refined 2026-09-14) — and is
    covered by ``TestAccountCenterView`` below, not here."""

    @pytest.fixture(autouse=True)
    def _account_fixture_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_FIXTURE_URLCONF):
            yield

    def test_the_entry_matching_the_current_page_is_marked_as_current(
        self, client, testapp_account_entries
    ):
        content = client.get(reverse("testapp_account:plain")).content.decode()
        assert re.search(r"menu-active[^>]*>.*?Fixture Plain", content, re.DOTALL), (
            "the fixture's own entry should be marked as the one being viewed"
        )
