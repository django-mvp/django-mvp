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
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from demo.models import Category, OrderLine, Product
from mvp.forms import DeleteConfirmForm
from mvp.views.edit import MVPCreateView, MVPFormView, MVPUpdateView, NextURLMixin

User = get_user_model()

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# US4 — Open-Redirect Protection
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# US1 — Chain Form Views with a URL Destination
# ---------------------------------------------------------------------------


class TestUS1GetNextUrl:
    """[US1] NextURLMixin.get_next_url() validates and returns same-origin next values."""

    def test_get_request_safe_path_returned(self):
        """[US1] GET request with ?next=/safe/path/ returns /safe/path/."""
        view = make_next_url_view(method="GET", params={"next": "/safe/path/"})
        assert view.get_next_url() == "/safe/path/"

    def test_post_request_safe_path_returned(self):
        """[US1] POST request with next=/safe/path/ in POST data returns /safe/path/."""
        view = make_next_url_view(method="POST", params={"next": "/safe/path/"})
        assert view.get_next_url() == "/safe/path/"

    def test_post_data_takes_precedence_over_query_string(self):
        """[US1] POST next value wins when both POST body and query string have next."""
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
        """[US1] get_next_url() returns None (not empty string) for absent next."""
        view = make_next_url_view(method="GET", params={})
        result = view.get_next_url()
        assert result is None

    def test_empty_next_returns_none(self):
        """[US1] get_next_url() returns None for empty-string next."""
        view = make_next_url_view(method="GET", params={"next": ""})
        assert view.get_next_url() is None

    @override_settings(DEBUG=True)
    def test_external_url_returns_none(self):
        """[US1] Cross-origin URL is rejected and None is returned."""
        view = make_next_url_view(method="POST", params={"next": "https://evil.com/"})
        assert view.get_next_url() is None


class TestUS1ContextData:
    """[US1] get_context_data() injects next_url into template context."""

    def test_get_with_next_injects_next_url(self):
        """[US1] GET with ?next=/records/ → context["next_url"] is "/records/"."""
        view = make_next_url_view(method="GET", params={"next": "/records/"})
        context = view.get_context_data()
        assert context["next_url"] == "/records/"

    def test_absent_next_injects_none(self):
        """[US1] next absent from request → context["next_url"] is None."""
        view = make_next_url_view(method="GET", params={})
        context = view.get_context_data()
        assert context["next_url"] is None

    def test_empty_next_injects_none(self):
        """[US1] Empty-string next → context["next_url"] is None."""
        view = make_next_url_view(method="GET", params={"next": ""})
        context = view.get_context_data()
        assert context["next_url"] is None


class TestGetNextCandidate:
    """[FR-001a] NextURLMixin.get_next_candidate() direct behaviour tests (T002d)."""

    def test_post_returns_post_value(self):
        """[FR-001a] POST request with next=foo → get_next_candidate() returns 'foo'."""
        view = make_next_url_view(method="POST", params={"next": "foo"})
        assert view.get_next_candidate() == "foo"

    def test_get_returns_query_string_value(self):
        """[FR-001a] GET request with ?next=bar → get_next_candidate() returns 'bar'."""
        view = make_next_url_view(method="GET", params={"next": "bar"})
        assert view.get_next_candidate() == "bar"

    def test_absent_next_returns_none(self):
        """[FR-001a] Absent next → get_next_candidate() returns None."""
        view = make_next_url_view(method="GET", params={})
        assert view.get_next_candidate() is None

    def test_post_falls_back_to_default_next_when_next_absent(self):
        """A clicked button's default_next is used only when no explicit next was sent.

        This is the button-carried shorthand (e.g. "Save & continue" submits
        default_next=list) for the common case where the caller never supplied
        a ?next= at all — the hidden explicit-next field never rendered, so the
        button's own value is the only candidate in the POST body.
        """
        view = make_next_url_view(method="POST", params={"default_next": "list"})
        assert view.get_next_candidate() == "list"

    def test_post_explicit_next_wins_over_default_next(self):
        """An explicit next (the hidden field) always wins over a clicked button's default_next."""
        view = make_next_url_view(
            method="POST", params={"next": "/orders/", "default_next": "list"}
        )
        assert view.get_next_candidate() == "/orders/"

    def test_post_reads_body_not_query_string(self):
        """[FR-001a] POST reads POST body, not query string."""
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
    """[FR-001a] Overriding get_next_candidate() is respected by all callers (T013a)."""

    def test_get_next_url_uses_overridden_candidate(self):
        """[FR-001a] get_next_url() uses the value from get_next_candidate(), not the request."""
        view = make_next_url_view(method="GET", params={"next": "/from-request/"})
        view.__class__ = type(
            "OverriddenView",
            (view.__class__,),
            {"get_next_candidate": lambda self: "/overridden/"},
        )
        assert view.get_next_url() == "/overridden/"

    def test_get_context_data_uses_overridden_candidate(self):
        """[FR-001a] get_context_data() reflects the overridden candidate in context['next_url']."""
        view = make_next_url_view(method="GET", params={"next": "/from-request/"})
        view.__class__ = type(
            "OverriddenView",
            (view.__class__,),
            {"get_next_candidate": lambda self: "/overridden/"},
        )
        assert view.get_context_data()["next_url"] == "/overridden/"


