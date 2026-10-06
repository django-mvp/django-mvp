"""Tests for HtmxMixin and HtmxFormMixin (mvp/views/htmx.py).

Covers all user stories from specs/020-htmx-form-mixin/:

  HtmxMixin  — base context injection (htmx_enabled)
  US1 — Submit a Form Without a Full Page Reload
  US2 — Wire Up HTMX Enhancement with Minimal Configuration
  US3 — Return an HX-Redirect Header on Success
  US4 — Emit HTMX Response Triggers on Success
  US5 — Select the Success Component from the Client Side

Source: mvp/views/htmx.py
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.test import RequestFactory
from django_htmx.middleware import HtmxDetails

from demo.models import Product
from mvp.views import MVPCreateView
from mvp.views.htmx import HtmxFormMixin, HtmxMixin

User = get_user_model()


HTMX_HEADERS = {"HTTP_HX_REQUEST": "true"}

SUCCESS_URL = "/products/"

SUCCESS_COMPONENT = "demo.htmx-product-created"
FORM_COMPONENT = "demo.htmx-product-form"


def has_success_partial(response):
    """True when the response body is the ``demo.htmx-product-created`` partial."""
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.find(attrs={"role": "alert"}) is not None and soup.find("form") is None


def has_form_partial(response):
    """True when the response body is the ``demo.htmx-product-form`` partial."""
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.find("form", id="htmx-demo-form") is not None


class _NoSaveCreateView(MVPCreateView):
    """MVPCreateView stub whose form_valid() skips the actual DB save.

    This isolates HtmxFormMixin unit tests from Product model DB constraints
    (price, category, etc.) that are irrelevant to mixin behavior.
    """

    def form_valid(self, form):
        # Simulate the side-effects the real form_valid would have:
        # set self.object so get_context_data() works, then return a redirect.
        self.object = form.instance
        return HttpResponseRedirect(self.get_success_url())


def make_htmx_view(
    method="POST",
    data=None,
    htmx=True,
    extra_attrs=None,
    kwargs=None,
):
    """Build a concrete HtmxFormMixin + _NoSaveCreateView stub with a fake request.

    Parameters
    ----------
    method:
        HTTP method string (``"POST"`` or ``"GET"``).
    data:
        POST body or GET query-string dict.
    htmx:
        When ``True``, adds ``HX-Request: true`` header so ``request.htmx``
        evaluates to truthy.
    extra_attrs:
        Additional class-level attributes merged into the stub view class.
    kwargs:
        URL kwargs passed to the view instance.

    Returns
    -------
    view instance with ``request``, ``kwargs``, ``args``, and ``object`` set.
    """
    rf = RequestFactory()
    headers = HTMX_HEADERS if htmx else {}

    request = (
        rf.post("/", data=data or {}, **headers)
        if method == "POST"
        else rf.get("/", data=data or {}, **headers)
    )

    request.user = User()
    # Attach HtmxDetails so request.htmx is available (middleware not run in unit tests)
    request.htmx = HtmxDetails(request)

    attrs = {
        "model": Product,
        "fields": ["name"],
        "template_name": "base.html",
        "htmx_success_component": SUCCESS_COMPONENT,
        "htmx_form_component": "demo.htmx-product-form",
        "success_url": SUCCESS_URL,
        "show_list_action": True,
        "show_detail_action": True,
        "show_create_action": True,
        "show_update_action": True,
        "show_delete_action": True,
        **(extra_attrs or {}),
    }
    view_cls = type("StubHtmxView", (HtmxFormMixin, _NoSaveCreateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = kwargs or {}
    view.args = []
    view.object = None
    return view


class TestHtmxContext:
    def test_htmx_mixin_standalone_injects_htmx_enabled(self):
        from django.views.generic import TemplateView

        rf = RequestFactory()
        request = rf.get("/")
        request.user = User()

        view_cls = type(
            "StubMixinView", (HtmxMixin, TemplateView), {"template_name": "base.html"}
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        assert context.get("htmx_enabled") is True


class TestHtmxFormResponses:
    @pytest.mark.django_db
    def test_form_valid_htmx_returns_success_partial(self):
        view = make_htmx_view(data={"name": "Widget A"})
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget A"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        from django.http import HttpResponseRedirect

        assert isinstance(response, HttpResponse)
        assert not isinstance(response, HttpResponseRedirect)
        assert response.status_code == 200
        assert has_success_partial(response)

    @pytest.mark.django_db
    def test_form_invalid_htmx_returns_form_partial_at_200(self):
        view = make_htmx_view(data={"name": ""})  # name is required
        form_cls = view.get_form_class()
        form = form_cls(data={"name": ""})
        assert not form.is_valid()

        response = view.form_invalid(form)

        assert isinstance(response, HttpResponse)
        assert response.status_code == 200
        assert has_form_partial(response)

    @pytest.mark.django_db
    def test_form_valid_non_htmx_redirects(self):
        view = make_htmx_view(data={"name": "Widget B"}, htmx=False)
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget B"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        from django.http import HttpResponseRedirect

        assert isinstance(response, HttpResponseRedirect)

    @pytest.mark.django_db
    def test_form_invalid_non_htmx_full_page(self):
        view = make_htmx_view(data={"name": ""}, htmx=False)
        form_cls = view.get_form_class()
        form = form_cls(data={"name": ""})
        assert not form.is_valid()

        response = view.form_invalid(form)

        from django.http import HttpResponseRedirect

        # Base view returns a TemplateResponse (not a redirect, not an htmx partial)
        assert isinstance(response, HttpResponse)
        assert not isinstance(response, HttpResponseRedirect)
        # The response should be a full-page TemplateResponse, not a short partial
        # (TemplateResponse has a .template_name attribute)
        assert hasattr(response, "template_name")

    @pytest.mark.django_db
    def test_messages_drained_on_htmx_success_path(self):
        from django.contrib.messages import get_messages
        from django.contrib.messages.storage.cookie import CookieStorage

        view = make_htmx_view(
            data={"name": "Widget C"},
            extra_attrs={"success_message": "Created!"},
        )
        # Use CookieStorage (no session required) so messages can be queued/drained
        view.request._messages = CookieStorage(view.request)

        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget C"})
        assert form.is_valid(), form.errors

        view.form_valid(form)

        remaining = list(get_messages(view.request))
        assert len(remaining) == 0, f"Expected empty queue; got {remaining}"


class TestHtmxComponentConfiguration:
    @pytest.mark.django_db
    def test_missing_success_component_raises_improperly_configured(self):
        from django.core.exceptions import ImproperlyConfigured

        view = make_htmx_view(
            data={"name": "Widget D"},
            extra_attrs={
                "htmx_success_component": None,
                "htmx_redirect_on_success": False,
            },
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget D"})
        assert form.is_valid(), form.errors

        with pytest.raises(ImproperlyConfigured, match="htmx_success_component"):
            view.form_valid(form)

    @pytest.mark.django_db
    def test_missing_form_component_raises_improperly_configured(self):
        from django.core.exceptions import ImproperlyConfigured

        view = make_htmx_view(
            data={"name": ""},
            extra_attrs={"htmx_form_component": None},
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": ""})
        assert not form.is_valid()

        with pytest.raises(ImproperlyConfigured, match="htmx_form_component"):
            view.form_invalid(form)

    @pytest.mark.django_db
    def test_get_htmx_success_component_override_used(self):
        view = make_htmx_view(
            data={"name": "Widget E"},
            extra_attrs={"htmx_success_component": "demo.htmx-product-created"},
        )
        view.get_htmx_success_component = lambda: FORM_COMPONENT

        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget E"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert has_form_partial(response)
        assert not has_success_partial(response)

    @pytest.mark.django_db
    def test_get_htmx_form_component_override_used(self):
        view = make_htmx_view(data={"name": ""})
        view.get_htmx_form_component = lambda: SUCCESS_COMPONENT

        form_cls = view.get_form_class()
        form = form_cls(data={"name": ""})
        assert not form.is_valid()

        response = view.form_invalid(form)

        assert has_success_partial(response)
        assert not has_form_partial(response)


class DefaultFormComponentView(HtmxFormMixin, MVPCreateView):
    """A view that leaves ``htmx_form_component`` at the mixin's default."""

    model = Product
    fields = ["name"]
    template_name = "base.html"
    htmx_success_component = "demo.htmx-product-created"
    success_url = SUCCESS_URL


