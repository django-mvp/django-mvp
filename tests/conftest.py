"""Shared test fixtures for django-mvp test suite.

Standardized per Phase 2: all model fixtures and view factory helpers live here
so individual test files stay focused on assertions, not setup boilerplate.
"""

import importlib
import importlib.util
import os
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import clear_url_caches
from django.views.generic import TemplateView

import mvp.urls as mvp_urls
from mvp.config import MVP_CONFIG
from mvp.menus import AccountCenterMenu
from tests.factories import ArticleFactory, CategoryFactory, ProductFactory
from tests.testapp_account.menus import build_entries
from tests.testapp_card_with_menu.menus import (
    build_entries as build_card_with_menu_entries,
)

User = get_user_model()


def _reload_urlconfs(module):
    """Rebuild every resolver in ``module`` against ``mvp.urls``'s current
    ``urlpatterns`` (T011, D17).

    ``include("mvp.urls")`` hands a ``URLResolver`` the module object, and
    the resolver's ``url_patterns`` is a ``cached_property`` frozen to the
    list it first read. Reloading ``mvp.urls`` alone rebinds
    ``mvp.urls.urlpatterns`` but leaves any resolver that already read the
    old list stale, so ``module`` — the test module that built its own
    urlconf by calling ``include("mvp.urls")`` at import time, the way
    ``tests/test_urls.py`` and ``tests/test_views/test_account.py`` both do
    — is reloaded too, rebuilding it with a resolver whose cached property
    has not been read yet. ``clear_url_caches()`` drops ``get_resolver()``'s
    cache, which is keyed by urlconf identity.
    """
    importlib.reload(mvp_urls)
    importlib.reload(module)
    clear_url_caches()


