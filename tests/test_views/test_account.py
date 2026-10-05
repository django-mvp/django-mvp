"""Tests for ``mvp.views.account`` — the Account Center's landing page.

Source: mvp/views/account.py, mvp/urls.py, mvp/templates/mvp/account/*.html

Mounted here through a purpose-built urlconf (mirroring
``tests/test_views/test_extra.py``'s ``_urlconf``) rather than through
``demo/urls.py``: T011 mounts the area in the demo app so a human has
something to look at, but this package's own URLconf (``mvp/urls.py``,
decision D2) is the contract this test exercises, independent of where a
project chooses to mount it.
"""

import copy
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.conf import global_settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.urls import include, path, reverse

from mvp.config import MVP_CONFIG


# A project's own template at the same path: mirrors mvp/templates/mvp/account/login.html
# in demo/templates/tests/, the loader's DIRS checked ahead of any app's own APP_DIRS
# entry (T009, FR-010) — scoped to the one test that needs it via override_settings
# rather than a permanent shadow every other test in this module would then sit under.
PROJECT_OVERRIDE_TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent.parent / "demo" / "templates" / "tests"
)


def _render(template_name):
    """Render a template with full request context (anonymous user)."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return render_to_string(template_name, request=request)


def _urlconf():
    """The demo site's URLs, which include ``mvp.urls``. Including it a second
    time would mount the Account Center twice, which the package refuses."""
    patterns = [
        path("", include("demo.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


def _fixture_urlconf():
    """The Account Center fixture app's own URLs, plus
    ``demo.urls`` (which includes ``mvp.urls``): the shell's sidebar renders
    ``AppMenu``, and
    ``demo/menus.py`` resolves several entries against ``demo.urls`` — a
    urlconf missing it 500s on any full-page render, not just this story's."""
    patterns = [
        path("testapp-account/", include("tests.testapp_account.urls")),
        path("", include("demo.urls")),
    ]
    return type("_FixtureURLConf", (), {"urlpatterns": patterns})


ACCOUNT_FIXTURE_URLCONF = _fixture_urlconf()
OVERRIDE_TEMPLATES = (
    Path(__file__).resolve().parents[1] / "fixtures" / "override_templates"
)


@pytest.mark.django_db
class TestSignInView:
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
        assert response.context["form"].has_error("__all__", code="invalid_login")

    def test_an_unknown_username_gets_the_same_treatment(self, client):
        response = self._post(client, "no-such-user", "whatever")

        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous
        assert response.context["form"].has_error("__all__", code="invalid_login")


@pytest.mark.django_db
class TestSignInViewDefaultRedirect:
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
class TestSignInViewAuthenticatedVisitor:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_a_signed_in_client_requesting_the_sign_in_address_is_redirected(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="alreadysignedin", password="correct-pass"
        )
        client.force_login(user)

        response = client.get(reverse("account_login"))

        assert response.status_code == 302


@pytest.mark.django_db
class TestSignOutView:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_a_post_by_a_signed_in_client_ends_the_session_and_renders_the_signed_out_page(
        self, client, django_user_model, settings
    ):
        settings.LOGOUT_REDIRECT_URL = global_settings.LOGOUT_REDIRECT_URL
        user = django_user_model.objects.create_user(
            username="signoutuser1", password="correct-pass"
        )
        client.force_login(user)

        response = client.post(reverse("account_logout"))

        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous
        assert response.templates[0].name == "mvp/account/logout.html"

    def test_a_get_does_not_end_the_session(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="signoutuser2", password="correct-pass"
        )
        client.force_login(user)

        client.get(reverse("account_logout"))

        assert client.session.get("_auth_user_id") is not None

    def test_an_anonymous_post_is_not_an_error(self, client, settings):
        settings.LOGOUT_REDIRECT_URL = global_settings.LOGOUT_REDIRECT_URL

        response = client.post(reverse("account_logout"))

        assert response.status_code == 200


