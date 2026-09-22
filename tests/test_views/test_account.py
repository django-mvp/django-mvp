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
from bs4 import BeautifulSoup
from django.conf import global_settings, settings
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
class TestSignInView:
    """``account_login`` — the sign-in page (T003, FR-006)."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def _post(self, client, username, password):
        return client.post(
            reverse("account_login"), {"username": username, "password": password}
        )

    def test_wrong_password_for_an_existing_account_re_renders_the_form(
        self, client, django_user_model
    ):
        django_user_model.objects.create_user(
            username="signinuser1", password="correct-pass"
        )
        response = self._post(client, "signinuser1", "wrong-pass")

        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous
        assert "Invalid username or password." in response.content.decode()

    def test_an_unknown_username_gets_the_same_treatment(self, client):
        response = self._post(client, "no-such-user", "whatever")

        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous
        assert "Invalid username or password." in response.content.decode()

    def test_the_message_is_identical_whether_the_account_exists_or_not(
        self, client, django_user_model
    ):
        """FR-006: non-disclosure — a failed sign-in must not reveal whether
        the account exists. That equality is the requirement."""
        django_user_model.objects.create_user(
            username="signinuser2", password="correct-pass"
        )
        wrong_password = self._post(client, "signinuser2", "wrong-pass")
        unknown_username = self._post(client, "no-such-user", "whatever")

        wrong_password_alert = BeautifulSoup(
            wrong_password.content.decode(), "html.parser"
        ).find(attrs={"role": "alert"})
        unknown_username_alert = BeautifulSoup(
            unknown_username.content.decode(), "html.parser"
        ).find(attrs={"role": "alert"})

        assert wrong_password_alert is not None
        assert unknown_username_alert is not None
        assert wrong_password_alert.get_text(strip=True) == (
            unknown_username_alert.get_text(strip=True)
        )


@pytest.mark.django_db
class TestSignInViewDefaultRedirect:
    """Where a successful sign-in lands (T004, FR-007, D4)."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def _sign_in(self, client, username, password, next_url=None):
        data = {"username": username, "password": password}
        if next_url is not None:
            data["next"] = next_url
        return client.post(reverse("account_login"), data)

    def test_lands_on_the_account_center_when_the_project_has_not_chosen_a_destination(
        self, client, django_user_model, settings
    ):
        """The demo sets ``LOGIN_REDIRECT_URL`` itself (D12); a project that
        has made no choice is Django's own global default (D10)."""
        settings.LOGIN_REDIRECT_URL = global_settings.LOGIN_REDIRECT_URL
        django_user_model.objects.create_user(
            username="redirectuser1", password="correct-pass"
        )
        response = self._sign_in(client, "redirectuser1", "correct-pass")

        assert response.status_code == 302
        assert response.url == reverse("account-center")

    def test_a_projects_own_login_redirect_url_wins(
        self, client, django_user_model, settings
    ):
        settings.LOGIN_REDIRECT_URL = "/products/"
        django_user_model.objects.create_user(
            username="redirectuser2", password="correct-pass"
        )
        response = self._sign_in(client, "redirectuser2", "correct-pass")

        assert response.status_code == 302
        assert response.url == "/products/"

    def test_a_next_on_the_request_beats_both(self, client, django_user_model):
        django_user_model.objects.create_user(
            username="redirectuser3", password="correct-pass"
        )
        response = self._sign_in(
            client, "redirectuser3", "correct-pass", next_url="/products/"
        )

        assert response.status_code == 302
        assert response.url == "/products/"