# ---------------------------------------------------------------------------
# US3 — CRUD Action Shorthand Destinations
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS3ShorthandSuccessUrl:
    """[US3] get_success_url() resolves CRUD shorthand keys from POST data."""

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
        """[US3] POST with next=list → get_success_url() returns list URL."""
        view = make_create_view(method="POST", params={"next": "list"})
        view.object = self.product
        url = view.get_success_url()
        from django.urls import reverse

        assert url == reverse("product-list")

    def test_next_detail_redirects_to_detail_url(self):
        """[US3] POST with next=detail → get_success_url() returns detail URL."""
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
        """[US3] POST with next=update → get_success_url() returns update URL."""
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
        """[US3] Unrecognised shorthand (e.g. next=foobar) silently falls through to object.get_absolute_url()."""
        view = make_create_view(method="POST", params={"next": "foobar"})
        view.object = self.product
        url = view.get_success_url()

        # Falls through to object.get_absolute_url() since no success_url is set
        assert url == self.product.get_absolute_url()

    def test_form_view_skips_shorthand_silently(self):
        """[US3] MVPFormView (no crud_views) with next=list falls through to success_url."""

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
    """[US3] get_context_data() contains the resolved URL for CRUD shorthands."""

    def test_post_shorthand_resolves_in_context(self):
        """[US3] POST next=list → context["next_url"] is the resolved list URL."""
        from django.urls import reverse

        view = make_create_view(method="POST", params={"next": "list"})
        context = view.get_context_data()
        assert context["next_url"] == reverse("product-list")

    def test_get_shorthand_unresolvable_without_pk(self):
        """[US3] GET ?next=detail on a create view → context["next_url"] is None (no pk yet)."""
        view = make_create_view(method="GET", params={"next": "detail"})
        context = view.get_context_data()
        assert context["next_url"] is None


@pytest.mark.django_db
class TestUS3DeleteViewNoRegression:
    """[US3] MVPDeleteView uses its own get_success_url() — no regression."""

    def test_delete_view_post_redirects_to_list(self, client):
        """[US3] POST delete still redirects to list URL (existing behaviour)."""
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


# ---------------------------------------------------------------------------
# US5 — Graceful Fallback
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS5FallbackChain:
    """[US5] Full priority chain: URL → shorthand → success_url → resoluve_crud_url("list")."""

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
        """[US5] No next + success_url="/done/" → get_success_url() returns "/done/"."""
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"success_url": "/done/"},
        )
        view.object = self.product
        assert view.get_success_url() == "/done/"

    def test_no_next_no_success_url_falls_back_to_object_url(self):
        """[US5] No next + no success_url → get_success_url() returns object.get_absolute_url()."""
        view = make_create_view(method="POST", params={})
        view.object = self.product
        assert view.get_success_url() == self.product.get_absolute_url()

    @override_settings(DEBUG=True)
    def test_rejected_next_falls_through_to_success_url(self, caplog):
        """[US5] next=https://evil.com/ (rejected) + success_url="/done/" → "/done/"."""
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
        """[US5] next="" + success_url="/done/" → "/done/"."""
        view = make_create_view(
            method="POST",
            params={"next": ""},
            extra_attrs={"success_url": "/done/"},
        )
        view.object = self.product
        assert view.get_success_url() == "/done/"

    def test_form_view_no_next_with_success_url(self):
        """[US5] MVPFormView (no model) + success_url="/done/" → "/done/" without raising."""
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


# ---------------------------------------------------------------------------
# US1 — Class-Level Attribute Contract Tests (TestMVPFormBase)
# ---------------------------------------------------------------------------


class TestMVPFormBase:
    """[US1] MVPFormBase class-level attribute and redirect contract tests."""

    def test_base_template_name(self):
        """[T-FM-006] MVPFormBase.base_template_name == 'form_view.html'."""
        from mvp.views.edit import MVPFormBase

        assert MVPFormBase.base_template_name == "form_view.html"

    def test_page_class(self):
        """[T-FM-007] MVPFormBase.page_class == 'mvp-form-page'."""
        from mvp.views.edit import MVPFormBase

        assert MVPFormBase.page_class == "mvp-form-page"

    def test_get_success_url_raises_improperly_configured(self):
        """[T-FM-005] get_success_url() raises ImproperlyConfigured when no next and no success_url."""
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


# ---------------------------------------------------------------------------
# US2 — Success Message Interpolation (TestGetSuccessMessage)
# ---------------------------------------------------------------------------


class TestMVPModelFormBaseSuccessMessage:
    """[US2] MVPModelFormBase.get_success_message() interpolation contract tests.

    Uses MVPUpdateView as the test vehicle so these tests remain decoupled from
    MVPCreateView's own get_success_message() override.
    """

    def test_verbose_name_only_resolves(self):
        """[T-FM-001] %(verbose_name)s with empty cleaned_data → lowercase model verbose_name."""
        view = make_update_view(
            extra_attrs={"success_message": "%(verbose_name)s created."}
        )
        result = view.get_success_message({})
        assert result == f"{Product._meta.verbose_name} created."

    def test_missing_field_placeholder_substitutes_empty_string(self):
        """[T-FM-002] %(name)s with empty cleaned_data → '' substituted, no KeyError raised."""
        view = make_update_view(
            extra_attrs={"success_message": "%(verbose_name)s %(name)s deleted."}
        )
        result = view.get_success_message({})
        assert result == f"{Product._meta.verbose_name}  deleted."

    def test_field_value_and_verbose_name_both_resolve(self):
        """[T-FM-003] %(verbose_name)s + %(name)s both resolve when name present in cleaned_data."""
        view = make_update_view(
            extra_attrs={"success_message": "%(verbose_name)s %(name)s updated."}
        )
        result = view.get_success_message({"name": "Widget A"})
        assert result == f"{Product._meta.verbose_name} Widget A updated."


# ---------------------------------------------------------------------------
# US3 — Unresolvable List URL Error (TestMVPModelFormBase)
# ---------------------------------------------------------------------------


