"""Shared test fixtures for django-mvp test suite.

Standardized per Phase 2: all model fixtures and view factory helpers live here
so individual test files stay focused on assertions, not setup boilerplate.
"""

import importlib.util
import os
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.views.generic import TemplateView

from tests.factories import ArticleFactory, CategoryFactory, ProductFactory

User = get_user_model()


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