@pytest.mark.django_db
class TestPackagedTemplatesAreOverridable:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_a_projects_own_sign_in_template_is_used_instead(self, client, settings):
        templates_config = copy.deepcopy(settings.TEMPLATES)
        templates_config[0]["DIRS"] = [str(PROJECT_OVERRIDE_TEMPLATES_DIR)]

        with override_settings(TEMPLATES=templates_config):
            response = client.get(reverse("account_login"))

        assert response.status_code == 200
        assert response.content.decode().strip() == "project-overridden-sign-in-page"


def _urlconf_with_allauth():
    """``mvp.urls`` mounted alongside allauth's own URLconf, the same order
    ``tests/test_urls.py``'s T012 exercises: the packaged pages stand down
    and allauth's own answer instead (T015, US-3 scenario 3). Not built at
    module scope: ``allauth.account`` is only importable once it is in
    ``INSTALLED_APPS`` (R11)."""
    patterns = [
        path("", include("mvp.urls")),
        path("account/", include("allauth.account.urls")),
        path("", include("demo.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


@pytest.mark.django_db
class TestDevelopmentNotice:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_the_sign_in_page_carries_the_notice(self, client):
        content = client.get(reverse("account_login")).content.decode()
        soup = BeautifulSoup(content, "html.parser")

        assert soup.find(class_="alert-warning") is not None

    def test_the_sign_out_page_carries_the_notice(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="noticeuser1", password="correct-pass"
        )
        client.force_login(user)

        content = client.post(reverse("account_logout")).content.decode()
        soup = BeautifulSoup(content, "html.parser")

        assert soup.find(class_="alert-warning") is not None


@pytest.mark.django_db
class TestDevelopmentNoticeAbsence:
    def test_with_allauth_installed_the_sign_in_page_carries_no_notice_of_ours(
        self, client, allauth_installed
    ):
        with override_settings(ROOT_URLCONF=_urlconf_with_allauth()):
            content = client.get(reverse("account_login")).content.decode()
        soup = BeautifulSoup(content, "html.parser")

        assert soup.find(class_="alert-warning") is None

    def test_a_projects_own_template_carries_no_notice_of_ours(self, client, settings):
        templates_config = copy.deepcopy(settings.TEMPLATES)
        templates_config[0]["DIRS"] = [str(PROJECT_OVERRIDE_TEMPLATES_DIR)]

        with override_settings(
            ROOT_URLCONF=ACCOUNT_URLCONF, TEMPLATES=templates_config
        ):
            content = client.get(reverse("account_login")).content.decode()
        soup = BeautifulSoup(content, "html.parser")

        assert soup.find(class_="alert-warning") is None


@pytest.mark.django_db
class TestAccountCenterView:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_anonymous_request_is_redirected_to_sign_in(self, client):
        response = client.get(reverse("account-center"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
        assert not response.url.startswith("/accounts/login/")

    def test_signed_in_request_renders_inside_the_shell(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="accountcenteruser1", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert "mvp-sidebar" in content
        assert "mvp-header" in content

    def test_the_title_is_a_bar_then_the_area_then_the_site(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="accountcentertitle", password="pass123!"
        )
        client.force_login(user)
        response = client.get(reverse("account-center"))
        soup = BeautifulSoup(response.content, "html.parser")
        assert " ".join(soup.title.get_text().split()) == (
            "| Account Center | example.com"
        )

    def test_signed_in_request_shows_no_cards(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="accountcenteruser3", password="pass123!"
        )
        client.force_login(user)
        content = client.get(reverse("account-center")).content.decode()
        assert re.search(r'<div id="account-center-cards"[^>]*>\s*</div>', content), (
            "the card region must render present but empty, not a fallback menu "
            "listing and not omitted entirely"
        )

    def test_response_carries_a_single_unlinked_breadcrumb(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="accountcenteruser6", password="pass123!"
        )
        client.force_login(user)
        response = client.get(reverse("account-center"))
        assert response.context["page"]["breadcrumbs"] == [{"text": "Account Center"}]


def sidebar_labels(response):
    """The brand link, then every link in a sidebar menu, by text."""
    soup = BeautifulSoup(response.content, "html.parser")
    sidebar = soup.select_one("aside.mvp-sidebar")
    links = sidebar.select("a.mvp-sidebar-brand, ul a")
    return [a.get_text(" ", strip=True) for a in links]


def main_content(response):
    """The page's ``<main>`` element."""
    return BeautifulSoup(response.content, "html.parser").select_one("main")


@pytest.mark.django_db
class TestAccountLayout:
    @pytest.fixture(autouse=True)
    def _account_fixture_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_FIXTURE_URLCONF):
            yield

    @pytest.fixture
    def signed_in(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username="accountlayoutuser", password="pass123!"
        )
        client.force_login(user)
        return client

    def test_the_landing_sidebar_carries_the_account_menu_under_a_back_link(
        self, signed_in
    ):
        labels = sidebar_labels(signed_in.get(reverse("account-center")))

        assert labels[1:3] == ["Back to example.com", "Account Center"]

    def test_the_landing_sidebar_carries_none_of_the_host_menu(self, signed_in):
        labels = sidebar_labels(signed_in.get(reverse("account-center")))

        assert "Home" not in labels
        assert "Layout" not in labels

    @pytest.mark.parametrize("breakpoint", ["sm", "lg", "2xl", "never"])
    def test_no_second_navigation_is_drawn_in_the_main_content(
        self, signed_in, monkeypatch, breakpoint
    ):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "breakpoint", breakpoint)

        main = main_content(signed_in.get(reverse("account-center")))

        assert main.select(".dropdown, .menu") == []
        assert "Account navigation" not in str(main)

    def test_a_page_written_against_the_layout_renders_inside_the_area(
        self, signed_in, testapp_account_entries
    ):
        response = signed_in.get(reverse("testapp_account:plain"))

        assert response.status_code == 200
        assert b'id="testapp-account-plain-content"' in response.content

    def test_that_pages_entry_is_current_in_the_sidebar(
        self, signed_in, testapp_account_entries
    ):
        response = signed_in.get(reverse("testapp_account:plain"))
        soup = BeautifulSoup(response.content, "html.parser")

        current = soup.select("aside.mvp-sidebar a.menu-active")

        assert [a.get_text(" ", strip=True) for a in current] == ["Fixture Plain"]

    def test_that_pages_sidebar_is_the_account_menu_under_a_back_link(
        self, signed_in, testapp_account_entries
    ):
        labels = sidebar_labels(signed_in.get(reverse("testapp_account:plain")))

        assert labels[1:3] == ["Back to example.com", "Account Center"]
        assert "Fixture Plain" in labels
        assert "Home" not in labels


@pytest.mark.django_db
class TestAccountCenterCards:
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
        """The ``<c-mvp.card>`` surfaces actually rendered inside the card
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

    def test_a_project_template_adds_its_card_to_the_region(
        self, client, django_user_model, settings
    ):
        engine = settings.TEMPLATES[0]
        settings.TEMPLATES = [
            {**engine, "DIRS": [str(OVERRIDE_TEMPLATES), *engine.get("DIRS", [])]}
        ]
        self._login(client, django_user_model, "cardsuser1")

        response = client.get(reverse("account-center"))

        (card,) = self._cards(response.content.decode())
        assert card.find(attrs={"data-testid": "project-account-card"}) is not None


@pytest.mark.django_db
class TestSignInFieldNaming:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def _render_with_label(self, label):
        """Render the real page against a form whose identifying field
        carries ``label``, standing in for a user model that names it
        something other than ``username``."""
        form = AuthenticationForm()
        form.fields["username"].label = label
        request = RequestFactory().get(reverse("account_login"))
        request.user = AnonymousUser()
        return render_to_string(
            "mvp/account/login.html", {"form": form, "next": ""}, request=request
        )

    def test_the_placeholder_names_the_field_the_model_declares(self):
        html = self._render_with_label("Email address")

        assert 'placeholder="Email address"' in html
        assert 'placeholder="Username"' not in html