class TestHtmxFormDefaultComponent:
    @pytest.mark.django_db
    def test_invalid_htmx_post_without_a_form_component_returns_the_form_partial(self):
        request = RequestFactory().post("/", data={"name": ""}, **HTMX_HEADERS)
        request.user = User()
        request.htmx = HtmxDetails(request)

        response = DefaultFormComponentView.as_view()(request)

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")
        assert soup.find("form") is not None


ALLOWLIST = (
    ("list", FORM_COMPONENT),
    ("detail", "demo.htmx-product-detail"),
)


class TestHtmxComponentAllowlist:
    @pytest.mark.django_db
    def test_x_success_component_header_resolves_via_allowlist(self):
        view = make_htmx_view(
            data={"name": "Widget X"},
            extra_attrs={
                "htmx_success_components": ALLOWLIST,
                "htmx_success_component": SUCCESS_COMPONENT,
            },
        )
        # Simulate the client sending X-Success-Component: list
        view.request.META["HTTP_X_SUCCESS_COMPONENT"] = "list"

        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget X"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert has_form_partial(response)
        assert not has_success_partial(response)

    @pytest.mark.django_db
    def test_x_success_component_unknown_alias_falls_through_to_default(self):
        view = make_htmx_view(
            data={"name": "Widget Y"},
            extra_attrs={
                "htmx_success_components": ALLOWLIST,
                "htmx_success_component": SUCCESS_COMPONENT,
            },
        )
        view.request.META["HTTP_X_SUCCESS_COMPONENT"] = "unknown-alias"

        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget Y"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert has_success_partial(response)
        assert not has_form_partial(response)

    @pytest.mark.django_db
    def test_x_success_component_header_ignored_when_allowlist_empty(self):
        view = make_htmx_view(
            data={"name": "Widget Z"},
            extra_attrs={"htmx_success_component": "demo.htmx-product-created"},
        )
        # No htmx_success_components defined; header should be ignored.
        view.request.META["HTTP_X_SUCCESS_COMPONENT"] = "list"

        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget Z"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert has_success_partial(response)
        assert not has_form_partial(response)

    @pytest.mark.django_db
    def test_x_success_component_no_header_uses_server_default(self):
        view = make_htmx_view(
            data={"name": "Widget Q"},
            extra_attrs={
                "htmx_success_components": ALLOWLIST,
                "htmx_success_component": SUCCESS_COMPONENT,
            },
        )
        # No X-Success-Component header — alias will be empty string after strip().

        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget Q"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert has_success_partial(response)
        assert not has_form_partial(response)