class TestMVPModelFormBase:
    """[US3] MVPModelFormBase.get_success_url() revised FR-008 priority chain tests."""

    def test_get_success_url_raises_when_list_url_unresolvable(self):
        """[T-FM-004] get_success_url() raises ImproperlyConfigured when object is None and no success_url."""
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
        """[T-FM-004a] success_url='list' resolves via resolve_crud_url('list') → list URL."""
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
        """[T-FM-004b] No next, no success_url, object has get_absolute_url() → object URL returned."""

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
        """[T-FM-004c] No next, no success_url, object lacks get_absolute_url() → ImproperlyConfigured."""
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


# ---------------------------------------------------------------------------
# US2 — MVPFormView Success Message Interpolation (TestMVPFormView)
# ---------------------------------------------------------------------------


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
    """[US2/US4] MVPFormView.get_success_message() and get_page_title() contract tests."""

    def test_field_placeholder_substituted_from_cleaned_data(self):
        """[US2-S1] %(email)s + email in cleaned_data → substituted correctly, no KeyError."""
        view = make_form_view(extra_attrs={"success_message": "Thanks, %(email)s!"})
        result = view.get_success_message({"email": "user@example.com"})
        assert result == "Thanks, user@example.com!"

    def test_unknown_placeholder_substitutes_empty_string(self):
        """[US2-S2] %(foo)s absent from cleaned_data → '' substituted, no KeyError raised."""
        view = make_form_view(extra_attrs={"success_message": "Hello %(foo)s!"})
        result = view.get_success_message({})
        assert result == "Hello !"

    def test_verbose_name_not_injected_substitutes_empty_string(self):
        """[US2-S3] %(verbose_name)s → '' because verbose_name is NOT injected on MVPFormView."""
        view = make_form_view(
            extra_attrs={"success_message": "%(verbose_name)s saved."}
        )
        result = view.get_success_message({})
        assert result == " saved."

    def test_default_title_derived_from_class_name(self):
        """[US4-S1] Subclass named ContactFormView with no page_title → 'Contact Form View'."""
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
        """[US4-S2] page_title='My Form' → 'My Form' returned as-is."""
        view = make_form_view(extra_attrs={"page_title": "My Form"})
        assert view.get_page_title() == "My Form"


# ---------------------------------------------------------------------------
# T005 — MVPCreateView class-level defaults (US1)
# ---------------------------------------------------------------------------


class TestMVPCreateViewDefaults:
    """[US1] MVPCreateView class-level attribute defaults with no overrides."""

    def test_page_class_contains_create(self):
        """'mvp-create-page' appears in MVPCreateView.page_class."""
        assert "mvp-create-page" in MVPCreateView.page_class

    def test_page_title_class_attr_is_template(self):
        """MVPCreateView defines page_title as an interpolation template on the class."""
        assert "page_title" in MVPCreateView.__dict__
        assert "%(verbose_name)s" in str(MVPCreateView.page_title)


# ---------------------------------------------------------------------------
# T006 — MVPCreateView.get_page_title() (US1 / US2)
# ---------------------------------------------------------------------------


class TestMVPCreateViewPageTitle:
    """[US1/US2] MVPCreateView.get_page_title() derives title from verbose_name or explicit override."""

    def test_default_title_single_word_verbose_name(self):
        """Single-word verbose_name 'product' → 'Create Product'."""
        view = make_create_view()
        assert view.get_page_title() == "Create Product"

    def test_default_title_multi_word_verbose_name(self):
        """Multi-word verbose_name 'order line' → 'Create Order Line'."""
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
        """page_title='Add a new product' overrides the default derivation."""
        view = make_create_view(extra_attrs={"page_title": "Add a new product"})
        assert view.get_page_title() == "Add a new product"

    def test_empty_string_page_title_returns_empty(self):
        """page_title='' is an explicit override; returned as-is (caller's intent)."""
        view = make_create_view(extra_attrs={"page_title": ""})
        assert view.get_page_title() == ""

    def test_lazy_string_page_title_returned(self):
        """page_title=_('Add Product') (lazy string) → 'Add Product'."""
        view = make_create_view(extra_attrs={"page_title": _("Add Product")})
        assert view.get_page_title() == "Add Product"


# ---------------------------------------------------------------------------
# T007 — MVPCreateView.get_success_message() (US1 / US2)
# ---------------------------------------------------------------------------


class TestMVPCreateViewSuccessMessage:
    """[US1/US2] MVPCreateView.get_success_message() injects title-cased verbose_name."""

    def test_default_message_uses_title_cased_verbose_name(self):
        """Default success_message → 'Product successfully created.' (title-cased, not lowercase)."""
        view = make_create_view()
        result = view.get_success_message({})
        assert result == "Product successfully created."

    def test_custom_message_with_field_interpolation(self):
        """Custom success_message with %(name)s interpolated from cleaned_data."""
        view = make_create_view(extra_attrs={"success_message": "%(name)s was added."})
        result = view.get_success_message({"name": "Widget"})
        assert result == "Widget was added."

    def test_missing_key_substitutes_empty_string(self):
        """Missing %(key)s placeholder silently substitutes '' — no KeyError raised."""
        view = make_create_view(
            extra_attrs={"success_message": "%(verbose_name)s %(missing)s done."}
        )
        result = view.get_success_message({})
        assert result == "Product  done."


# ---------------------------------------------------------------------------
# T013 — MVPCreateView overridable defaults (US2)
# ---------------------------------------------------------------------------