@pytest.mark.django_db
class TestSignInViewNextRedirect:
    """The ``next`` allow-list, and the round trip a person actually makes
    (T005, FR-008, Article V)."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_an_off_site_next_is_refused(self, client, django_user_model, settings):
        settings.LOGIN_REDIRECT_URL = global_settings.LOGIN_REDIRECT_URL
        django_user_model.objects.create_user(
            username="nextuser1", password="correct-pass"
        )
        response = client.post(
            reverse("account_login"),
            {
                "username": "nextuser1",
                "password": "correct-pass",
                "next": "https://evil.example/",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("account-center")

    def test_an_in_site_next_is_honoured(self, client, django_user_model):
        django_user_model.objects.create_user(
            username="nextuser2", password="correct-pass"
        )
        response = client.post(
            reverse("account_login"),
            {"username": "nextuser2", "password": "correct-pass", "next": "/products/"},
        )

        assert response.status_code == 302
        assert response.url == "/products/"

    def test_the_full_round_trip_from_a_protected_page_back_to_it(
        self, client, django_user_model, settings
    ):
        """US-1 scenario 6, end to end: with ``LOGIN_URL`` configured the way
        T010 documents, an anonymous visitor to the Account Center reaches
        the packaged sign-in page, and signing in returns them there."""
        settings.LOGIN_URL = "account_login"
        django_user_model.objects.create_user(
            username="nextuser3", password="correct-pass"
        )

        anonymous_visit = client.get(reverse("account-center"))
        assert anonymous_visit.status_code == 302
        assert anonymous_visit.url.startswith(reverse("account_login"))

        signed_in = client.post(
            anonymous_visit.url,
            {"username": "nextuser3", "password": "correct-pass"},
        )

        assert signed_in.status_code == 302
        assert signed_in.url == reverse("account-center")


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
    """``mvp/account/base.html`` — the layout a page in the area extends,
    which declares the navigation itself (FR-012, FR-013)."""

    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        """The area mounted, independent of whether the demo app also mounts
        it (T011): the "overview" entry's ``view_name="account-center"`` has
        to resolve for the navigation to draw it at all."""
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_page_content_renders_beside_the_navigation_panel(self):
        html = _render("tests/account_layout_content.html")
        assert "account-layout-test-content" in html
        assert 'aria-label="Account navigation"' in html

    def test_the_navigation_is_a_landmark_with_an_accessible_name(self):
        html = _render("tests/account_layout_content.html")
        assert 'role="navigation"' in html
        assert 'aria-label="Account navigation"' in html

    def test_it_draws_the_entry_for_the_landing_page(self):
        html = _render("tests/account_layout_content.html")
        assert "Overview" in html

    def test_a_persistent_card_renders_at_the_configured_breakpoint(self):
        """Above ``lg`` (the test suite's configured breakpoint) the
        navigation is a persistent block. ``mvp-desktop-only`` is the same
        stylesheet rule (T015) the header's own desktop/mobile widget split
        uses."""
        html = _render("tests/account_layout_content.html")
        assert "mvp-desktop-only" in html

    def test_a_collapsed_control_renders_below_the_breakpoint(self):
        html = _render("tests/account_layout_content.html")
        assert "mvp-mobile-only" in html

    def test_the_collapsed_control_is_the_packaged_dropdown(self):
        html = _render("tests/account_layout_content.html")
        assert "dropdown" in html
        assert "dropdown-content" in html

    def test_the_menu_is_processed_once_for_both_sites(self):
        """One pass over the tree feeds both render sites. Processing it a
        second time runs every entry's visibility check again for markup that
        has to agree with the first copy anyway."""
        source = ACCOUNT_BASE_TEMPLATE.read_text()
        assert source.count("{% process_menu") == 1

    def test_the_wide_panel_follows_the_content_and_the_collapsed_one_precedes_it(
        self,
    ):
        """Markup order is what places the panel: the wide card after the
        page's content so it sits on the right of the row, the collapsed
        control before it so it stays above the page when the two stack."""
        html = _render("tests/account_layout_content.html")
        content = html.index("account-layout-test-content")
        sites = [
            match.start()
            for match in re.finditer(r'aria-label="Account navigation"', html)
        ]
        assert len(sites) == 2
        collapsed, card = min(sites), max(sites)
        assert collapsed < content < card

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


def _installed_apps_with(*card_apps):
    """``settings.INSTALLED_APPS`` with ``card_apps`` inserted immediately
    before ``"mvp"``.

    The block-and-extend pattern (FR-018) resolves the *first* app in
    INSTALLED_APPS order that ships ``mvp/account/overview.html`` — the
    standard Django app-template-override convention. A contributing app
    installed after ``mvp`` is never reached: the app_directories loader
    returns mvp's own copy on the very first lookup and never tries the
    rest. Appending — the way the old attribute-based mechanism's tests
    did — does not compose these templates; this precedes ``mvp`` instead.
    """
    installed_apps = list(settings.INSTALLED_APPS)
    mvp_index = installed_apps.index("mvp")
    return [*installed_apps[:mvp_index], *card_apps, *installed_apps[mvp_index:]]


@pytest.mark.django_db
class TestAccountCenterCards:
    """The landing page's card region (US-3, T021, reworked T030): an
    installed app contributes by shipping its own copy of
    ``mvp/account/overview.html``, extending the package's template of the
    same name, and adding to ``{% block account.cards %}`` through
    ``{{ block.super }}`` (Refined 2026-09-14). The two fixture apps,
    ``tests.testapp_card_with_menu`` and ``tests.testapp_card_no_menu``
    (T024), are activated per test with ``override_settings(INSTALLED_APPS=...)``
    — never installed globally, so
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

    def _cards(self, content):
        """The ``<c-card>`` surfaces actually rendered inside the card
        region — counted from the real markup, not a context list the view
        no longer builds."""
        soup = BeautifulSoup(content, "html.parser")
        region = soup.find(id="account-center-cards")
        return region.find_all(class_="card")

    def test_with_neither_app_installed_the_region_is_empty(
        self, client, django_user_model
    ):
        self._login(client, django_user_model, "cardsuser0")
        response = client.get(reverse("account-center"))
        assert self._cards(response.content.decode()) == []

    def test_one_contributing_app_renders_its_card_alone(
        self, client, django_user_model
    ):
        self._login(client, django_user_model, "cardsuser1")
        with override_settings(
            INSTALLED_APPS=_installed_apps_with(self.CARD_NO_MENU_APP)
        ):
            response = client.get(reverse("account-center"))
        content = response.content.decode()
        assert len(self._cards(content)) == 1
        assert 'data-testid="testapp-card-no-menu"' in content
        assert "No Menu Card" in content

    def test_two_contributing_apps_both_get_their_card(self, client, django_user_model):
        self._login(client, django_user_model, "cardsuser2")
        with override_settings(
            INSTALLED_APPS=_installed_apps_with(
                self.CARD_WITH_MENU_APP, self.CARD_NO_MENU_APP
            )
        ):
            response = client.get(reverse("account-center"))
        content = response.content.decode()
        assert len(self._cards(content)) == 2
        assert 'data-testid="testapp-card-with-menu"' in content
        assert 'data-testid="testapp-card-no-menu"' in content

    def test_a_menu_entry_alongside_a_card_does_not_disturb_it(
        self, client, django_user_model, card_with_menu_entries
    ):
        """FR-020, from the other direction: ``testapp_card_with_menu`` has a
        real, resolvable menu entry attached here, and it does not prevent,
        duplicate, or otherwise disturb its own card contribution."""
        self._login(client, django_user_model, "cardsuser3")
        with override_settings(
            INSTALLED_APPS=_installed_apps_with(self.CARD_WITH_MENU_APP)
        ):
            response = client.get(reverse("account-center"))
        content = response.content.decode()
        assert len(self._cards(content)) == 1
        assert 'data-testid="testapp-card-with-menu"' in content
        assert "With Menu Card" in content
        assert "Card With Menu Fixture" in content
