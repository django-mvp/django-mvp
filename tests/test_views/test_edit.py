"""Tests for NextURLMixin and the form view redirect priority chain.

Covers all five user stories defined in specs/008-safe-post-submit-redirect/:

  US1 — Chain Form Views with a URL Destination
  US2 — Redirected Back to the Right Place
  US3 — CRUD Action Shorthand Destinations
  US4 — Open-Redirect Protection (logging + rejection)
  US5 — Graceful Fallback (success_url → resoluve_crud_url("list"))

Source: mvp/views/edit.py
"""

import logging
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup
from django import forms as django_forms
from django.contrib.auth import get_user_model
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models.deletion import Collector
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from demo.forms import ContactForm, ProductForm
from demo.models import (
    Category,
    OrderLine,
    Product,
    Project,
    ProjectNote,
    ProjectTask,
)
from mvp.forms import DeleteConfirmForm
from mvp.views.edit import (
    MVPCreateView,
    MVPDeleteView,
    MVPFormView,
    MVPUpdateView,
    NextURLMixin,
)
from tests.conftest import requires_browser
from tests.factories import (
    OrderLineFactory,
    ProductFactory,
    ProjectFactory,
    ProjectNoteFactory,
    ProjectTaskFactory,
)

User = get_user_model()


EDIT_VIEW_LOGGER = "mvp.views.edit"