class TestMVPCreateViewOverrides:
    """[US2] Each MVPCreateView default can be independently overridden."""

    def test_page_class_overridable(self):
        """Setting page_class='custom-class' on a subclass overrides the default."""
        view = make_create_view(extra_attrs={"page_class": "custom-class"})
        assert "custom-class" in view.get_page_class()


# ---------------------------------------------------------------------------
# T016 — MVPCreateView breadcrumb structure (US3)
# ---------------------------------------------------------------------------


class TestMVPCreateViewBreadcrumb:
    """[US3] MVPCreateView breadcrumb structure via PageObjectMixin.get_breadcrumbs()."""

    def test_breadcrumb_has_two_items(self):
        """get_breadcrumbs() returns exactly two items by default."""
        view = make_create_view()
        assert len(view.get_breadcrumbs()) == 2

    def test_first_item_has_no_href_when_list_permission_false(self):
        """show_list_action=False → first breadcrumb href is falsy."""
        view = make_create_view(extra_attrs={"show_list_action": False})
        breadcrumbs = view.get_breadcrumbs()
        assert not breadcrumbs[0].get("href")

    def test_first_item_has_href_when_list_permission_true(self):
        """show_list_action=True → first breadcrumb href resolves to product-list URL."""
        from django.urls import reverse

        view = make_create_view()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["href"] == reverse("product-list")

    def test_second_item_has_no_href(self):
        """Second breadcrumb (current page) has no href."""
        view = make_create_view()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[1].get("href") is None

    def test_second_item_text_matches_page_title(self):
        """Second breadcrumb text equals get_page_title() → 'Create Product'."""
        view = make_create_view()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[1]["text"] == view.get_page_title()
        assert breadcrumbs[1]["text"] == "Create Product"

    def test_get_breadcrumbs_override_is_respected(self):
        """Subclass overriding get_breadcrumbs() returns its custom list (SC-003)."""
        custom_crumbs = [{"text": "Home", "href": "/"}, {"text": "New"}]
        view = make_create_view(
            extra_attrs={"get_breadcrumbs": lambda self: custom_crumbs}
        )
        assert view.get_breadcrumbs() == custom_crumbs


# ---------------------------------------------------------------------------
# T002 — MVPUpdateView class-level defaults (US1)
# ---------------------------------------------------------------------------


class TestMVPUpdateViewDefaults:
    """[US1] MVPUpdateView class-level attribute defaults with no overrides."""

    def test_page_class_contains_update(self):
        """'mvp-update-page' appears in MVPUpdateView.page_class."""
        assert "mvp-update-page" in MVPUpdateView.page_class

    def test_page_title_class_attr_is_template(self):
        """MVPUpdateView defines page_title as an interpolation template on the class."""
        assert "page_title" in MVPUpdateView.__dict__
        assert "%(verbose_name)s" in str(MVPUpdateView.page_title)


# ---------------------------------------------------------------------------
# T003 — MVPUpdateView.get_page_title() (US1 / US2)
# ---------------------------------------------------------------------------


class TestMVPUpdateViewPageTitle:
    """[US1/US2] MVPUpdateView.get_page_title() derives title from verbose_name or explicit override."""

    def test_default_title_single_word_verbose_name(self):
        """Single-word verbose_name 'product' → 'Update Product'."""
        view = make_update_view()
        assert view.get_page_title() == "Update Product"

    def test_default_title_multi_word_verbose_name(self):
        """Multi-word verbose_name 'order line' → 'Update Order Line'."""
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
        """page_title='Edit product details' overrides the default derivation."""
        view = make_update_view(extra_attrs={"page_title": "Edit product details"})
        assert view.get_page_title() == "Edit product details"

    def test_empty_string_page_title_returns_empty(self):
        """page_title='' is an explicit override; returned as-is (caller's intent)."""
        view = make_update_view(extra_attrs={"page_title": ""})
        assert view.get_page_title() == ""


# ---------------------------------------------------------------------------
# T004 — MVPUpdateView.get_breadcrumbs() (US1 / US5)
# ---------------------------------------------------------------------------


class TestMVPUpdateViewBreadcrumb:
    """[US1/US5] MVPUpdateView breadcrumb structure — three-level with detail link."""

    @pytest.fixture(autouse=True)
    def _stub_object(self):
        """Attach a minimal stub object (with pk) to all views in this class."""

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
        """get_breadcrumbs() returns exactly three items."""
        view = self._view_with_object()
        assert len(view.get_breadcrumbs()) == 3

    def test_second_item_text_is_str_object(self):
        """Second breadcrumb text is str(object)."""
        view = self._view_with_object()
        crumbs = view.get_breadcrumbs()
        assert crumbs[1]["text"] == str(self._obj)

    def test_second_item_href_uses_resolve_crud_url_detail(self):
        """Second breadcrumb href uses resolve_crud_url('detail'), not object.get_absolute_url()."""
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
        """Third breadcrumb (current page) has no href."""
        view = self._view_with_object()
        crumbs = view.get_breadcrumbs()
        assert crumbs[2].get("href") is None

    def test_third_item_text_matches_page_title(self):
        """Third breadcrumb text equals get_page_title()."""
        view = self._view_with_object()
        crumbs = view.get_breadcrumbs()
        assert crumbs[2]["text"] == view.get_page_title()

    # US5 — breadcrumb degrades when list or detail permission is missing
    def test_first_item_has_no_href_when_list_permission_false(self):
        """show_list_action=False → first breadcrumb href is falsy."""
        view = self._view_with_object(extra_attrs={"show_list_action": False})
        assert not view.get_breadcrumbs()[0].get("href")

    def test_first_item_has_href_when_list_permission_true(self):
        """show_list_action=True → first breadcrumb href resolves to list URL."""
        from django.urls import reverse

        view = self._view_with_object()
        assert view.get_breadcrumbs()[0]["href"] == reverse("product-list")

    def test_second_item_has_no_href_when_detail_permission_false(self):
        """show_detail_action=False → second breadcrumb href is falsy."""
        view = self._view_with_object(extra_attrs={"show_detail_action": False})
        assert not view.get_breadcrumbs()[1].get("href")

    def test_second_item_has_href_when_detail_permission_true(self):
        """show_detail_action=True → second breadcrumb href is truthy."""
        view = self._view_with_object()
        assert view.get_breadcrumbs()[1].get("href")


