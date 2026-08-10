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


def _browser_cache_root() -> Path:
    """Where Playwright downloads browsers, honouring ``PLAYWRIGHT_BROWSERS_PATH``.

    Mirrors Playwright's own resolution: an explicit override if set, else
    its default per-user cache directory.
    """
    override = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    return Path(override) if override else Path.home() / ".cache" / "ms-playwright"


def _browsers_were_attempted() -> bool:
    """True when something has already tried to install Playwright's browsers
    in this environment.

    ``playwright install`` creates its cache root as the very first thing it
    does, before any download completes — verified directly: 2 seconds into
    a 184 MiB chromium download, the directory and its lock file already
    existed. So a CI job that ran the install step leaves this directory
    behind even when the install later failed or left the wrong browser
    version cached, which is exactly the case that should be loud rather
    than silently skipped.
    """
    return _browser_cache_root().exists()


def _should_skip_browser_tests(
    *, has_browser: bool, in_ci: bool, browsers_attempted: bool
) -> bool:
    """True when browser/e2e tests should be skipped rather than run.

    Skips whenever the browser is present — nothing to decide there — and
    otherwise skips unless CI has actually tried to get one. That's the
    fix for keying this on bare ``CI=true``: GitHub Actions sets that on
    every job unconditionally, before the workflow's own
    ``install-playwright`` step has had a chance to run, so a naive
    CI-only check fails loudly even when nobody asked for a browser (today's
    workflow default: ``install-playwright: false``). Once CI has attempted
    an install and the browser still isn't there, that is left unskipped and
    fails loudly against Playwright's own launch error instead of a silent
    skip — the actual defect #171 reports.
    """
    if has_browser:
        return False
    return not (in_ci and browsers_attempted)


HAS_BROWSER = _browser_is_installed()
IN_CI = os.environ.get("CI", "").lower() == "true"
BROWSERS_ATTEMPTED = _browsers_were_attempted()

requires_browser = pytest.mark.skipif(
    _should_skip_browser_tests(
        has_browser=HAS_BROWSER, in_ci=IN_CI, browsers_attempted=BROWSERS_ATTEMPTED
    ),
    reason=(
        "playwright browser not installed (run: playwright install chromium; "
        "in CI, set install-playwright: true in tests.yml)"
    ),
)