def make_next_url_view(method="GET", params=None, extra_attrs=None):
    """Return a configured NextURLMixin stub with a fake request.

    Creates a throwaway concrete subclass of NextURLMixin + TemplateView so
    Django's ContextMixin chain is complete. ``params`` are query-string data
    for GET requests and POST-body data for POST requests.
    """
    rf = RequestFactory()
    request = (
        rf.post("/", data=params or {})
        if method == "POST"
        else rf.get("/", data=params or {})
    )

    attrs = {"template_name": "base.html", **(extra_attrs or {})}
    view_cls = type("StubNextURLView", (NextURLMixin, TemplateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    return view


def make_create_view(method="POST", params=None, extra_attrs=None, kwargs=None):
    """Return a configured MVPCreateView stub with a fake request.

    Uses a concrete subclass with Product model and full CRUD permissions so
    shorthand resolution can proceed end-to-end during unit tests.
    """
    rf = RequestFactory()
    request = (
        rf.post("/", data=params or {})
        if method == "POST"
        else rf.get("/", data=params or {})
    )
    request.user = User()

    attrs = {
        "model": Product,
        "fields": ["name"],
        "template_name": "form_view.html",
        "show_list_action": True,
        "show_detail_action": True,
        "show_create_action": True,
        "show_update_action": True,
        "show_delete_action": True,
        **(extra_attrs or {}),
    }
    view_cls = type("StubCreateView", (MVPCreateView,), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = kwargs or {}
    view.args = []
    view.object = None
    return view


def make_update_view(extra_attrs=None):
    """Return a configured MVPUpdateView stub with a fake POST request.

    Used as the test vehicle for MVPModelFormBase behaviour tests so they
    remain decoupled from MVPCreateView-specific overrides.
    """
    rf = RequestFactory()
    request = rf.post("/", data={})
    request.user = User()
    attrs = {
        "model": Product,
        "fields": ["name"],
        "template_name": "form_view.html",
        "show_list_action": True,
        "show_detail_action": True,
        "show_create_action": True,
        "show_update_action": True,
        "show_delete_action": True,
        **(extra_attrs or {}),
    }
    view_cls = type("StubUpdateView", (MVPUpdateView,), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    view.object = None
    return view


class TestUS1GetNextUrl:
    def test_get_request_safe_path_returned(self):
        view = make_next_url_view(method="GET", params={"next": "/safe/path/"})
        assert view.get_next_url() == "/safe/path/"

    def test_post_request_safe_path_returned(self):
        view = make_next_url_view(method="POST", params={"next": "/safe/path/"})
        assert view.get_next_url() == "/safe/path/"

    def test_post_data_takes_precedence_over_query_string(self):
        rf = RequestFactory()
        request = rf.post("/?next=/from-get/", data={"next": "/from-post/"})
        view_cls = type(
            "StubView", (NextURLMixin, TemplateView), {"template_name": "base.html"}
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        assert view.get_next_url() == "/from-post/"

    def test_absent_next_returns_none(self):
        view = make_next_url_view(method="GET", params={})
        result = view.get_next_url()
        assert result is None

    def test_empty_next_returns_none(self):
        view = make_next_url_view(method="GET", params={"next": ""})
        assert view.get_next_url() is None

    @override_settings(DEBUG=True)
    def test_external_url_returns_none(self):
        view = make_next_url_view(method="POST", params={"next": "https://evil.com/"})
        assert view.get_next_url() is None


class TestUS1ContextData:
    def test_get_with_next_injects_next_url(self):
        view = make_next_url_view(method="GET", params={"next": "/records/"})
        context = view.get_context_data()
        assert context["next_url"] == "/records/"

    def test_absent_next_injects_none(self):
        view = make_next_url_view(method="GET", params={})
        context = view.get_context_data()
        assert context["next_url"] is None

    def test_empty_next_injects_none(self):
        view = make_next_url_view(method="GET", params={"next": ""})
        context = view.get_context_data()
        assert context["next_url"] is None


class TestGetNextCandidate:
    def test_post_returns_post_value(self):
        view = make_next_url_view(method="POST", params={"next": "foo"})
        assert view.get_next_candidate() == "foo"

    def test_get_returns_query_string_value(self):
        view = make_next_url_view(method="GET", params={"next": "bar"})
        assert view.get_next_candidate() == "bar"

    def test_absent_next_returns_none(self):
        view = make_next_url_view(method="GET", params={})
        assert view.get_next_candidate() is None

    def test_post_falls_back_to_default_next_when_next_absent(self):
        view = make_next_url_view(method="POST", params={"default_next": "list"})
        assert view.get_next_candidate() == "list"

    def test_post_explicit_next_wins_over_default_next(self):
        view = make_next_url_view(
            method="POST", params={"next": "/orders/", "default_next": "list"}
        )
        assert view.get_next_candidate() == "/orders/"

    def test_post_reads_body_not_query_string(self):
        rf = RequestFactory()
        request = rf.post("/?next=/from-qs/", data={"next": "/from-body/"})
        view_cls = type(
            "StubView", (NextURLMixin, TemplateView), {"template_name": "base.html"}
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        assert view.get_next_candidate() == "/from-body/"


class TestGetNextCandidateOverride:
    def test_get_next_url_uses_overridden_candidate(self):
        view = make_next_url_view(method="GET", params={"next": "/from-request/"})
        view.__class__ = type(
            "OverriddenView",
            (view.__class__,),
            {"get_next_candidate": lambda self: "/overridden/"},
        )
        assert view.get_next_url() == "/overridden/"

    def test_get_context_data_uses_overridden_candidate(self):
        view = make_next_url_view(method="GET", params={"next": "/from-request/"})
        view.__class__ = type(
            "OverriddenView",
            (view.__class__,),
            {"get_next_candidate": lambda self: "/overridden/"},
        )
        assert view.get_context_data()["next_url"] == "/overridden/"


@pytest.mark.django_db
class TestUS3ShorthandSuccessUrl:
    @pytest.fixture(autouse=True)
    def _product(self, db):
        cat = Category.objects.create(name="Cat", slug="cat-us3")
        self.product = Product.objects.create(
            name="Test US3",
            slug="test-us3",
            category=cat,
            description="desc",
            price="1.00",
            sku="US3-001",
        )

    def test_next_list_redirects_to_list_url(self):
        view = make_create_view(method="POST", params={"next": "list"})
        view.object = self.product
        url = view.get_success_url()
        from django.urls import reverse

        assert url == reverse("product-list")

    def test_next_detail_redirects_to_detail_url(self):
        view = make_create_view(
            method="POST",
            params={"next": "detail"},
            kwargs={"pk": self.product.pk},
        )
        view.object = self.product
        url = view.get_success_url()
        from django.urls import reverse

        assert url == reverse("product-detail", kwargs={"pk": self.product.pk})

    def test_next_update_redirects_to_update_url(self):
        view = make_create_view(
            method="POST",
            params={"next": "update"},
            kwargs={"pk": self.product.pk},
        )
        view.object = self.product
        url = view.get_success_url()
        from django.urls import reverse

        assert url == reverse("product-update", kwargs={"pk": self.product.pk})

    def test_unrecognised_shorthand_falls_through_to_object_url(self):
        view = make_create_view(method="POST", params={"next": "foobar"})
        view.object = self.product
        url = view.get_success_url()

        # Falls through to object.get_absolute_url() since no success_url is set
        assert url == self.product.get_absolute_url()

    def test_form_view_skips_shorthand_silently(self):

        rf = RequestFactory()
        request = rf.post("/", data={"next": "list"})
        request.user = User()
        view_cls = type(
            "StubFormView",
            (MVPFormView,),
            {
                "template_name": "form_view.html",
                "success_url": "/done/",
            },
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        url = view.get_success_url()
        assert url == "/done/"


class TestUS3ShorthandContext:
    def test_post_shorthand_resolves_in_context(self):
        from django.urls import reverse

        view = make_create_view(method="POST", params={"next": "list"})
        context = view.get_context_data()
        assert context["next_url"] == reverse("product-list")

    def test_get_shorthand_unresolvable_without_pk(self):
        view = make_create_view(method="GET", params={"next": "detail"})
        context = view.get_context_data()
        assert context["next_url"] is None


@pytest.mark.django_db
class TestUS3DeleteViewNoRegression:
    def test_delete_view_post_redirects_to_list(self, client):
        from django.urls import reverse

        cat = Category.objects.create(name="Cat Del", slug="cat-del-us3")
        product = Product.objects.create(
            name="Del US3",
            slug="del-us3",
            category=cat,
            description="d",
            price="1.00",
            sku="DEL-US3-001",
        )
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")


@pytest.mark.django_db
class TestUS5FallbackChain:
    @pytest.fixture(autouse=True)
    def _product(self, db):
        cat = Category.objects.create(name="Cat US5", slug="cat-us5")
        self.product = Product.objects.create(
            name="Test US5",
            slug="test-us5",
            category=cat,
            description="desc",
            price="1.00",
            sku="US5-001",
        )

    def test_no_next_with_success_url_returns_success_url(self):
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"success_url": "/done/"},
        )
        view.object = self.product
        assert view.get_success_url() == "/done/"

    def test_no_next_no_success_url_falls_back_to_object_url(self):
        view = make_create_view(method="POST", params={})
        view.object = self.product
        assert view.get_success_url() == self.product.get_absolute_url()

    @override_settings(DEBUG=True)
    def test_rejected_next_falls_through_to_success_url(self, caplog):
        view = make_create_view(
            method="POST",
            params={"next": "https://evil.com/"},
            extra_attrs={"success_url": "/done/"},
        )
        view.object = self.product
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            url = view.get_success_url()
        assert url == "/done/"

    def test_empty_next_with_success_url_returns_success_url(self):
        view = make_create_view(
            method="POST",
            params={"next": ""},
            extra_attrs={"success_url": "/done/"},
        )
        view.object = self.product
        assert view.get_success_url() == "/done/"

    def test_form_view_no_next_with_success_url(self):
        rf = RequestFactory()
        request = rf.post("/", data={})
        request.user = User()
        view_cls = type(
            "StubFormView",
            (MVPFormView,),
            {
                "template_name": "form_view.html",
                "success_url": "/done/",
            },
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        assert view.get_success_url() == "/done/"


class TestMVPFormBase:
    def test_base_template_name(self):
        from mvp.views.edit import MVPFormBase

        assert MVPFormBase.base_template_name == "form_view.html"

    def test_page_class(self):
        from mvp.views.edit import MVPFormBase

        assert MVPFormBase.page_class == "mvp-form-page"

    def test_get_success_url_raises_improperly_configured(self):
        from django.core.exceptions import ImproperlyConfigured

        rf = RequestFactory()
        request = rf.post("/", data={})
        request.user = User()
        view_cls = type(
            "StubFormView",
            (MVPFormView,),
            {"template_name": "form_view.html"},
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []

        with pytest.raises(ImproperlyConfigured):
            view.get_success_url()


class TestMVPModelFormBaseSuccessMessage:
    def test_verbose_name_only_resolves(self):
        view = make_update_view(
            extra_attrs={"success_message": "%(verbose_name)s created."}
        )
        result = view.get_success_message({})
        assert result == f"{Product._meta.verbose_name} created."

    def test_missing_field_placeholder_substitutes_empty_string(self):
        view = make_update_view(
            extra_attrs={"success_message": "%(verbose_name)s %(name)s deleted."}
        )
        result = view.get_success_message({})
        assert result == f"{Product._meta.verbose_name}  deleted."

    def test_field_value_and_verbose_name_both_resolve(self):
        view = make_update_view(
            extra_attrs={"success_message": "%(verbose_name)s %(name)s updated."}
        )
        result = view.get_success_message({"name": "Widget A"})
        assert result == f"{Product._meta.verbose_name} Widget A updated."


class TestMVPModelFormBase:
    def test_get_success_url_raises_when_list_url_unresolvable(self):
        from django.core.exceptions import ImproperlyConfigured

        # show_list_action=False → resolve_crud_url("list") returns None; object=None → ImproperlyConfigured
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"show_list_action": False},
        )
        view.object = None

        with pytest.raises(ImproperlyConfigured):
            view.get_success_url()

    def test_success_url_shorthand_resolves_to_crud_url(self):
        from django.urls import reverse

        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"success_url": "list"},
        )
        view.object = None

        result = view.get_success_url()
        assert result == reverse("product-list")

    def test_no_success_url_falls_back_to_object_get_absolute_url(self):

        class _MockObj:
            def get_absolute_url(self):
                return "/products/42/"

        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"show_list_action": False},
        )
        view.object = _MockObj()

        result = view.get_success_url()
        assert result == "/products/42/"

    def test_no_success_url_no_get_absolute_url_raises(self):
        from django.core.exceptions import ImproperlyConfigured

        class _NoURL:
            pass

        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"show_list_action": False},
        )
        view.object = _NoURL()

        with pytest.raises(ImproperlyConfigured):
            view.get_success_url()