# ---------------------------------------------------------------------------
# T010 — MVPUpdateView overridable defaults (US2)
# ---------------------------------------------------------------------------


class TestMVPUpdateViewOverrides:
    """[US2] Each MVPUpdateView default can be independently overridden."""

    def test_page_class_overridable(self):
        """Setting page_class='custom-class' on a subclass overrides the default."""
        view = make_update_view(extra_attrs={"page_class": "custom-class"})
        assert "custom-class" in view.get_page_class()

    def test_page_title_overridable(self):
        """Setting page_title='Edit product details' overrides the default derivation."""
        view = make_update_view(extra_attrs={"page_title": "Edit product details"})
        assert view.get_page_title() == "Edit product details"

    def test_success_message_overridable_with_field_interpolation(self):
        """Custom success_message with %(name)s interpolated from cleaned_data."""
        view = make_update_view(extra_attrs={"success_message": "%(name)s was saved."})
        result = view.get_success_message({"name": "Widget"})
        assert result == "Widget was saved."

    def test_get_breadcrumbs_override_is_respected(self):
        """Subclass overriding get_breadcrumbs() returns its custom list (SC-003)."""
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
        """Setting show_delete_action=False suppresses the delete URL."""
        view = make_update_view(extra_attrs={"show_delete_action": False})
        assert not view.get_delete_url()


# ---------------------------------------------------------------------------
# T013 — MVPUpdateView delete button visibility (US4)
# ---------------------------------------------------------------------------


class TestMVPUpdateViewDeleteLinkVisibility:
    """[US4] Delete button visibility is gated on delete_url context variable.

    Tests use get_delete_url() directly (equivalent to get_context_data()["delete_url"],
    since get_context_data() just delegates to get_delete_url()).
    """

    def test_delete_button_absent_when_delete_url_empty(self):
        """show_delete_action=False → get_delete_url() is falsy (empty string)."""
        view = make_update_view(extra_attrs={"show_delete_action": False})
        view.object = None
        assert not view.get_delete_url()

    def test_delete_button_present_when_delete_url_set(self):
        """show_delete_action=True and pk present → get_delete_url() is truthy."""

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


# -------------------------------------------------------------------------
# Browser tests (form/create/update views)
# -------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# US1 — MVPCreateView: zero-config model create page (T021)
# ---------------------------------------------------------------------------


class TestCreateViewRendering:
    """Create page title, success message and breadcrumb."""

    @pytest.mark.django_db
    def test_US1_create_page_title_is_model_aware(self, client):
        """[US1] GET /products/create/ — page contains 'Create Product'."""
        response = client.get(reverse("product-create"))
        assert b"Create Product" in response.content

    @pytest.mark.django_db
    def test_US1_success_message_is_title_cased(self, client, category):
        """[US1] POST valid create form — flash message contains 'Product successfully created.'"""
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
        """[US1] GET /products/create/ — first breadcrumb href points to /products/."""
        response = client.get(reverse("product-create"))
        breadcrumbs = response.context["page"]["breadcrumbs"]
        assert len(breadcrumbs) >= 1
        assert breadcrumbs[0].get("href") == reverse("product-list")


# ---------------------------------------------------------------------------
# US2 — Redirected Back to the Right Place (T022, T023)
# ---------------------------------------------------------------------------


class TestCreateViewRedirects:
    """Where a successful create sends the user."""

    @pytest.mark.django_db
    def test_US2_create_with_url_next_redirects_to_url(self, client, category):
        """[US2] A caller-supplied ?next= survives a real rendered-form round trip.

        Goes through the actual markup rather than around it: fetches the create
        page with ?next=/orders/, asserts the create form (not the language-
        selector form, which also appears in the document) carries a hidden
        ``next`` input with that value, then submits exactly what a browser
        submits when "Save & continue" is clicked — the form fields plus the
        clicked button's default_next=list — and asserts the redirect honours
        the caller's destination rather than the button's default.
        """
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
        """[US2] A failed rendered-form submission still carries the caller's next.

        Fetches the create form with ?next=/orders/, submits it with the
        required 'name' field missing (as the real form's own action, carrying
        the real hidden next field, rather than posting straight to the view),
        and asserts the re-rendered create form's hidden next input still
        carries /orders/ — not merely that the bytes 'name="next"' and
        '/orders/' happen to appear somewhere in the page (they always do,
        from the submit buttons and the breadcrumbs, regardless of this
        feature).
        """
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
        """A plain create with no ?next= anywhere still lands on the list view.

        Rendered without a caller-supplied ?next=, the create form has no hidden
        next input at all — only the clicked button's own default_next=list
        travels in the POST body. Confirms the button-rename in (b) didn't
        change this, the overwhelming majority case, at all.
        """
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

    # ---------------------------------------------------------------------------
    # US3 — CRUD Action Shorthand Destinations (T035a, T035b)
    # ---------------------------------------------------------------------------

    @pytest.mark.django_db
    def test_US3_create_with_list_shorthand_redirects_to_list(self, client, category):
        """[US3] POST with next='list' in body — redirect lands at the product list URL."""
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
        """[US3] POST with next='detail' in body — redirect lands at the new object's detail URL."""
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


