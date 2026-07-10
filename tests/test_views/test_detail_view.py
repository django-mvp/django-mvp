"""Tests for PageObjectMixin and MVPDetailView — US1, US2, US3.

Each test class is tagged with [USn] in its docstring to identify the user story it covers.
Run individual stories with: pytest -k US1, -k US2, -k US3, etc.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.views.generic import TemplateView

from demo.models import Article, Product
from mvp.views.detail import MVPDetailView, PageObjectMixin

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_page_object_view(extra_attrs=None, user=None):
    """Return a configured PageObjectMixin stub with a fake GET request.

    Creates a throwaway concrete subclass of PageObjectMixin + TemplateView
    so Django's MRO works without requiring a real URL dispatch cycle.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"model": Product, **(extra_attrs or {})}
    view_cls = type("StubPageView", (PageObjectMixin, TemplateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    return view


def make_detail_view(model, obj, extra_attrs=None, user=None):
    """Return a configured MVPDetailView instance with the object pre-set.

    Sets ``view.object`` directly so tests can exercise view methods without
    dispatching through the full URL cycle.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"model": model, **(extra_attrs or {})}
    view_cls = type("StubDetailView", (MVPDetailView,), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {"pk": obj.pk}
    view.args = []
    view.object = obj
    return view


# ---------------------------------------------------------------------------
# TestPageObjectMixin — US1
# ---------------------------------------------------------------------------


class TestPageObjectMixin:
    """[US1] Unit tests for PageObjectMixin — shared composition base.

    Verifies that model resolution, sibling URL directory, and breadcrumb/page-class
    concerns are correctly assembled and independently testable without a database.
    """

    def test_context_contains_page_and_directory_with_list_permission(self):
        """[US1] Given has_list_permission=True and directory=['list'], context has 'page' and 'directory['list_url']'."""
        view = make_page_object_view(extra_attrs={"directory": ["list"], "has_list_permission": True})
        ctx = view.get_context_data()
        assert "page" in ctx
        assert "list_url" in ctx["directory"]

    def test_breadcrumb_text_defaults_to_verbose_name_plural(self):
        """[US1] First breadcrumb text equals verbose_name_plural.title() when list_view_title is unset."""
        view = make_page_object_view()
        expected = view.model_meta.verbose_name_plural.title()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == expected

    def test_breadcrumb_text_uses_list_view_title_when_set(self):
        """[US1] First breadcrumb text equals list_view_title when explicitly set."""
        view = make_page_object_view(extra_attrs={"list_view_title": "All Orders"})
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "All Orders"


# ---------------------------------------------------------------------------
# TestMVPDetailView — US2
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDetailView:
    """[US2] Unit tests for MVPDetailView zero-configuration read-only behaviour.

    Verifies that page title, effective CSS classes, breadcrumb trail, and template
    fallback order are all correct without any subclass override.
    """

    def test_page_title_equals_str_of_object(self, product):
        """[US2] get_page_title() returns str(product) — SC-003 model 1."""
        view = make_detail_view(Product, product)
        assert view.get_page_title() == str(product)

    def test_page_title_equals_str_of_article(self, article):
        """[US2] get_page_title() returns str(article) — SC-003 model 2."""
        view = make_detail_view(Article, article)
        assert view.get_page_title() == str(article)

    def test_page_title_handles_unicode_str(self, category):
        """[US2] get_page_title() returns a unicode product name without corruption — US4 AC-2."""
        unicode_product = Product.objects.create(
            name="Ünïcödé Prödüct",
            slug="unicode-product-detail",
            category=category,
            description="A unicode test product",
            price="9.99",
            stock=1,
        )
        view = make_detail_view(Product, unicode_product)
        assert view.get_page_title() == "Ünïcödé Prödüct"

    def test_page_class_contains_model_name_and_action_class(self, product):
        """[US2] get_page_class() output contains both 'product-page' and 'mvp-detail-page'."""
        view = make_detail_view(Product, product)
        page_class = view.get_page_class()
        assert "product-page" in page_class
        assert "mvp-detail-page" in page_class

    def test_breadcrumbs_are_list_link_then_object_name(self, product):
        """[US2] Given has_list_permission=True, breadcrumbs are [list_link, object_name]."""
        view = make_detail_view(
            Product,
            product,
            extra_attrs={"directory": ["list"], "has_list_permission": True},
        )
        breadcrumbs = view.get_breadcrumbs()
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["href"]
        assert breadcrumbs[1]["text"] == str(product)

    def test_template_names_include_app_specific_then_fallback(self, product):
        """[US2] get_template_names() returns ['demo/product_detail.html', 'detail_view.html']."""
        view = make_detail_view(Product, product)
        names = view.get_template_names()
        assert names[0] == "demo/product_detail.html"
        assert names[-1] == "detail_view.html"


# ---------------------------------------------------------------------------
# TestListViewTitle — US3
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListViewTitle:
    """[US3] Unit tests for the list_view_title attribute customisation.

    Verifies that setting list_view_title controls breadcrumb back-link text via a
    single class attribute with no method override required.
    """

    def test_custom_list_view_title_appears_in_breadcrumb(self, product):
        """[US3] First breadcrumb text is list_view_title when set."""
        view = make_detail_view(
            Product,
            product,
            extra_attrs={"list_view_title": "Active Orders"},
        )
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "Active Orders"

    def test_default_breadcrumb_text_is_verbose_name_plural_title_cased(self, product):
        """[US3] First breadcrumb text equals verbose_name_plural.title() when list_view_title is unset."""
        view = make_detail_view(Product, product)
        expected = Product._meta.verbose_name_plural.title()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == expected

    def test_custom_title_present_even_when_permission_false(self, product):
        """[US3] Given list_view_title='Active Orders' and has_list_permission=False, first breadcrumb has that text with empty href."""
        view = make_detail_view(
            Product,
            product,
            extra_attrs={
                "list_view_title": "Active Orders",
                "directory": ["list"],
                "has_list_permission": False,
            },
        )
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "Active Orders"
        assert breadcrumbs[0]["href"] == ""