def make_form_view(extra_attrs=None):
    """Return a configured MVPFormView stub with a fake POST request."""
    rf = RequestFactory()
    request = rf.post("/", data={})
    request.user = User()
    attrs = {
        "template_name": "form_view.html",
        "success_url": "/done/",
        **(extra_attrs or {}),
    }
    view_cls = type("StubFormView", (MVPFormView,), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    return view


class TestMVPFormView:
    def test_field_placeholder_substituted_from_cleaned_data(self):
        view = make_form_view(extra_attrs={"success_message": "Thanks, %(email)s!"})
        result = view.get_success_message({"email": "user@example.com"})
        assert result == "Thanks, user@example.com!"

    def test_unknown_placeholder_substitutes_empty_string(self):
        view = make_form_view(extra_attrs={"success_message": "Hello %(foo)s!"})
        result = view.get_success_message({})
        assert result == "Hello !"

    def test_verbose_name_not_injected_substitutes_empty_string(self):
        view = make_form_view(
            extra_attrs={"success_message": "%(verbose_name)s saved."}
        )
        result = view.get_success_message({})
        assert result == " saved."

    def test_default_title_derived_from_class_name(self):
        rf = RequestFactory()
        request = rf.get("/")
        request.user = User()
        view_cls = type(
            "ContactFormView",
            (MVPFormView,),
            {"template_name": "form_view.html", "success_url": "/done/"},
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        assert view.get_page_title() == "Contact Form View"

    def test_explicit_page_title_returned_as_is(self):
        view = make_form_view(extra_attrs={"page_title": "My Form"})
        assert view.get_page_title() == "My Form"


class TestMVPCreateViewDefaults:
    def test_page_class_contains_create(self):
        assert "mvp-create-page" in MVPCreateView.page_class

    def test_page_title_class_attr_is_template(self):
        assert "page_title" in MVPCreateView.__dict__
        assert "%(verbose_name)s" in str(MVPCreateView.page_title)


class TestMVPCreateViewPageTitle:
    def test_default_title_single_word_verbose_name(self):
        view = make_create_view()
        assert view.get_page_title() == "Create Product"

    def test_default_title_multi_word_verbose_name(self):
        rf = RequestFactory()
        request = rf.get("/")
        request.user = User()
        attrs = {
            "model": OrderLine,
            "fields": ["quantity"],
            "template_name": "form_view.html",
            "show_list_action": False,
            "show_detail_action": False,
            "show_create_action": True,
            "show_update_action": False,
            "show_delete_action": False,
        }
        view_cls = type("StubOrderLineCreateView", (MVPCreateView,), attrs)
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        view.object = None
        assert view.get_page_title() == "Create Order Line"

    def test_explicit_page_title_returned(self):
        view = make_create_view(extra_attrs={"page_title": "Add a new product"})
        assert view.get_page_title() == "Add a new product"

    def test_empty_string_page_title_returns_empty(self):
        view = make_create_view(extra_attrs={"page_title": ""})
        assert view.get_page_title() == ""

    def test_lazy_string_page_title_returned(self):
        view = make_create_view(extra_attrs={"page_title": _("Add Product")})
        assert view.get_page_title() == "Add Product"


class TestMVPCreateViewSuccessMessage:
    def test_default_message_uses_title_cased_verbose_name(self):
        view = make_create_view()
        result = view.get_success_message({})
        assert result == "Product successfully created."

    def test_custom_message_with_field_interpolation(self):
        view = make_create_view(extra_attrs={"success_message": "%(name)s was added."})
        result = view.get_success_message({"name": "Widget"})
        assert result == "Widget was added."

    def test_missing_key_substitutes_empty_string(self):
        view = make_create_view(
            extra_attrs={"success_message": "%(verbose_name)s %(missing)s done."}
        )
        result = view.get_success_message({})
        assert result == "Product  done."


class TestMVPCreateViewOverrides:
    def test_page_class_overridable(self):
        view = make_create_view(extra_attrs={"page_class": "custom-class"})
        assert "custom-class" in view.get_page_class()


class TestMVPCreateViewBreadcrumb:
    def test_breadcrumb_has_two_items(self):
        view = make_create_view()
        assert len(view.get_breadcrumbs()) == 2

    def test_first_item_has_no_href_when_list_permission_false(self):
        view = make_create_view(extra_attrs={"show_list_action": False})
        breadcrumbs = view.get_breadcrumbs()
        assert not breadcrumbs[0].get("href")

    def test_first_item_has_href_when_list_permission_true(self):
        from django.urls import reverse

        view = make_create_view()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["href"] == reverse("product-list")

    def test_second_item_has_no_href(self):
        view = make_create_view()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[1].get("href") is None

    def test_second_item_text_matches_page_title(self):
        view = make_create_view()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[1]["text"] == view.get_page_title()
        assert breadcrumbs[1]["text"] == "Create Product"

    def test_get_breadcrumbs_override_is_respected(self):
        custom_crumbs = [{"text": "Home", "href": "/"}, {"text": "New"}]
        view = make_create_view(
            extra_attrs={"get_breadcrumbs": lambda self: custom_crumbs}
        )
        assert view.get_breadcrumbs() == custom_crumbs


class TestMVPUpdateViewDefaults:
    def test_page_class_contains_update(self):
        assert "mvp-update-page" in MVPUpdateView.page_class

    def test_page_title_class_attr_is_template(self):
        assert "page_title" in MVPUpdateView.__dict__
        assert "%(verbose_name)s" in str(MVPUpdateView.page_title)


class TestMVPUpdateViewPageTitle:
    def test_default_title_single_word_verbose_name(self):
        view = make_update_view()
        assert view.get_page_title() == "Update Product"

    def test_default_title_multi_word_verbose_name(self):
        rf = RequestFactory()
        request = rf.post("/", data={})
        request.user = User()
        attrs = {
            "model": OrderLine,
            "fields": ["quantity"],
            "template_name": "form_view.html",
            "show_list_action": False,
            "show_detail_action": False,
            "show_create_action": False,
            "show_update_action": True,
            "show_delete_action": False,
        }
        view_cls = type("StubOrderLineUpdateView", (MVPUpdateView,), attrs)
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        view.object = None
        assert view.get_page_title() == "Update Order Line"

    def test_explicit_page_title_returned(self):
        view = make_update_view(extra_attrs={"page_title": "Edit product details"})
        assert view.get_page_title() == "Edit product details"

    def test_empty_string_page_title_returns_empty(self):
        view = make_update_view(extra_attrs={"page_title": ""})
        assert view.get_page_title() == ""


class TestMVPUpdateViewBreadcrumb:
    @pytest.fixture(autouse=True)
    def _stub_object(self):

        class _Obj:
            pk = 1

            def __str__(self):
                return "Test Product"

            def get_absolute_url(self):
                return "/products/1/"

        self._obj = _Obj()

    def _view_with_object(self, extra_attrs=None):
        view = make_update_view(extra_attrs=extra_attrs)
        view.kwargs = {"pk": 1}
        view.object = self._obj
        return view

    def test_breadcrumb_has_three_items(self):
        view = self._view_with_object()
        assert len(view.get_breadcrumbs()) == 3

    def test_second_item_text_is_str_object(self):
        view = self._view_with_object()
        crumbs = view.get_breadcrumbs()
        assert crumbs[1]["text"] == str(self._obj)

    def test_second_item_href_uses_resolve_crud_url_detail(self):
        from django.urls import reverse

        from demo.models import Product as _Product

        rf = RequestFactory()
        request = rf.post("/", data={})
        request.user = User()

        class _RealObj:
            pk = 1

            def __str__(self):
                return "Product 1"

            def get_absolute_url(self):
                return "/old-absolute-url/"

        attrs = {
            "model": _Product,
            "fields": ["name"],
            "template_name": "form_view.html",
            "show_list_action": True,
            "show_detail_action": True,
            "show_create_action": True,
            "show_update_action": True,
            "show_delete_action": True,
        }
        view_cls = type("StubUpdateWithPk", (MVPUpdateView,), attrs)
        view = view_cls()
        view.request = request
        view.kwargs = {"pk": 1}
        view.args = []
        view.object = _RealObj()

        crumbs = view.get_breadcrumbs()
        expected = reverse("product-detail", kwargs={"pk": 1})
        assert crumbs[1]["href"] == expected
        assert crumbs[1]["href"] != "/old-absolute-url/"

    def test_third_item_has_no_href(self):
        view = self._view_with_object()
        crumbs = view.get_breadcrumbs()
        assert crumbs[2].get("href") is None

    def test_third_item_text_matches_page_title(self):
        view = self._view_with_object()
        crumbs = view.get_breadcrumbs()
        assert crumbs[2]["text"] == view.get_page_title()

    # US5 — breadcrumb degrades when list or detail permission is missing
    def test_first_item_has_no_href_when_list_permission_false(self):
        view = self._view_with_object(extra_attrs={"show_list_action": False})
        assert not view.get_breadcrumbs()[0].get("href")

    def test_first_item_has_href_when_list_permission_true(self):
        from django.urls import reverse

        view = self._view_with_object()
        assert view.get_breadcrumbs()[0]["href"] == reverse("product-list")

    def test_second_item_has_no_href_when_detail_permission_false(self):
        view = self._view_with_object(extra_attrs={"show_detail_action": False})
        assert not view.get_breadcrumbs()[1].get("href")

    def test_second_item_has_href_when_detail_permission_true(self):
        view = self._view_with_object()
        assert view.get_breadcrumbs()[1].get("href")


class TestMVPUpdateViewOverrides:
    def test_page_class_overridable(self):
        view = make_update_view(extra_attrs={"page_class": "custom-class"})
        assert "custom-class" in view.get_page_class()

    def test_page_title_overridable(self):
        view = make_update_view(extra_attrs={"page_title": "Edit product details"})
        assert view.get_page_title() == "Edit product details"

    def test_success_message_overridable_with_field_interpolation(self):
        view = make_update_view(extra_attrs={"success_message": "%(name)s was saved."})
        result = view.get_success_message({"name": "Widget"})
        assert result == "Widget was saved."

    def test_get_breadcrumbs_override_is_respected(self):
        custom_crumbs = [
            {"text": "Home", "href": "/"},
            {"text": "Products", "href": "/products/"},
            {"text": "Edit"},
        ]
        view = make_update_view(
            extra_attrs={"get_breadcrumbs": lambda self: custom_crumbs}
        )
        assert view.get_breadcrumbs() == custom_crumbs

    def test_delete_url_can_be_suppressed_via_override(self):
        view = make_update_view(extra_attrs={"show_delete_action": False})
        assert not view.get_delete_url()


class TestMVPUpdateViewDeleteLinkVisibility:
    def test_delete_button_absent_when_delete_url_empty(self):
        view = make_update_view(extra_attrs={"show_delete_action": False})
        view.object = None
        assert not view.get_delete_url()

    def test_delete_button_present_when_delete_url_set(self):

        class _Obj:
            pk = 1

            def __str__(self):
                return "Product 1"

        rf = RequestFactory()
        request = rf.get("/")
        request.user = User()
        attrs = {
            "model": __import__("demo.models", fromlist=["Product"]).Product,
            "fields": ["name"],
            "template_name": "form_view.html",
            "show_list_action": True,
            "show_detail_action": True,
            "show_create_action": True,
            "show_update_action": True,
            "show_delete_action": True,
        }
        view_cls = type("StubUpdateWithPk", (MVPUpdateView,), attrs)
        view = view_cls()
        view.request = request
        view.kwargs = {"pk": 1}
        view.args = []
        view.object = _Obj()
        assert view.get_delete_url()


def _product_post_data(
    category, *, name="Created Product", slug="created-product-integ"
):
    """Return valid POST data for the product create/update form."""
    return {
        "name": name,
        "slug": slug,
        "description": "Integration test description",
        "price": "12.99",
        "stock": "3",
        "category": category.pk,
        "status": "draft",
    }


def _get_form(content, action_substring):
    """Parse ``content`` and return the ``<form>`` whose action contains the substring.

    A rendered mvp page carries more than one ``<form>`` — the language-selector
    form (``action="/i18n/setlang/"``) appears first in the document — so
    selecting by action rather than taking the first match is load-bearing.
    """
    soup = BeautifulSoup(content, "html.parser")
    for form in soup.find_all("form"):
        if action_substring in (form.get("action") or ""):
            return form
    raise AssertionError(
        f"no <form> with action containing {action_substring!r} found in response"
    )


class TestCreateViewRendering:
    @pytest.mark.django_db
    def test_US1_create_page_title_is_model_aware(self, client):
        response = client.get(reverse("product-create"))
        assert b"Create Product" in response.content

    @pytest.mark.django_db
    def test_US1_success_message_is_title_cased(self, client, category):
        from django.contrib.messages import get_messages

        response = client.post(
            reverse("product-create"),
            _product_post_data(
                category, name="Flash Product", slug="flash-product-integ"
            ),
        )
        assert response.status_code == 302
        # Follow redirect and check message appears in content
        response = client.get(response["Location"])
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert "Product successfully created." in messages

    @pytest.mark.django_db
    def test_US1_breadcrumb_links_to_list(self, client):
        response = client.get(reverse("product-create"))
        breadcrumbs = response.context["page"]["breadcrumbs"]
        assert len(breadcrumbs) >= 1
        assert breadcrumbs[0].get("href") == reverse("product-list")


class TestCreateViewRedirects:
    @pytest.mark.django_db
    def test_US2_create_with_url_next_redirects_to_url(self, client, category):
        get_response = client.get(reverse("product-create") + "?next=/orders/")
        form = _get_form(get_response.content, "/products/create/")
        hidden_next = form.find("input", {"type": "hidden", "name": "next"})
        assert hidden_next is not None, "rendered create form has no hidden next input"
        assert hidden_next["value"] == "/orders/"

        data = _product_post_data(
            category, name="Next URL Product", slug="next-url-product-integ"
        )
        data["next"] = hidden_next["value"]
        data["default_next"] = "list"  # the clicked "Save & continue" button
        response = client.post(form["action"], data)
        assert response.status_code == 302
        assert response["Location"] == "/orders/"

    @pytest.mark.django_db
    def test_US2_failed_form_preserves_next_url(self, client, category):
        get_response = client.get(reverse("product-create") + "?next=/orders/")
        form = _get_form(get_response.content, "/products/create/")
        hidden_next = form.find("input", {"type": "hidden", "name": "next"})
        assert hidden_next is not None
        assert hidden_next["value"] == "/orders/"

        response = client.post(form["action"], {"next": hidden_next["value"]})
        assert response.status_code == 200

        form2 = _get_form(response.content, "/products/create/")
        hidden_next2 = form2.find("input", {"type": "hidden", "name": "next"})
        assert hidden_next2 is not None, "next input lost on failed-form re-render"
        assert hidden_next2["value"] == "/orders/"

    @pytest.mark.django_db
    def test_US2_plain_create_with_no_next_still_lands_on_list_by_default(
        self, client, category
    ):
        get_response = client.get(reverse("product-create"))
        form = _get_form(get_response.content, "/products/create/")
        assert form.find("input", {"type": "hidden", "name": "next"}) is None

        data = _product_post_data(
            category, name="Default Redirect Product", slug="default-redirect-integ"
        )
        data["default_next"] = "list"  # the clicked "Save & continue" button
        response = client.post(form["action"], data)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")

    @pytest.mark.django_db
    def test_US3_create_with_list_shorthand_redirects_to_list(self, client, category):
        data = _product_post_data(
            category, name="List Redirect Product", slug="list-redirect-integ"
        )
        data["next"] = "list"
        response = client.post(reverse("product-create"), data)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")

    @pytest.mark.django_db
    def test_US3_create_with_detail_shorthand_redirects_to_detail(
        self, client, category
    ):
        from demo.models import Product

        data = _product_post_data(
            category, name="Detail Redirect Product", slug="detail-redirect-integ"
        )
        data["next"] = "detail"
        response = client.post(reverse("product-create"), data)
        assert response.status_code == 302
        product = Product.objects.get(slug="detail-redirect-integ")
        assert response["Location"] == reverse(
            "product-detail", kwargs={"pk": product.pk}
        )


class TestUpdateViewRendering:
    @pytest.mark.django_db
    def test_US6_update_page_title_is_model_aware(self, client, product):
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        assert b"Update Product" in response.content

    @pytest.mark.django_db
    def test_US6_update_success_message_appears(self, client, product, category):
        from django.contrib.messages import get_messages

        url = reverse("product-update", kwargs={"pk": product.pk})
        data = _product_post_data(
            category, name="Updated Product Name", slug="edit-product-integ"
        )
        response = client.post(url, data)
        assert response.status_code == 302
        response = client.get(response["Location"])
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("successfully updated" in m for m in messages)

    @pytest.mark.django_db
    def test_US6_update_breadcrumb_has_three_items(self, client, product):
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        breadcrumbs = response.context["page"]["breadcrumbs"]
        assert len(breadcrumbs) == 3
        # First two items are links; last item is plain text (current page).
        assert breadcrumbs[0].get("href") is not None, (
            "First breadcrumb must be a link (list)"
        )
        assert breadcrumbs[1].get("href") is not None, (
            "Second breadcrumb must be a link (detail)"
        )
        assert breadcrumbs[2].get("href") is None, (
            "Third breadcrumb must be plain text (no link)"
        )

    @pytest.mark.django_db
    def test_US3_update_delete_link_visible_when_configured(self, client, product):
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "delete" in content, "Delete link must be present on the update page"
        assert "back=" in content, "Delete link must contain ?back= parameter"
        assert "next=" in content, "Delete link must contain next= parameter"

    @pytest.mark.django_db
    def test_US4_update_delete_link_absent_when_not_configured(self, client):
        from demo.models import Category

        cat = Category.objects.create(name="No Delete Cat", slug="no-delete-cat-integ")
        url = reverse("category-update", kwargs={"pk": cat.pk})
        response = client.get(url)
        # CategoryUpdateView has show_delete_action=False → get_delete_url() returns ''.
        content = response.content.decode()
        # No anchor pointing to a delete URL should appear.
        import re

        delete_links = re.findall(r'href="[^"]*delete[^"]*"', content)
        assert delete_links == [], (
            f"Expected no delete link on category update page, but found: {delete_links}"
        )


class TestDeleteConfirmForm:
    def test_form_valid_when_field_provided(self):
        form = DeleteConfirmForm(data={"confirmation": "some-value"})
        assert form.is_valid()

    def test_form_invalid_when_field_empty(self):
        form = DeleteConfirmForm(data={"confirmation": ""})
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_valid_when_confirmation_matches_value(self):
        form = DeleteConfirmForm(
            data={"confirmation": "correct"}, confirmation_value="correct"
        )
        assert form.is_valid()

    def test_form_invalid_when_confirmation_does_not_match(self):
        form = DeleteConfirmForm(
            data={"confirmation": "wrong"}, confirmation_value="correct"
        )
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_invalid_when_confirmation_empty_with_value(self):
        form = DeleteConfirmForm(
            data={"confirmation": ""}, confirmation_value="correct"
        )
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_valid_when_confirmation_value_is_none(self):
        form = DeleteConfirmForm(data={"confirmation": "x"}, confirmation_value=None)
        assert form.is_valid()


@pytest.mark.django_db
class TestMVPDeleteViewBasic:
    def test_get_returns_200(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_context_has_no_related_objects_by_default(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["related_objects"] == []

    def test_context_is_not_protected_by_default(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["is_protected"] is False

    def test_context_require_confirmation_false_by_default(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["require_confirmation"] is False

    def test_page_title_contains_verbose_name(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert "Product" in response.context["page"]["title"]
        assert "Delete" in response.context["page"]["title"]

    def test_breadcrumbs_has_three_items(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert len(response.context["page"]["breadcrumbs"]) == 3

    def test_post_deletes_object(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Product.objects.filter(pk=product.pk).exists()

    def test_post_redirects_to_list_url(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")

    def test_post_shows_success_message(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url, follow=True)
        messages = list(response.context["messages"])
        assert len(messages) == 1

    def test_page_class_contains_mvp_delete_page(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert "mvp-delete-page" in response.context["page"]["class"]


@pytest.mark.django_db
class TestMVPDeleteViewBackUrl:
    def test_back_url_defaults_to_list_when_absent(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["back_url"] == reverse("product-list")

    def test_back_url_reads_from_query_param(self, client, product):
        update_url = reverse("product-update", kwargs={"pk": product.pk})
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url, {"back": update_url})
        assert response.context["back_url"] == update_url

    def test_falls_back_to_the_objects_absolute_url_when_no_list_action(self, product):
        view_cls = type("StubDeleteView", (MVPDeleteView,), {"model": Product})
        view = view_cls()
        view.request = RequestFactory().get("/")
        view.object = product

        assert view.get_back_url() == product.get_absolute_url()

    def test_back_param_still_wins_over_the_objects_absolute_url(self, product):
        other = f"/products/{product.pk}/edit/"
        view_cls = type("StubDeleteView", (MVPDeleteView,), {"model": Product})
        view = view_cls()
        view.request = RequestFactory().get("/", {"back": other})
        view.object = product

        assert view.get_back_url() == other

    def test_off_host_back_param_is_rejected_in_favour_of_the_absolute_url(
        self, product
    ):
        view_cls = type("StubDeleteView", (MVPDeleteView,), {"model": Product})
        view = view_cls()
        view.request = RequestFactory().get("/", {"back": "https://evil.com/"})
        view.object = product

        assert view.get_back_url() == product.get_absolute_url()

    def test_no_back_button_when_object_has_no_absolute_url_and_no_list_action(self):
        order_line = OrderLineFactory()
        view_cls = type("StubDeleteView", (MVPDeleteView,), {"model": OrderLine})
        request = RequestFactory().get("/")

        response = view_cls.as_view()(request, pk=order_line.pk)
        response.render()

        soup = BeautifulSoup(response.content, "html.parser")
        assert soup.find("a", class_="btn-outline") is None

    def test_back_button_still_renders_when_a_list_action_exists(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)

        assert f'href="{reverse("product-list")}"' in response.content.decode()

    def test_back_url_rejects_external_url(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url, {"back": "https://evil.com/"})
        assert response.context["back_url"] == reverse("product-list")

    def test_next_url_is_none_when_absent(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["next_url"] is None

    def test_post_with_external_next_redirects_to_list(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url, data={"next": "https://evil.com/"})
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")

    def test_rendered_form_carries_caller_next_through_real_delete_submit(
        self, client, product
    ):
        delete_url = reverse("product-delete", kwargs={"pk": product.pk})
        get_response = client.get(delete_url + "?next=/orders/")
        form = _get_form(get_response.content, delete_url)
        hidden_next = form.find("input", {"type": "hidden", "name": "next"})
        assert hidden_next is not None, "rendered delete form has no hidden next input"
        assert hidden_next["value"] == "/orders/"

        response = client.post(form["action"], {"next": hidden_next["value"]})
        assert response.status_code == 302
        assert response["Location"] == "/orders/"


@pytest.mark.django_db
class TestMVPDeleteViewRelatedObjects:
    def test_related_objects_hidden_when_flag_off(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["related_objects"] == []

    def test_related_objects_attrs_defaults_to_info_variant(self, client, product):
        url = reverse("product-delete-related", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["related_objects_attrs"] == {"variant": "info"}

    def test_related_objects_shown_when_flag_on(self, client, product):
        url = reverse("product-delete-related", kwargs={"pk": product.pk})
        response = client.get(url)
        assert "related_objects" in response.context
        assert response.context["is_protected"] is False

    def test_related_objects_not_shown_when_protected(self, client, product):
        OrderLine.objects.create(product=product, quantity=2)
        url = reverse("product-delete-related", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["is_protected"] is True
        assert response.context["related_objects"] == []

    def test_related_objects_are_3_tuples(self, client, category):
        # Create products to give the category cascade-deleted children
        for i in range(2):
            Product.objects.create(
                name=f"Product {i}",
                slug=f"product-{i}-cat-del",
                category=category,
                description="Test",
                price="1.00",
                sku=f"SKU-CAT-DEL-{i}",
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        assert isinstance(related, list)
        for item in related:
            assert len(item) == 3, f"Expected 3-tuple, got {len(item)}-tuple: {item}"

    def test_related_objects_capped_at_max_per_group(self, client, category):
        for i in range(5):
            Product.objects.create(
                name=f"Cap Product {i}",
                slug=f"cap-product-{i}",
                category=category,
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        # SET_NULL products don't appear as cascade objects
        assert len(related) == 0

    def test_overflow_count_is_correct(self, client, category):
        for i in range(5):
            Product.objects.create(
                name=f"Overflow Prod {i}",
                slug=f"overflow-prod-{i}",
                category=category,
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        # SET_NULL products don't appear as cascade objects
        assert related == []

    def test_overflow_note_in_html(self, client, category):
        for i in range(5):
            Product.objects.create(
                name=f"Html Overflow {i}",
                slug=f"html-overflow-{i}",
                category=category,
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        assert (
            "and" not in response.content.decode()
            or "more" not in response.content.decode()
        )

    def test_no_overflow_note_when_within_cap(self, client, category):
        for i in range(2):
            Product.objects.create(
                name=f"No Overflow {i}",
                slug=f"no-overflow-{i}",
                category=category,
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        assert related == []

    def test_post_deletes_when_cascade_related_objects_exist(self, client, category):
        product_pk = Product.objects.create(
            name="Cascade Delete Me",
            slug="cascade-del-me",
            category=category,
        ).pk
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Category.objects.filter(pk=category.pk).exists()
        # Product survives — category FK is set to NULL, not cascade-deleted
        assert Product.objects.filter(pk=product_pk).exists()
        assert Product.objects.get(pk=product_pk).category is None


@pytest.mark.django_db
class TestMVPDeleteViewRelatedObjectsPresentation:
    @staticmethod
    def _stub_related_objects(monkeypatch, category):
        from mvp.views.edit import MVPDeleteView

        related_map = {Category: [category]}  # any real model instance will do
        monkeypatch.setattr(
            MVPDeleteView,
            "_collect_deletion_data",
            lambda self: (related_map, []),
        )

    @staticmethod
    def _related_objects_alert(content):
        """Return the <c-alert> whose body contains the related-objects heading.

        The page always carries a separate, hardcoded variant="warning" alert for
        the basic "this is permanent" notice, so asserting on `alert-warning`
        anywhere in the page would pass whether or not this feature works. Locate
        the specific alert this feature controls instead.
        """
        soup = BeautifulSoup(content, "html.parser")
        for alert in soup.select('[role="alert"]'):
            if alert.find("ul"):
                return alert
        raise AssertionError("no related-objects alert (containing a <ul>) found")

    def test_default_attrs_render_info_alert_byte_for_byte(
        self, monkeypatch, client, category
    ):
        self._stub_related_objects(monkeypatch, category)
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        alert = self._related_objects_alert(response.content.decode())
        assert "alert-info" in alert["class"]

    def test_custom_variant_renders_as_configured(self, monkeypatch, client, category):
        self._stub_related_objects(monkeypatch, category)
        url = reverse("category-delete-related-warning", kwargs={"pk": category.pk})
        response = client.get(url)
        alert = self._related_objects_alert(response.content.decode())
        assert "alert-warning" in alert["class"]
        assert "alert-info" not in alert["class"]

    def test_arbitrary_attrs_reach_the_alert(self, monkeypatch, client, category):
        from demo.views import CategoryDeleteWithRelatedView

        self._stub_related_objects(monkeypatch, category)
        monkeypatch.setattr(
            CategoryDeleteWithRelatedView,
            "related_objects_attrs",
            {"variant": "error", "class": "mt-4", "data-testid": "cascade"},
        )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        alert = self._related_objects_alert(response.content.decode())
        assert "alert-error" in alert["class"]
        assert "mt-4" in alert["class"]
        assert alert["data-testid"] == "cascade"

    def test_attrs_are_presentation_only(self, monkeypatch, client, category):
        self._stub_related_objects(monkeypatch, category)
        default_url = reverse("category-delete-related", kwargs={"pk": category.pk})
        warning_url = reverse(
            "category-delete-related-warning", kwargs={"pk": category.pk}
        )
        default_related = client.get(default_url).context["related_objects"]
        warning_related = client.get(warning_url).context["related_objects"]
        assert default_related == warning_related != []


@pytest.mark.django_db
class TestMVPDeleteViewFastDeletedRelatedObjects:
    @staticmethod
    def _view_for(project):
        class ProjectDeleteView(MVPDeleteView):
            model = Project
            show_related_objects = True

        view = ProjectDeleteView()
        view.object = project
        return view

    def test_children_are_actually_on_the_fast_delete_path(self, db):
        project = ProjectFactory()
        ProjectTaskFactory(project=project)
        collector = Collector(using=project._state.db)
        collector.collect([project])
        fast_deleted = {qs.model for qs in collector.fast_deletes}
        assert ProjectTask in fast_deleted
        assert ProjectTask not in collector.data

    def test_fast_deleted_children_appear_in_the_summary(self, db):
        project = ProjectFactory()
        tasks = [ProjectTaskFactory(project=project) for _ in range(2)]
        note = ProjectNoteFactory(project=project)

        related, protected = self._view_for(project)._collect_deletion_data()

        assert protected == []
        assert set(related) == {ProjectTask, ProjectNote}
        assert sorted(o.pk for o in related[ProjectTask]) == sorted(t.pk for t in tasks)
        assert [o.pk for o in related[ProjectNote]] == [note.pk]

    def test_the_object_itself_is_never_listed(self, db):
        project = ProjectFactory()
        ProjectTaskFactory(project=project)

        related, _ = self._view_for(project)._collect_deletion_data()

        assert Project not in related


@pytest.mark.django_db
class TestMVPDeleteViewProtected:
    def test_get_shows_protected_flag_when_orderline_exists(self, client, product):
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["is_protected"] is True

    def test_get_lists_protected_objects(self, client, product):
        line = OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert line in response.context["protected_objects"]

    def test_get_html_has_no_delete_button_when_protected(self, client, product):
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        content = response.content.decode()
        # Delete submit button (btn-danger) must not be present.
        # Note: the language switcher renders type="submit" buttons (name="language"),
        # so we check for the danger-styled button class instead.
        assert "btn-danger" not in content

    def test_post_does_not_delete_protected_object(self, client, product):
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 200
        assert Product.objects.filter(pk=product.pk).exists()

    def test_get_shows_not_protected_after_orderline_removed(self, client, product):
        line = OrderLine.objects.create(product=product, quantity=1)
        line.delete()
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["is_protected"] is False


@pytest.mark.django_db
class TestMVPDeleteViewTypeToConfirm:
    def test_get_sets_require_confirmation_true(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["require_confirmation"] is True

    def test_get_sets_confirmation_value_to_str_object(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["confirmation_value"] == str(product)

    def test_post_wrong_confirmation_does_not_delete(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, data={"confirmation": "wrong-value"})
        assert response.status_code == 200
        assert Product.objects.filter(pk=product.pk).exists()

    def test_post_wrong_confirmation_shows_error(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, data={"confirmation": "wrong-value"})
        assert "confirmation" in response.context["form"].errors

    def test_post_correct_confirmation_deletes_object(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, data={"confirmation": str(product)})
        assert response.status_code == 302
        assert not Product.objects.filter(pk=product.pk).exists()

    def test_confirmation_value_empty_when_flag_off(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["confirmation_value"] == ""

    def test_page_renders_exactly_one_confirmation_input(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        soup = BeautifulSoup(client.get(url).content, "html.parser")
        inputs = soup.find_all("input", attrs={"name": "confirmation"})
        assert len(inputs) == 1
        assert inputs[0]["id"] == "id_confirmation"

    def test_confirmation_input_is_inside_the_form(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        soup = BeautifulSoup(client.get(url).content, "html.parser")
        field = soup.find("input", attrs={"name": "confirmation"})
        assert field.find_parent("form") is not None

    def test_confirmation_label_reaches_the_rendered_field(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        soup = BeautifulSoup(client.get(url).content, "html.parser")
        label = soup.find("label", attrs={"for": "id_confirmation"})
        assert label is not None
        assert label.get_text(strip=True)

    def test_protected_record_renders_no_confirmation_input(self, client, product):
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        assert response.context["is_protected"] is True
        assert soup.find_all("input", attrs={"name": "confirmation"}) == []


class TestDeleteViewPublicAPI:
    def test_mvp_delete_view_in_public_api(self):
        from mvp.views import MVPDeleteView

        assert MVPDeleteView is not None


@pytest.mark.django_db
class TestMVPUpdateViewDeleteUrl:
    def test_get_delete_url_contains_back_and_next_params(self, client, product):
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        delete_url = response.context["delete_url"]
        parsed = urlparse(delete_url)
        qs = parse_qs(parsed.query)
        assert "back" in qs, "delete_url must contain ?back"
        assert "next" in qs, "delete_url must contain ?next"

    def test_get_delete_url_back_points_to_update_page(self, client, product):
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        delete_url = response.context["delete_url"]
        qs = parse_qs(urlparse(delete_url).query)
        expected_back = reverse("product-update", kwargs={"pk": product.pk})
        assert qs["back"][0] == expected_back

    def test_get_delete_url_next_points_to_list(self, client, product):
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        delete_url = response.context["delete_url"]
        qs = parse_qs(urlparse(delete_url).query)
        expected_next = reverse("product-list")
        assert qs["next"][0] == expected_next

    def test_get_delete_url_returns_empty_on_reverse_failure(self):
        from django.test import RequestFactory

        from mvp.views.edit import MVPUpdateView

        rf = RequestFactory()
        request = rf.get("/")

        # Use a crud_views mapping where "update" points to a non-existent URL name.
        # _get_view_name("update") will format this and produce "no-such-product-update"
        # which has no URL registered → triggers NoReverseMatch inside get_delete_url().
        attrs = {
            "model": __import__("demo.models", fromlist=["Product"]).Product,
            "fields": ["name"],
            "template_name": "form_view.html",
            "show_list_action": True,
            "show_detail_action": True,
            "show_create_action": True,
            "show_update_action": True,
            "show_delete_action": True,
            "crud_views": {
                "list": "{model_name}-list",
                "detail": "{model_name}-detail",
                "create": "{model_name}-create",
                "update": "no-such-{model_name}-update",  # will cause NoReverseMatch
                "delete": "{model_name}-delete",
            },
        }
        view_cls = type("StubUpdateBadName", (MVPUpdateView,), attrs)
        view = view_cls()
        view.request = request
        view.kwargs = {"pk": 1}
        view.args = []

        class _Obj:
            pk = 1

            def __str__(self):
                return "Product 1"

        view.object = _Obj()
        # Must not raise — should return a URL string with the delete URL (back may be empty)
        result = view.get_delete_url()
        assert isinstance(result, str), (
            "get_delete_url() must return a string, not raise"
        )
        assert "delete" in result, "delete_url should still contain the delete path"


class TestDeleteViewRendering:
    @pytest.mark.django_db
    def test_US1_delete_page_has_delete_button(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert b'type="submit"' in response.content

    @pytest.mark.django_db
    def test_US1_delete_page_breadcrumb_has_three_levels(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert len(response.context["page"]["breadcrumbs"]) == 3

    @pytest.mark.django_db
    def test_US1_submit_delete_redirects_to_list_and_object_absent(
        self, client, product
    ):
        from demo.models import Product

        pk = product.pk
        url = reverse("product-delete", kwargs={"pk": pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")
        assert not Product.objects.filter(pk=pk).exists()


class TestDeleteViewRelatedObjects:
    @pytest.mark.django_db
    def test_US2_set_null_relations_are_not_listed_as_deleted(self, client, product):
        url = reverse("category-delete-related", kwargs={"pk": product.category.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert not response.context["related_objects"]

    @pytest.mark.django_db
    def test_US2_many_set_null_relations_still_list_nothing(self, client, category):
        from demo.models import Product

        for i in range(4):
            Product.objects.create(
                name=f"Overflow Product {i}",
                slug=f"overflow-product-integ-{i}",
                sku=f"OVF-{i:03d}",
                category=category,
            )

        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        assert not response.context["related_objects"]


class TestDeleteViewProtected:
    @pytest.mark.django_db
    def test_US3_protected_page_shows_protection_alert(self, client, product):
        from demo.models import OrderLine

        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        alert = soup.select_one('[role="alert"]')
        assert alert is not None
        assert "alert-error" in alert["class"]

    @pytest.mark.django_db
    def test_US3_protected_page_has_no_delete_button(self, client, product):
        from demo.models import OrderLine

        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        # The view sets is_protected=True which hides the submit button in the template.
        # We verify via context rather than raw HTML since other page elements (sidebar
        # settings form) may also contain type="submit".
        assert response.context["is_protected"] is True
        assert b"delete-submit-btn" not in response.content

    @pytest.mark.django_db
    def test_restrict_blocked_page_shows_protection_alert_on_get(self, client, product):
        from demo.models import ShipmentLine

        ShipmentLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["is_protected"] is True

    @pytest.mark.django_db
    def test_restrict_blocked_page_refuses_post(self, client, product):
        from demo.models import Product, ShipmentLine

        ShipmentLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert Product.objects.filter(pk=product.pk).exists()


class TestDeleteViewConfirmation:
    @pytest.mark.django_db
    def test_US4_wrong_confirmation_shows_inline_error(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, {"confirmation": "wrong-value"})
        assert response.context["form"].has_error("confirmation")

    @pytest.mark.django_db
    def test_US4_correct_confirmation_deletes_and_redirects(self, client, product):
        from demo.models import Product

        pk = product.pk
        url = reverse("product-delete-confirm", kwargs={"pk": pk})
        response = client.post(url, {"confirmation": str(product)})
        assert response.status_code == 302
        assert not Product.objects.filter(pk=pk).exists()

    @pytest.mark.django_db
    def test_US4_confirmation_input_visible_with_prompt(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "id_confirmation" in content
        assert str(product) in content


def _make_formset_in_context_view():
    """A GET-able MVPFormView subclass with a formset injected into its context.

    No parent object is involved — this is the standalone case (US2 scenario
    4), distinct from US3's inline formset tied to a parent record. form_class
    is a ModelForm (ProductForm) purely so PageObjectMixin can resolve
    model_meta; the formset itself is unrelated to that model.
    """
    FormSet = django_forms.formset_factory(ContactForm, extra=1)

    class StubFormsetView(MVPFormView):
        template_name = "form_view.html"
        form_class = ProductForm
        success_url = "/done/"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context["formset"] = FormSet()
            return context

    rf = RequestFactory()
    request = rf.get("/")
    request.user = User()
    return StubFormsetView, request


class TestFormViewStandaloneFormset:
    @pytest.mark.django_db
    def test_formset_in_context_renders_on_the_page(self):
        view_cls, request = _make_formset_in_context_view()
        response = view_cls.as_view()(request)
        response.render()
        html = response.content.decode()
        assert 'name="form-TOTAL_FORMS"' in html


# InlinesMixin is a default no-op on MVPCreateView/MVPUpdateView (#313)
#
# InlinesMixin is mixed into both views by default (mvp/views/edit.py) so a
# project adds rows to a page it already has by setting `inlines` on that
# same view. Declaring no `inlines` must leave the view behaving exactly as
# it would without the mixin — these tests are that guarantee.


def _dispatch_with_messages(view_cls, method="GET", data=None, view_kwargs=None):
    """Build a request carrying working session and messages storage, then
    dispatch it through ``view_cls`` via ``as_view()``.

    ``as_view()`` is called directly (no middleware runs), but ``form_valid``
    needs ``request._messages`` to queue the success flash, so session and
    messages middleware are applied to the request by hand.
    """
    rf = RequestFactory()
    request = rf.post("/", data=data or {}) if method == "POST" else rf.get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    MessageMiddleware(lambda r: None).process_request(request)
    return view_cls.as_view()(request, **(view_kwargs or {}))


class TestCreateViewWithOnlyFormClassIsUnaffectedByInlinesMixin:
    def _view_class(self):
        return type(
            "StubFormClassOnlyCreateView",
            (MVPCreateView,),
            {
                "form_class": ProductForm,
                "template_name": "form_view.html",
                "success_url": "/done/",
                "show_list_action": False,
                "show_detail_action": False,
            },
        )

    @pytest.mark.django_db
    def test_renders(self):
        response = _dispatch_with_messages(self._view_class())
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_saves_on_valid_submission(self):
        response = _dispatch_with_messages(
            self._view_class(),
            method="POST",
            data={"name": "New Product", "description": "", "price": ""},
        )
        assert response.status_code == 302
        assert Product.objects.filter(name="New Product").exists()


class TestUpdateViewWithNoInlinesIsUnaffectedByInlinesMixin:
    def _view_class(self, **extra_attrs):
        return type(
            "StubNoInlinesUpdateView",
            (MVPUpdateView,),
            {
                "model": Product,
                "fields": ["name"],
                "template_name": "form_view.html",
                "success_url": "/done/",
                "show_list_action": False,
                "show_detail_action": False,
                **extra_attrs,
            },
        )

    @pytest.mark.django_db
    def test_valid_submission_redirects_messages_and_saves(self):
        product = ProductFactory(name="Original")

        response = _dispatch_with_messages(
            self._view_class(),
            method="POST",
            data={"name": "Renamed"},
            view_kwargs={"pk": product.pk},
        )

        assert response.status_code == 302
        assert response["Location"] == "/done/"
        product.refresh_from_db()
        assert product.name == "Renamed"

    @pytest.mark.django_db
    def test_invalid_submission_does_not_re_read_the_object_from_the_database(
        self, monkeypatch
    ):
        product = ProductFactory(name="Original")
        refresh_calls = []
        original_refresh = Product.refresh_from_db

        def counting_refresh(self, *args, **kwargs):
            refresh_calls.append(kwargs)
            return original_refresh(self, *args, **kwargs)

        monkeypatch.setattr(Product, "refresh_from_db", counting_refresh)

        response = _dispatch_with_messages(
            self._view_class(),
            method="POST",
            data={"name": ""},  # required field left blank — invalid
            view_kwargs={"pk": product.pk},
        )

        assert response.status_code == 200
        assert refresh_calls == []

    @pytest.mark.django_db
    def test_context_inlines_is_empty(self):
        product = ProductFactory()

        response = _dispatch_with_messages(
            self._view_class(), view_kwargs={"pk": product.pk}
        )

        assert response.context_data["inlines"] == []


#
# Both claims below are about computed layout, which is why they run in a
# browser. A rendered-HTML assertion can say which elements are present and
# which classes they carry, but neither defect is visible at that level:
#
# - An alert is a column grid, so every direct child becomes its own column. A
#   message written as text with an emphasised word inside it produced three
#   columns, and the browser spread them across the alert's width. The markup
#   was correct in every other sense.
# - The content above the form and the form itself sat flush against each
#   other. Nothing in the markup says so — only the boxes the browser computed.

DESKTOP = {"width": 1440, "height": 900}

# The icon plus one content column. Anything more means the message was split.
EXPECTED_ALERT_COLUMNS = 2


def alert_columns(page):
    """Return the alert's resolved grid columns, as a list of track sizes."""
    return page.evaluate("""
        () => getComputedStyle(document.querySelector('[role=alert]'))
                .gridTemplateColumns.split(' ')
    """)


def gap_above_form(page):
    """Return the vertical distance between the content above the form and it."""
    return page.evaluate("""
        () => {
          const form = document.querySelector('.mvp-delete-page form');
          const previous = form.previousElementSibling;
          return Math.round(form.getBoundingClientRect().top
                            - previous.getBoundingClientRect().bottom);
        }
    """)


@pytest.mark.e2e
@requires_browser
@pytest.mark.django_db(transaction=True)
class TestDeletePageAlertLayout:
    def test_warning_alert_has_one_content_column(self, page, live_server, product):
        path = reverse("product-delete", kwargs={"pk": product.pk})
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{path}")

        columns = alert_columns(page)

        assert len(columns) == EXPECTED_ALERT_COLUMNS, (
            f"alert resolved to {len(columns)} columns ({columns}); the message "
            "is being split across them instead of flowing as one block"
        )

    def test_blocked_alert_has_one_content_column(self, page, live_server, product):
        OrderLine.objects.create(product=product, quantity=1)
        path = reverse("product-delete", kwargs={"pk": product.pk})
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{path}")

        columns = alert_columns(page)

        assert len(columns) == EXPECTED_ALERT_COLUMNS, (
            f"alert resolved to {len(columns)} columns ({columns})"
        )


@pytest.mark.e2e
@requires_browser
@pytest.mark.django_db(transaction=True)
class TestDeletePageSpacing:
    def test_form_is_spaced_from_the_content_above_it(self, page, live_server, product):
        path = reverse("product-delete", kwargs={"pk": product.pk})
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{path}")

        assert gap_above_form(page) > 0, (
            "the form starts where the warning ends, so the actions read as part "
            "of the alert"
        )

    def test_confirmation_page_is_spaced_from_the_content_above_it(
        self, page, live_server, product
    ):
        path = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{path}")

        assert gap_above_form(page) > 0


@pytest.mark.e2e
@requires_browser
@pytest.mark.django_db(transaction=True)
class TestDeletePageTypeToConfirmInteraction:
    def _open(self, page, live_server, product):
        path = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{path}")
        return page.locator("#id_confirmation"), page.locator("#delete-submit-btn")

    def test_delete_button_starts_disabled(self, page, live_server, product):
        _, button = self._open(page, live_server, product)

        assert button.is_disabled()

    def test_wrong_value_leaves_the_button_disabled(self, page, live_server, product):
        field, button = self._open(page, live_server, product)

        field.fill("not the name")

        assert button.is_disabled()

    def test_matching_value_enables_the_button(self, page, live_server, product):
        field, button = self._open(page, live_server, product)

        field.fill(str(product))

        assert button.is_enabled()

    def test_submitting_the_typed_value_deletes_the_record(
        self, page, live_server, product
    ):
        field, button = self._open(page, live_server, product)

        field.fill(str(product))
        button.click()
        page.wait_for_url(f"{live_server.url}{reverse('product-list')}")

        assert not Product.objects.filter(pk=product.pk).exists()