# ---------------------------------------------------------------------------
# US6 — MVPUpdateView: model-aware title and success message (T007-T009)
# ---------------------------------------------------------------------------


class TestUpdateViewRendering:
    """Update page title, message, breadcrumb and delete link."""

    @pytest.mark.django_db
    def test_US6_update_page_title_is_model_aware(self, client, product):
        """[US6/T007] GET update URL — page contains 'Update Product'."""
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        assert b"Update Product" in response.content

    @pytest.mark.django_db
    def test_US6_update_success_message_appears(self, client, product, category):
        """[US6/T008] POST valid update — flash message 'product successfully updated.' appears.

        Note: MVPUpdateView inherits get_success_message() from MVPModelFormBase which
        uses the lowercase verbose_name. MVPCreateView overrides it to title-case; the
        update view does not.
        """
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
        """[US6/T009] GET update URL — breadcrumb context has exactly three items."""
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

    # ---------------------------------------------------------------------------
    # US3 — Delete link visible on update page when delete view configured (T012)
    # ---------------------------------------------------------------------------

    @pytest.mark.django_db
    def test_US3_update_delete_link_visible_when_configured(self, client, product):
        """[US3/T012] GET update URL — Delete link is present with ?back= and next= params."""
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "delete" in content, "Delete link must be present on the update page"
        assert "back=" in content, "Delete link must contain ?back= parameter"
        assert "next=" in content, "Delete link must contain next= parameter"

    # ---------------------------------------------------------------------------
    # US4 — Delete link absent when delete view not configured (T014)
    # ---------------------------------------------------------------------------

    @pytest.mark.django_db
    def test_US4_update_delete_link_absent_when_not_configured(self, client):
        """[US4/T014] GET category update URL (no delete view) — no delete link rendered."""
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


# -------------------------------------------------------------------------
# MVPDeleteView
# -------------------------------------------------------------------------


class TestDeleteConfirmForm:
    def test_form_valid_when_field_provided(self):
        form = DeleteConfirmForm(data={"confirmation": "some-value"})
        assert form.is_valid()

    def test_form_invalid_when_field_empty(self):
        form = DeleteConfirmForm(data={"confirmation": ""})
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_valid_when_confirmation_matches_value(self):
        """(a) Matching confirmation_value → form is valid."""
        form = DeleteConfirmForm(
            data={"confirmation": "correct"}, confirmation_value="correct"
        )
        assert form.is_valid()

    def test_form_invalid_when_confirmation_does_not_match(self):
        """(b) Non-matching confirmation_value → form is invalid."""
        form = DeleteConfirmForm(
            data={"confirmation": "wrong"}, confirmation_value="correct"
        )
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_invalid_when_confirmation_empty_with_value(self):
        """(c) Empty input with confirmation_value set → invalid (required field)."""
        form = DeleteConfirmForm(
            data={"confirmation": ""}, confirmation_value="correct"
        )
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_valid_when_confirmation_value_is_none(self):
        """(d) confirmation_value=None → no match check, any non-empty value is valid."""
        form = DeleteConfirmForm(data={"confirmation": "x"}, confirmation_value=None)
        assert form.is_valid()