@pytest.fixture
def allauth_installed(request):
    """Installs allauth's account application for the duration of one test
    (T011, T012, T013, T015).

    R11: ``override_settings.enable()`` populates the app registry from
    ``INSTALLED_APPS`` before any other overridden setting takes effect, and
    allauth's ``AccountConfig.ready()`` requires ``AccountMiddleware`` in
    ``MIDDLEWARE`` at that moment — so the two overrides are applied nested,
    ``MIDDLEWARE`` outside, already in place when ``INSTALLED_APPS`` triggers
    the check.

    Reloads ``request.module`` — the requesting test's own module — rather
    than a name fixed at definition time, so the same fixture rebuilds
    whichever module-level urlconf the calling test file built (D17).
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
    _reload_urlconfs(request.module)
    try:
        yield
    finally:
        installed_apps.disable()
        middleware.disable()
        _reload_urlconfs(request.module)


PWA_URLCONF_MODULES = (
    "demo.urls",
    "tests.urls_pwa",
    "tests.urls_shell_pwa",
)


def reload_pwa_urlconfs(request_module):
    """Rebuild ``mvp.urls`` and every URLconf that includes it, so the manifest
    and worker routes follow ``MVP_CONFIG["pwa"]`` as it now stands.

    ``mvp.urls`` reads the setting once, at import. Each module below built a
    resolver from the old ``urlpatterns``, so each is reloaded, in dependency
    order, before Django's resolver cache is cleared.
    """
    importlib.reload(mvp_urls)
    for name in PWA_URLCONF_MODULES:
        importlib.reload(importlib.import_module(name))
    importlib.reload(request_module)
    clear_url_caches()


@pytest.fixture
def pwa_enabled(request):
    """Turn the installable app on for one test, routes included.

    Sets ``MVP_CONFIG["pwa"]`` to a colour, reloads the URLconfs that mount
    ``mvp.urls``, and on teardown undoes the setting first and reloads them
    again so no later test sees the routes.
    """
    patch = pytest.MonkeyPatch()
    patch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})
    reload_pwa_urlconfs(request.module)
    try:
        yield
    finally:
        patch.undo()
        reload_pwa_urlconfs(request.module)


@pytest.fixture
def testapp_account_entries():
    """Apply the Account Center fixture app's entries to ``AccountCenterMenu``
    for the duration of one test, then detach them (ARC-001).

    Yields a ``{name: MenuItem}`` dict for lookup by name. See
    ``tests/testapp_account/menus.py`` for what each entry proves.
    """
    entries = build_entries()
    AccountCenterMenu.extend(entries)
    try:
        yield {entry.name: entry for entry in entries}
    finally:
        for entry in entries:
            entry.parent = None


@pytest.fixture
def card_with_menu_entries():
    """Apply ``tests.testapp_card_with_menu``'s entry to ``AccountCenterMenu``
    for one test, then detach it (ARC-001) — the same pattern as
    ``testapp_account_entries``, for the card fixture (US-3, T021/T024) that
    proves a menu entry alongside a card doesn't disturb either.
    """
    entries = build_card_with_menu_entries()
    AccountCenterMenu.extend(entries)
    try:
        yield {entry.name: entry for entry in entries}
    finally:
        for entry in entries:
            entry.parent = None


# ---------------------------------------------------------------------------
# Model fixtures — thin wrappers over the factories in tests/factories.py.
# A one-off variation needs no fixture here: call the factory inline in the
# test, e.g. ProductFactory(category=None).
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    """A single Category for FK relationships."""
    return CategoryFactory()


@pytest.fixture
def product(db):
    """A Product linked to its own category."""
    return ProductFactory()


@pytest.fixture
def article(db):
    """An Article instance for detail/list view tests."""
    return ArticleFactory()


# ---------------------------------------------------------------------------
# View factory helpers (replace inline type() stub creation)
# ---------------------------------------------------------------------------


def make_stub_view(mixin_class, extra_attrs=None, kwargs=None, user=None):
    """Build a concrete mixin + TemplateView stub with a fake GET request.

    Replaces the common pattern of:
        view_cls = type("StubView", (Mixin, TemplateView), attrs)
        view = view_cls()
        view.request = request; view.kwargs = {}; view.args = []

    Parameters
    ----------
    mixin_class : type
        The mixin to compose with TemplateView.
    extra_attrs : dict, optional
        Additional class-level attributes merged into the stub.
    kwargs : dict, optional
        URL kwargs passed to the view instance.
    user : User, optional
        Request user; defaults to anonymous User().

    Returns
    -------
    view instance with request, kwargs, and args set.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"template_name": "base.html", **(extra_attrs or {})}
    view_cls = type("StubView", (mixin_class, TemplateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = kwargs or {}
    view.args = []
    return view


def _browser_is_installed():
    """True when Playwright is importable *and* its browser is downloaded.

    Testing the import alone is not enough. Installing the package is one
    step and downloading the browser is another, so a CI runner that has the
    dependency but has never run ``playwright install`` errors at launch
    instead of skipping. That gap is why the end-to-end formset tests had
    never run anywhere (specs/024-formset-pages/decisions.md D42).
    """
    if importlib.util.find_spec("playwright") is None:
        return False

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


def _should_skip_browser_tests(has_browser, env):
    """Decide whether browser-marked tests skip, given the browser and the environment.

    Locally a missing browser is ordinary: a contributor who has not run
    ``playwright install`` should see skips, not a wall of errors.

    In CI it is a failure. ``.github/workflows/tests.yml`` passes
    ``install-playwright: true``, so a browser is always expected there, and
    skipping would hide exactly the thing this guard exists to surface —
    nineteen silent skips reading as nineteen passes (issue #171).
    """
    if has_browser:
        return False
    return env.get("CI", "").lower() not in {"1", "true"}


HAS_BROWSER = _browser_is_installed()

requires_browser = pytest.mark.skipif(
    _should_skip_browser_tests(HAS_BROWSER, os.environ),
    reason="playwright browser not installed (run: playwright install chromium)",
)
