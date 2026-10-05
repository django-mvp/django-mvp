"""Tests for ``mvp.urls`` — the Account Center's URLconf.

Source: mvp/urls.py
"""

import pytest
from django.test import override_settings
from django.urls import (
    NoReverseMatch,
    get_resolver,
    include,
    path,
    resolve,
    reverse,
)

from mvp.views.account import AccountCenterView, account_center


def _urlconf():
    """A project that mounts only the Account Center, the way ``mvp/urls.py``'s
    own docstring shows a project doing it."""
    patterns = [path("", include("mvp.urls"))]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


def _urlconf_mvp_then_allauth():
    """The mount order this project's documentation and django-accounts-center's
    own example both use: the Account Center first, allauth's own URLconf
    second, under ``account/``. Not built at module scope: ``allauth.account``
    is only importable once it is in ``INSTALLED_APPS`` (R11)."""
    patterns = [
        path("", include("mvp.urls")),
        path("account/", include("allauth.account.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


def _urlconf_allauth_then_mvp():
    """The opposite mount order (US-2 scenario 2's second half)."""
    patterns = [
        path("account/", include("allauth.account.urls")),
        path("", include("mvp.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


def _count_registrations(urlconf, name):
    """How many patterns in ``urlconf``, walked recursively through every
    ``include()``, register ``name`` (T013)."""

    def _walk(url_patterns):
        count = 0
        for entry in url_patterns:
            if hasattr(entry, "url_patterns"):
                count += _walk(entry.url_patterns)
            elif getattr(entry, "name", None) == name:
                count += 1
        return count

    return _walk(get_resolver(urlconf).url_patterns)


class TestMountedAtTheSiteRoot:
    def test_the_account_pages_sit_under_account(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            assert reverse("account-center") == "/account/"
            assert reverse("account_login") == "/account/login/"
            assert reverse("account_logout") == "/account/logout/"


class TestAccountLoginURL:
    @pytest.mark.django_db
    def test_reversing_account_login_serves_a_sign_in_form(self, client):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            response = client.get(reverse("account_login"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "<form" in content
        assert 'type="password"' in content


@pytest.mark.django_db
class TestPackagedEntriesStandDownWhenAllauthIsInstalled:
    def test_without_allauth_both_names_are_present_and_answer(self, client):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            assert client.get(reverse("account_login")).status_code == 200
            assert client.post(reverse("account_logout")).status_code == 200

    def test_with_allauth_installed_neither_name_is_registered(self, allauth_installed):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            with pytest.raises(NoReverseMatch):
                reverse("account_login")
            with pytest.raises(NoReverseMatch):
                reverse("account_logout")


@pytest.mark.django_db
class TestAllauthAnswersRegardlessOfMountOrder:
    def test_mvp_mounted_before_allauth(self, client, allauth_installed):
        # Local import: allauth.account is only importable once INSTALLED_APPS
        # carries it (R11), which allauth_installed has just arranged.
        from allauth.account.views import LoginView, LogoutView

        with override_settings(ROOT_URLCONF=_urlconf_mvp_then_allauth()):
            assert resolve(reverse("account_login")).func.view_class is LoginView
            assert resolve(reverse("account_logout")).func.view_class is LogoutView
            assert client.get(reverse("account_login")).status_code == 200

    def test_allauth_mounted_before_mvp(self, client, allauth_installed):
        from allauth.account.views import LoginView, LogoutView

        with override_settings(ROOT_URLCONF=_urlconf_allauth_then_mvp()):
            assert resolve(reverse("account_login")).func.view_class is LoginView
            assert resolve(reverse("account_logout")).func.view_class is LogoutView
            assert client.get(reverse("account_login")).status_code == 200


@pytest.mark.django_db
class TestEachNameIsRegisteredExactlyOnce:
    def test_with_allauth_mvp_mounted_first(self, allauth_installed):
        urlconf = _urlconf_mvp_then_allauth()
        assert _count_registrations(urlconf, "account_login") == 1
        assert _count_registrations(urlconf, "account_logout") == 1

    def test_with_allauth_allauth_mounted_first(self, allauth_installed):
        urlconf = _urlconf_allauth_then_mvp()
        assert _count_registrations(urlconf, "account_login") == 1
        assert _count_registrations(urlconf, "account_logout") == 1


class TestPwaUrls:
    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_routes_are_absent_when_the_feature_is_off(self):
        with pytest.raises(NoReverseMatch):
            reverse("mvp-pwa-manifest")
        with pytest.raises(NoReverseMatch):
            reverse("mvp-pwa-service-worker")

    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    @pytest.mark.usefixtures("pwa_enabled")
    def test_the_two_routes_have_fixed_names_and_paths(self):
        assert reverse("mvp-pwa-manifest") == "/manifest.webmanifest"
        assert reverse("mvp-pwa-service-worker") == "/sw.js"

    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    @pytest.mark.usefixtures("pwa_enabled")
    def test_the_routes_resolve_to_the_packaged_views(self):
        assert resolve("/manifest.webmanifest").func.__name__ == "manifest"
        assert resolve("/sw.js").func.__name__ == "service_worker"


class TestAccountCenterMount:
    @pytest.fixture(autouse=True)
    def _account_urlconf(self):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            yield

    def test_the_landing_resolves_to_the_account_center_view(self):

        assert resolve("/account/").func.view_class is AccountCenterView

    def test_the_landing_is_served_for_the_account_center(self):

        assert resolve("/account/").func.mounted_app is account_center

    def test_the_sign_in_page_is_outside_the_mount(self):
        match = resolve("/account/login/")

        assert getattr(match.func, "mounted_app", None) is None