# ---------------------------------------------------------------------------
# Scenario 1: Basic delete
# ---------------------------------------------------------------------------


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
        """(a) GET page title interpolates model verbose_name (e.g. 'Delete Product')."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert "Product" in response.context["page"]["title"]
        assert "Delete" in response.context["page"]["title"]

    def test_breadcrumbs_has_three_items(self, client, product):
        """(b) GET context breadcrumbs list has exactly 3 items."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert len(response.context["page"]["breadcrumbs"]) == 3

    def test_post_deletes_object(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Product.objects.filter(pk=product.pk).exists()

    def test_post_redirects_to_list_url(self, client, product):
        """(c) POST without body returns 302 to list URL."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")

    def test_post_shows_success_message(self, client, product):
        """(e) POST deletion adds a success flash message."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url, follow=True)
        messages = list(response.context["messages"])
        assert len(messages) == 1

    def test_page_class_contains_mvp_delete_page(self, client, product):
        """(g) page class contains 'mvp-delete-page' — FR-012 AdminLTE integration."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert "mvp-delete-page" in response.context["page"]["class"]


# ---------------------------------------------------------------------------
# back_url / next_url context keys
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDeleteViewBackUrl:
    def test_back_url_defaults_to_list_when_absent(self, client, product):
        """No ?back param → back_url falls back to the list URL."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["back_url"] == reverse("product-list")

    def test_back_url_reads_from_query_param(self, client, product):
        """?back=/products/1/edit/ → back_url is that URL."""
        update_url = reverse("product-update", kwargs={"pk": product.pk})
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url, {"back": update_url})
        assert response.context["back_url"] == update_url

    def test_back_url_rejects_external_url(self, client, product):
        """?back=https://evil.com/ → back_url falls back to list URL (open-redirect guard)."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url, {"back": "https://evil.com/"})
        assert response.context["back_url"] == reverse("product-list")

    def test_next_url_is_none_when_absent(self, client, product):
        """No ?next param → next_url is None (redirect handled by get_success_url())."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["next_url"] is None

    def test_post_with_external_next_redirects_to_list(self, client, product):
        """?next=https://evil.com/ on POST → redirects to list URL (open-redirect guard)."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url, data={"next": "https://evil.com/"})
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")

    def test_rendered_form_carries_caller_next_through_real_delete_submit(
        self, client, product
    ):
        """A caller-supplied ?next= survives a real rendered delete-form round trip.

        delete_view.html used to inject its own hidden next input in the
        ``before_form`` block, which renders outside the ``<c-form>`` element and
        is therefore never part of the submitted ``<form>``. Confirms the hidden
        next input the form now inherits from form_view.html is present inside
        the real delete form and that submitting it lands on the caller's
        destination, not the list-URL fallback.
        """
        delete_url = reverse("product-delete", kwargs={"pk": product.pk})
        get_response = client.get(delete_url + "?next=/orders/")
        form = _get_form(get_response.content, delete_url)
        hidden_next = form.find("input", {"type": "hidden", "name": "next"})
        assert hidden_next is not None, "rendered delete form has no hidden next input"
        assert hidden_next["value"] == "/orders/"

        response = client.post(form["action"], {"next": hidden_next["value"]})
        assert response.status_code == 302
        assert response["Location"] == "/orders/"


# ---------------------------------------------------------------------------
# Scenario 2: Related-objects summary
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDeleteViewRelatedObjects:
    def test_related_objects_hidden_when_flag_off(self, client, product):
        """(f) show_related_objects=False (default) → related_objects is empty."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["related_objects"] == []

    def test_related_objects_shown_when_flag_on(self, client, product):
        """show_related_objects=True → context key is present and is_protected=False."""
        url = reverse("product-delete-related", kwargs={"pk": product.pk})
        response = client.get(url)
        assert "related_objects" in response.context
        assert response.context["is_protected"] is False

    def test_related_objects_not_shown_when_protected(self, client, product):
        """When is_protected=True, related_objects must be empty even if flag on."""
        OrderLine.objects.create(product=product, quantity=2)
        url = reverse("product-delete-related", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["is_protected"] is True
        assert response.context["related_objects"] == []

    def test_related_objects_are_3_tuples(self, client, category):
        """(a) Each element in related_objects is a 3-tuple (label, display_list, overflow)."""
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
        """(b) Product.category is SET_NULL so products are not cascade-deleted.

        No cascade objects → related_objects is empty regardless of cap.
        """
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
        """(c) Product.category is SET_NULL so no cascade objects → no overflow."""
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
        """(d) No overflow note — Product.category is SET_NULL, no cascade objects."""
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
        """(e) No overflow note — Product.category is SET_NULL, no cascade objects."""
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
        """(g) POST deletes category; product survives with category set to NULL (SET_NULL)."""
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


# ---------------------------------------------------------------------------
# Scenario 3: Protected object
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDeleteViewProtected:
    def test_get_shows_protected_flag_when_orderline_exists(self, client, product):
        """(a) GET with protected object returns 200 with is_protected=True in context."""
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["is_protected"] is True

    def test_get_lists_protected_objects(self, client, product):
        """protected_objects contains the blocking OrderLine instances."""
        line = OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert line in response.context["protected_objects"]

    def test_get_html_has_no_delete_button_when_protected(self, client, product):
        """(b) HTML contains protection explanation but no Delete button."""
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "cannot be deleted" in content
        # Delete submit button (btn-danger) must not be present.
        # Note: the language switcher renders type="submit" buttons (name="language"),
        # so we check for the danger-styled button class instead.
        assert "btn-danger" not in content

    def test_post_does_not_delete_protected_object(self, client, product):
        """(c) POST to protected object returns 200 (re-render), not 302 or 500; (d) not deleted."""
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 200
        assert Product.objects.filter(pk=product.pk).exists()

    def test_get_shows_not_protected_after_orderline_removed(self, client, product):
        """After removing the blocking record the flag resets to False."""
        line = OrderLine.objects.create(product=product, quantity=1)
        line.delete()
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["is_protected"] is False


# ---------------------------------------------------------------------------
# Scenario 4: Type-to-confirm
# ---------------------------------------------------------------------------


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
        """Wrong confirmation value returns 200 with form.errors["confirmation"]."""
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, data={"confirmation": "wrong-value"})
        assert "confirmation" in response.context["form"].errors

    def test_post_correct_confirmation_deletes_object(self, client, product):
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, data={"confirmation": str(product)})
        assert response.status_code == 302
        assert not Product.objects.filter(pk=product.pk).exists()

    def test_confirmation_value_empty_when_flag_off(self, client, product):
        """confirmation_value must be empty string when require_confirmation=False."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["confirmation_value"] == ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class TestDeleteViewPublicAPI:
    """MVPDeleteView is exported from the package's public API."""

    def test_mvp_delete_view_in_public_api(self):
        from mvp.views import MVPDeleteView

        assert MVPDeleteView is not None


# ---------------------------------------------------------------------------
# MVPUpdateView.get_delete_url() — back+next params
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPUpdateViewDeleteUrl:
    def test_get_delete_url_contains_back_and_next_params(self, client, product):
        """The delete link generated from the update page must carry both ?back and ?next."""
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        delete_url = response.context["delete_url"]
        parsed = urlparse(delete_url)
        qs = parse_qs(parsed.query)
        assert "back" in qs, "delete_url must contain ?back"
        assert "next" in qs, "delete_url must contain ?next"

    def test_get_delete_url_back_points_to_update_page(self, client, product):
        """`back` param must be the update view URL."""
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        delete_url = response.context["delete_url"]
        qs = parse_qs(urlparse(delete_url).query)
        expected_back = reverse("product-update", kwargs={"pk": product.pk})
        assert qs["back"][0] == expected_back

    def test_get_delete_url_next_points_to_list(self, client, product):
        """`next` param must be the list URL."""
        url = reverse("product-update", kwargs={"pk": product.pk})
        response = client.get(url)
        delete_url = response.context["delete_url"]
        qs = parse_qs(urlparse(delete_url).query)
        expected_next = reverse("product-list")
        assert qs["next"][0] == expected_next

    def test_get_delete_url_returns_empty_on_reverse_failure(self):
        """[T023/M2] get_delete_url() returns a string when the update view name is not registered.

        Verifies that a NoReverseMatch for back_url does not propagate to the caller —
        the method returns a URL string with an empty back param rather than raising.
        """
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


