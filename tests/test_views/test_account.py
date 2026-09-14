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
from django.apps import apps as django_apps
from django.conf import settings
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
class TestAccountSectionTrail:
    """``page.breadcrumbs`` for a page in the area (US-2, T017): the area
    itself, then the active section ``get_active_section`` resolves, with the
    last crumb carrying no link (FR-014, FR-015, FR-016)."""

    @pytest.fixture(autouse=True)
    def _account_fixture_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_FIXTURE_URLCONF):
            yield

    def test_a_page_at_a_sections_own_address_names_the_area_and_that_section(
        self, client, testapp_account_entries
    ):
        response = client.get(reverse("testapp_account:grouped"))
        assert response.context["page"]["breadcrumbs"] == [
            {"text": "Account Center", "href": reverse("account-center")},
            {"text": "Fixture Grouped Item"},
        ]

    def test_a_page_below_a_sections_address_names_that_section_and_links_to_it(
        self, client, testapp_account_entries
    ):
        response = client.get(reverse("testapp_account:grouped-detail"))
        assert response.context["page"]["breadcrumbs"] == [
            {"text": "Account Center", "href": reverse("account-center")},
            {
                "text": "Fixture Grouped Item",
                "href": reverse("testapp_account:grouped"),
            },
        ]

    def test_a_page_no_entry_points_at_renders_a_trail_naming_the_area_alone(
        self, client, django_user_model
    ):
        """No fixture entries applied here (no ``testapp_account_entries``
        fixture requested), and the landing page's own "overview" entry is
        excluded from section resolution by design — it names the area, not
        a section below it (FR-015 scenario 7)."""
        user = django_user_model.objects.create_user(
            username="trailuser1", password="pass123!"
        )
        client.force_login(user)
        response = client.get(reverse("account-center"))
        assert response.context["page"]["breadcrumbs"] == [{"text": "Account Center"}]

    def test_the_entry_matching_the_current_page_is_marked_as_current(
        self, client, testapp_account_entries
    ):
        content = client.get(reverse("testapp_account:plain")).content.decode()
        assert re.search(r"menu-active[^>]*>.*?Fixture Plain", content, re.DOTALL), (
            "the fixture's own entry should be marked as the one being viewed"
        )


@pytest.mark.django_db
class TestAccountCenterCards:
    """The landing page's card region (US-3, T021): what an installed app's
    ``account_center_card_template``/``account_center_card_context`` attributes
    put there. The two fixture apps, ``tests.testapp_card_with_menu`` and
    ``tests.testapp_card_no_menu`` (T024), are activated per test with
    ``override_settings(INSTALLED_APPS=...)`` — never installed globally, so
    ``TestAccountCenterView.test_signed_in_request_shows_no_cards`` above stays
    green (ARC-001). Mounted through ``ACCOUNT_FIXTURE_URLCONF`` so
    ``testapp_account:plain`` — the target ``testapp_card_with_menu``'s entry
    points at — resolves.
    """

    CARD_WITH_MENU_APP = "tests.testapp_card_with_menu"
    CARD_NO_MENU_APP = "tests.testapp_card_no_menu"

    @pytest.fixture(autouse=True)
    def _account_fixture_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_FIXTURE_URLCONF):
            yield

    def _login(self, client, django_user_model, username):
        user = django_user_model.objects.create_user(
            username=username, password="pass123!"
        )
        client.force_login(user)

    def test_a_card_renders_with_the_context_its_app_supplies(
        self, client, django_user_model
    ):
        self._login(client, django_user_model, "cardsuser1")
        with override_settings(
            INSTALLED_APPS=[*settings.INSTALLED_APPS, self.CARD_NO_MENU_APP]
        ):
            response = client.get(reverse("account-center"))
        assert len(response.context["account_center_cards"]) == 1
        content = response.content.decode()
        assert 'data-testid="testapp-card-no-menu"' in content
        assert "No Menu Card" in content

    def test_two_contributing_apps_both_get_their_card(self, client, django_user_model):
        self._login(client, django_user_model, "cardsuser2")
        with override_settings(
            INSTALLED_APPS=[
                *settings.INSTALLED_APPS,
                self.CARD_WITH_MENU_APP,
                self.CARD_NO_MENU_APP,
            ]
        ):
            response = client.get(reverse("account-center"))
        assert len(response.context["account_center_cards"]) == 2
        content = response.content.decode()
        assert 'data-testid="testapp-card-with-menu"' in content
        assert 'data-testid="testapp-card-no-menu"' in content

    def test_an_app_declaring_no_card_contributes_nothing_and_the_page_still_renders(
        self, client, django_user_model
    ):
        """Only ``testapp_card_no_menu`` declares a card here; every other
        installed app (``testapp_account``, ``demo``, the Django contrib
        apps) declares none, so exactly one card renders and the page still
        returns 200 rather than erroring on an app with nothing to collect."""
        self._login(client, django_user_model, "cardsuser3")
        with override_settings(
            INSTALLED_APPS=[*settings.INSTALLED_APPS, self.CARD_NO_MENU_APP]
        ):
            response = client.get(reverse("account-center"))
        assert response.status_code == 200
        assert len(response.context["account_center_cards"]) == 1
        assert 'data-testid="testapp-card-no-menu"' in response.content.decode()

    def test_a_menu_entry_alongside_a_card_does_not_disturb_collection(
        self, client, django_user_model, card_with_menu_entries
    ):
        """FR-020, from the other direction: ``testapp_card_with_menu`` has a
        real, resolvable menu entry attached here, and it does not prevent,
        duplicate, or otherwise disturb its own card being collected."""
        self._login(client, django_user_model, "cardsuser4")
        with override_settings(
            INSTALLED_APPS=[*settings.INSTALLED_APPS, self.CARD_WITH_MENU_APP]
        ):
            response = client.get(reverse("account-center"))
        assert len(response.context["account_center_cards"]) == 1
        content = response.content.decode()
        assert 'data-testid="testapp-card-with-menu"' in content
        assert "With Menu Card" in content
        assert "Card With Menu Fixture" in content

    def test_a_cards_context_cannot_replace_the_pages_own(
        self, client, django_user_model, monkeypatch
    ):
        """A card is rendered in a context of its own, so a card context that
        names a key the page itself uses — ``user`` is the one with teeth,
        since the shell's user menu and avatar resolve it — changes what that
        card sees and nothing else. Merging card contexts into the page's own
        made this silently replace the signed-in user for the whole render:
        the page returned 200 with the user display gone."""
        self._login(client, django_user_model, "victim")
        with override_settings(
            INSTALLED_APPS=[*settings.INSTALLED_APPS, self.CARD_NO_MENU_APP]
        ):
            app_config = django_apps.get_app_config("testapp_card_no_menu")
            monkeypatch.setattr(
                app_config,
                "account_center_card_context",
                lambda request: {"user": "I AM NOT A USER OBJECT"},
                raising=False,
            )
            response = client.get(reverse("account-center"))

        assert response.status_code == 200
        # The view's own context dict — what the page and the shell around it
        # render from. Merging card contexts into it put the card's value here,
        # replacing the signed-in user for the whole render.
        assert "user" not in response.context_data
        # The card still received what its own app supplied.
        assert 'data-testid="testapp-card-no-menu"' in response.content.decode()