class TestHtmxRedirect:
    @pytest.mark.django_db
    def test_htmx_redirect_on_success_returns_client_redirect(self):
        from django_htmx.http import HttpResponseClientRedirect

        view = make_htmx_view(
            data={"name": "Widget F"},
            extra_attrs={"htmx_redirect_on_success": True},
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget F"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert isinstance(response, HttpResponseClientRedirect)
        assert response["HX-Redirect"] == view.get_success_url()


class TestHtmxTriggerHeaders:
    @pytest.mark.django_db
    def test_htmx_trigger_string_adds_hx_trigger_header(self):
        view = make_htmx_view(
            data={"name": "Widget H"},
            extra_attrs={"htmx_trigger": "itemCreated"},
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget H"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert "HX-Trigger" in response
        assert "itemCreated" in response["HX-Trigger"]

    @pytest.mark.django_db
    def test_htmx_trigger_dict_adds_events_for_each_key(self):
        view = make_htmx_view(
            data={"name": "Widget I"},
            extra_attrs={"htmx_trigger": {"eventA": None, "eventB": {"id": 1}}},
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget I"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        trigger_header = response.get("HX-Trigger", "")
        assert "eventA" in trigger_header
        assert "eventB" in trigger_header

    @pytest.mark.django_db
    def test_htmx_trigger_after_settle_uses_correct_header(self):
        view = make_htmx_view(
            data={"name": "Widget J"},
            extra_attrs={
                "htmx_trigger": "itemCreated",
                "htmx_trigger_after": "settle",
            },
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget J"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert "HX-Trigger-After-Settle" in response
        assert "HX-Trigger" not in response or response.get("HX-Trigger") is None

    @pytest.mark.django_db
    def test_htmx_trigger_after_swap_uses_correct_header(self):
        view = make_htmx_view(
            data={"name": "Widget K"},
            extra_attrs={
                "htmx_trigger": "itemCreated",
                "htmx_trigger_after": "swap",
            },
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget K"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert "HX-Trigger-After-Swap" in response

    @pytest.mark.django_db
    def test_htmx_trigger_none_adds_no_trigger_header(self):
        view = make_htmx_view(
            data={"name": "Widget L"},
            extra_attrs={"htmx_trigger": None},
        )
        form_cls = view.get_form_class()
        form = form_cls(data={"name": "Widget L"})
        assert form.is_valid(), form.errors

        response = view.form_valid(form)

        assert "HX-Trigger" not in response
        assert "HX-Trigger-After-Settle" not in response
        assert "HX-Trigger-After-Swap" not in response