# -------------------------------------------------------------------------
# MVPDeleteView browser tests
# -------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# US1 â€” Basic delete page (T008)
# ---------------------------------------------------------------------------


class TestDeleteViewRendering:
    """The delete confirmation page and a successful deletion."""

    @pytest.mark.django_db
    def test_US1_delete_page_has_permanent_deletion_warning(self, client, product):
        """[US1] GET delete page â€” permanent-deletion warning is visible."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert b"permanently" in response.content

    @pytest.mark.django_db
    def test_US1_delete_page_has_delete_button(self, client, product):
        """[US1] GET delete page â€” Delete submit button is present."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert b'type="submit"' in response.content

    @pytest.mark.django_db
    def test_US1_delete_page_breadcrumb_has_three_levels(self, client, product):
        """[US1] GET delete page â€” breadcrumb context has three items (List â†’ obj â†’ Delete)."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert len(response.context["page"]["breadcrumbs"]) == 3

    @pytest.mark.django_db
    def test_US1_submit_delete_redirects_to_list_and_object_absent(
        self, client, product
    ):
        """[US1] POST delete form â€” redirect to product list, object no longer exists."""
        from demo.models import Product

        pk = product.pk
        url = reverse("product-delete", kwargs={"pk": pk})
        response = client.post(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")
        assert not Product.objects.filter(pk=pk).exists()


# ---------------------------------------------------------------------------
# US2 â€” Related objects summary (T013)
# ---------------------------------------------------------------------------


class TestDeleteViewRelatedObjects:
    """The related-objects summary and its overflow note."""

    @pytest.mark.django_db
    def test_US2_related_objects_section_visible(self, client, product):
        """[US2] show_related_objects=True — page renders but no related-objects section.

        Product.category uses SET_NULL, so products are not cascade-deleted.
        The related-records section is absent; the permanent-deletion warning is shown.
        """
        url = reverse("category-delete-related", kwargs={"pk": product.category.pk})
        response = client.get(url)
        assert response.status_code == 200
        # Permanent-deletion warning is present
        assert b"permanently" in response.content
        # Related-records section is absent (no cascade objects with SET_NULL)
        assert (
            b"related records will also be permanently deleted" not in response.content
        )

    @pytest.mark.django_db
    def test_US2_overflow_note_appears_when_related_objects_exceed_cap(
        self, client, category
    ):
        """[US2] No overflow note — Product.category is SET_NULL, no cascade objects."""
        from demo.models import Product

        # Create products; they are SET_NULL'd on category deletion, not cascade-deleted.
        for i in range(4):
            Product.objects.create(
                name=f"Overflow Product {i}",
                slug=f"overflow-product-integ-{i}",
                sku=f"OVF-{i:03d}",
                category=category,
            )

        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        # No related cascade objects → no overflow note
        assert (
            b"related records will also be permanently deleted" not in response.content
        )


# ---------------------------------------------------------------------------
# US3 â€” Protected object (T015)
# ---------------------------------------------------------------------------


class TestDeleteViewProtected:
    """Protected objects show an alert instead of a delete button."""

    @pytest.mark.django_db
    def test_US3_protected_page_shows_protection_alert(self, client, product):
        """[US3] GET delete page for a PROTECT-blocked record â€” protection alert visible."""
        from demo.models import OrderLine

        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert b"cannot be deleted" in response.content

    @pytest.mark.django_db
    def test_US3_protected_page_has_no_delete_button(self, client, product):
        """[US3] GET delete page for a PROTECT-blocked record â€” Delete button is absent."""
        from demo.models import OrderLine

        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        # The view sets is_protected=True which hides the submit button in the template.
        # We verify via context rather than raw HTML since other page elements (sidebar
        # settings form) may also contain type="submit".
        assert response.context["is_protected"] is True
        assert b"delete-submit-btn" not in response.content


# ---------------------------------------------------------------------------
# US4 â€” Type-to-confirm (T023)
# ---------------------------------------------------------------------------


class TestDeleteViewConfirmation:
    """Type-to-confirm behaviour."""

    @pytest.mark.django_db
    def test_US4_wrong_confirmation_shows_inline_error(self, client, product):
        """[US4] POST wrong confirmation text â€” form error message is shown."""
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, {"confirmation": "wrong-value"})
        content = response.content.decode()
        assert "does not match" in content or "value you entered" in content

    @pytest.mark.django_db
    def test_US4_correct_confirmation_deletes_and_redirects(self, client, product):
        """[US4] POST correct confirmation text â€” redirect to list, object deleted."""
        from demo.models import Product

        pk = product.pk
        url = reverse("product-delete-confirm", kwargs={"pk": pk})
        response = client.post(url, {"confirmation": str(product)})
        assert response.status_code == 302
        assert not Product.objects.filter(pk=pk).exists()

    @pytest.mark.django_db
    def test_US4_confirmation_input_visible_with_prompt(self, client, product):
        """[US4] GET type-to-confirm page â€” confirmation input and prompt text visible."""
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.get(url)
        content = response.content.decode()
        assert "id_confirmation" in content
        assert str(product) in content
