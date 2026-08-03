"""Shared test fixtures for django-mvp test suite.

Standardized per Phase 2: all model fixtures and view factory helpers live here
so individual test files stay focused on assertions, not setup boilerplate.
"""

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
