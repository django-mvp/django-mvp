"""Tests for ``mvp.urls`` — the Account Center's URLconf.

Source: mvp/urls.py
"""

import importlib
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import (
    NoReverseMatch,
    clear_url_caches,
    get_resolver,
    include,
    path,
    reverse,
)

import mvp.urls as mvp_urls

LOGIN_TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "mvp"
    / "templates"
    / "mvp"
    / "account"
    / "login.html"
)


def _urlconf():
    """A project that mounts only the Account Center, the way ``mvp/urls.py``'s
    own docstring shows a project doing it."""
    patterns = [path("account/", include("mvp.urls"))]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


def _urlconf_mvp_then_allauth():
    """The mount order this project's documentation and django-accounts-center's
    own example both use: the Account Center first, allauth's own URLconf
    second, at the same prefix. Not built at module scope: ``allauth.account``
    is only importable once it is in ``INSTALLED_APPS`` (R11)."""
    patterns = [
        path("account/", include("mvp.urls")),
        path("account/", include("allauth.account.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


def _urlconf_allauth_then_mvp():
    """The opposite mount order (US-2 scenario 2's second half)."""
    patterns = [
        path("account/", include("allauth.account.urls")),
        path("account/", include("mvp.urls")),
    ]
    return type("_URLConf", (), {"urlpatterns": patterns})


def _reload_urlconfs():
    """Rebuild every resolver in this module against ``mvp.urls``'s current
    ``urlpatterns`` (T011).

    ``include("mvp.urls")`` hands a ``URLResolver`` the module object, and the
    resolver's ``url_patterns`` is a ``cached_property`` frozen to the list it
    first read. Reloading ``mvp.urls`` alone rebinds ``mvp.urls.urlpatterns``
    but leaves any resolver that already read the old list stale, so this
    module — which builds ``ACCOUNT_URLCONF`` by calling ``include("mvp.urls")``
    at import time — is reloaded too, rebuilding it with a resolver whose
    cached property has not been read yet. ``clear_url_caches()`` drops
    ``get_resolver()``'s cache, which is keyed by urlconf identity.
    """
    importlib.reload(mvp_urls)
    importlib.reload(sys.modules[__name__])
    clear_url_caches()


@pytest.fixture
def allauth_installed():
    """Installs allauth's account application for the duration of one test
    (T011, T012, T013).

    R11: ``override_settings.enable()`` populates the app registry from
    ``INSTALLED_APPS`` before any other overridden setting takes effect, and
    allauth's ``AccountConfig.ready()`` requires ``AccountMiddleware`` in
    ``MIDDLEWARE`` at that moment — so the two overrides are applied nested,
    ``MIDDLEWARE`` outside, already in place when ``INSTALLED_APPS`` triggers
    the check.
    """
    middleware = override_settings(
        MIDDLEWARE=[
            *settings.MIDDLEWARE,
            "allauth.account.middleware.AccountMiddleware",
        ]
    )
    installed_apps = override_settings(
        INSTALLED_APPS=[*settings.INSTALLED_APPS, "allauth", "allauth.account"]
    )
    middleware.enable()
    installed_apps.enable()
    _reload_urlconfs()
    try:
        yield
    finally:
        installed_apps.disable()
        middleware.disable()
        _reload_urlconfs()


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


class TestAccountLoginURL:
    """``account_login`` — the sign-in page (T002)."""

    @pytest.mark.django_db
    def test_reversing_account_login_serves_a_sign_in_form(self, client):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            response = client.get(reverse("account_login"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "<form" in content
        assert 'type="password"' in content

    def test_the_identifying_fields_label_is_not_hard_coded(self):
        """FR-005: the field's label comes from ``form.username.label`` —
        whatever the user model calls its identifying field — never a
        literal string in the template."""
        assert "form.username.label" in LOGIN_TEMPLATE.read_text()


@pytest.mark.django_db
class TestPackagedEntriesStandDownWhenAllauthIsInstalled:
    """``mvp.urls`` contributes neither ``account_login`` nor
    ``account_logout`` once allauth's account application is installed, so
    which view answers those addresses never depends on mount order (T011,
    FR-003, D1)."""

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
