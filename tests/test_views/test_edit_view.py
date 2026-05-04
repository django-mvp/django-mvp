"""Tests for NextURLMixin and the form view redirect priority chain.

Covers all five user stories defined in specs/008-safe-post-submit-redirect/:

  US1 — Chain Form Views with a URL Destination
  US2 — Redirected Back to the Right Place (E2E in test_edit_view_e2e.py)
  US3 — CRUD Action Shorthand Destinations
  US4 — Open-Redirect Protection (logging + rejection)
  US5 — Graceful Fallback (success_url → resoluve_crud_url("list"))

Source: mvp/views/edit.py
"""

import logging

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.views.generic import TemplateView

from demo.models import Category, Product
from mvp.views.edit import MVPCreateView, MVPFormView, NextURLMixin

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
    request = rf.post("/", data=params or {}) if method == "POST" else rf.get("/", data=params or {})

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
    request = rf.post("/", data=params or {}) if method == "POST" else rf.get("/", data=params or {})
    request.user = User()

    attrs = {
        "model": Product,
        "fields": ["name"],
        "template_name": "form_view.html",
        "has_list_permission": True,
        "has_detail_permission": True,
        "has_create_permission": True,
        "has_update_permission": True,
        "has_delete_permission": True,
        **(extra_attrs or {}),
    }
    view_cls = type("StubCreateView", (MVPCreateView,), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = kwargs or {}
    view.args = []
    view.object = None
    return view


# ---------------------------------------------------------------------------
# US4 — Open-Redirect Protection
# ---------------------------------------------------------------------------


class TestUS4LoggingDebugOn:
    """[US4] logger.warning is emitted for rejected next values when DEBUG=True."""

    @override_settings(DEBUG=True)
    def test_external_url_logs_warning(self, caplog):
        """[US4] next=https://evil.com/ logs a warning."""
        view = make_next_url_view(method="POST", params={"next": "https://evil.com/"})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            result = view.get_next_url()
        assert result is None
        assert any("https://evil.com/" in r.message for r in caplog.records)

    @override_settings(DEBUG=True)
    def test_javascript_scheme_logs_warning(self, caplog):
        """[US4] next=javascript:alert(1) logs a warning."""
        view = make_next_url_view(method="POST", params={"next": "javascript:alert(1)"})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            view.get_next_url()
        assert any("javascript:alert(1)" in r.message for r in caplog.records)

    @override_settings(DEBUG=True)
    def test_protocol_relative_url_logs_warning(self, caplog):
        """[US4] next=//evil.com/path logs a warning."""
        view = make_next_url_view(method="POST", params={"next": "//evil.com/path"})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            view.get_next_url()
        assert any("//evil.com/path" in r.message for r in caplog.records)

    @override_settings(DEBUG=True)
    def test_absent_next_no_log(self, caplog):
        """[US4] No next parameter emits no log even when DEBUG=True."""
        view = make_next_url_view(method="POST", params={})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            view.get_next_url()
        assert caplog.records == []

    @override_settings(DEBUG=True)
    def test_empty_string_next_no_log(self, caplog):
        """[US4] Empty-string next emits no log even when DEBUG=True."""
        view = make_next_url_view(method="POST", params={"next": ""})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            view.get_next_url()
        assert caplog.records == []

    @override_settings(DEBUG=True)
    def test_crud_shorthand_no_log(self, caplog):
        """[US4] next=list (recognized CRUD shorthand) emits no warning and resolves to list URL.

        Shorthands are resolved by MVPFormBase before URL validation — they are
        not unsafe URLs, they are valid inputs resolved directly.
        """
        from django.urls import reverse

        view = make_create_view(method="POST", params={"next": "list"})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            result = view.get_next_url()
        assert result == reverse("product-list")
        assert caplog.records == []


class TestUS4LoggingDebugOff:
    """[US4] logger.warning is NOT emitted when DEBUG=False."""

    @override_settings(DEBUG=False)
    def test_external_url_no_log_in_production(self, caplog):
        """[US4] next=https://evil.com/ does not log when DEBUG=False."""
        view = make_next_url_view(method="POST", params={"next": "https://evil.com/"})
        with caplog.at_level(logging.WARNING, logger=EDIT_VIEW_LOGGER):
            result = view.get_next_url()
        assert result is None
        assert caplog.records == []


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
        view_cls = type("StubView", (NextURLMixin, TemplateView), {"template_name": "base.html"})
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

    def test_post_reads_body_not_query_string(self):
        """[FR-001a] POST reads POST body, not query string."""
        rf = RequestFactory()
        request = rf.post("/?next=/from-qs/", data={"next": "/from-body/"})
        view_cls = type("StubView", (NextURLMixin, TemplateView), {"template_name": "base.html"})
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


class TestGetSuccessMessage:
    """[US2] MVPModelFormBase.get_success_message() interpolation contract tests."""

    def test_verbose_name_only_resolves(self):
        """[T-FM-001] %(verbose_name)s with empty cleaned_data → model verbose_name."""
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"success_message": "%(verbose_name)s created."},
        )
        result = view.get_success_message({})
        assert result == f"{Product._meta.verbose_name} created."

    def test_missing_field_placeholder_substitutes_empty_string(self):
        """[T-FM-002] %(name)s with empty cleaned_data → '' substituted, no KeyError raised."""
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"success_message": "%(verbose_name)s %(name)s deleted."},
        )
        result = view.get_success_message({})
        assert result == f"{Product._meta.verbose_name}  deleted."

    def test_field_value_and_verbose_name_both_resolve(self):
        """[T-FM-003] %(verbose_name)s + %(name)s both resolve when name present in cleaned_data."""
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"success_message": "%(verbose_name)s %(name)s updated."},
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

        # has_list_permission=False → resolve_crud_url("list") returns None; object=None → ImproperlyConfigured
        view = make_create_view(
            method="POST",
            params={},
            extra_attrs={"has_list_permission": False},
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
            extra_attrs={"has_list_permission": False},
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
            extra_attrs={"has_list_permission": False},
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
        view = make_form_view(extra_attrs={"success_message": "%(verbose_name)s saved."})
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
