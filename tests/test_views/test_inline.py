"""Tests for InlineFormsetMixin, MVPInlineCreateView and MVPInlineUpdateView.

Covers User Story 3 (specs/024-formset-pages): a parent record and its related
rows validated, saved and rendered together on one page.

Source: mvp/views/inline.py
Contract: specs/024-formset-pages/contracts/inline-view.md
"""

import re

import pytest
from bs4 import BeautifulSoup
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from demo.models import OrderLine, Product
from mvp.views.inline import InlineFormsetMixin
from mvp.views.edit import MVPCreateView, MVPUpdateView
from tests.factories import OrderLineFactory, ProductFactory

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _build_request(method="GET", data=None):
    """Return a request carrying working session and messages storage.

    ``as_view()`` is called directly (no middleware runs), but ``form_valid``
    needs ``request._messages`` to queue the success flash, so session and
    messages middleware are applied to the request by hand.
    """
    rf = RequestFactory()
    request = rf.post("/", data=data or {}) if method == "POST" else rf.get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    MessageMiddleware(lambda r: None).process_request(request)
    return request


def _dispatch(view_cls, method="GET", data=None, view_kwargs=None):
    """Build a request and run it through ``view_cls`` via ``as_view()``."""
    request = _build_request(method=method, data=data)
    response = view_cls.as_view()(request, **(view_kwargs or {}))
    return request, response


def _rendered_html(response):
    """Render a ``TemplateResponse`` and return its decoded content."""
    response.render()
    return response.content.decode()


def _field_value(html, field_name):
    """Return the ``value`` of the first field named ``field_name``, or None."""
    soup = BeautifulSoup(html, "html.parser")
    field = soup.find(attrs={"name": field_name})
    if field is None:
        return None
    if field.name == "textarea":
        return field.text
    return field.get("value")


def _all_field_values(html, name_pattern):
    """Return the ``value`` attrs of every field whose name matches the pattern."""
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(name_pattern)
    return [tag.get("value") for tag in soup.find_all(attrs={"name": pattern})]


def _inline_update_view_class(**attrs):
    base_attrs = {
        "model": Product,
        "fields": ["name"],
        "inline_model": OrderLine,
        "inline_fields": ["quantity"],
        "template_name": "form_view.html",
        "show_detail_action": True,
        "show_list_action": True,
        **attrs,
    }
    return type("StubInlineUpdateView", (InlineFormsetMixin, MVPUpdateView), base_attrs)


def _inline_create_view_class(**attrs):
    base_attrs = {
        "model": Product,
        "fields": ["name"],
        "inline_model": OrderLine,
        "inline_fields": ["quantity"],
        "template_name": "form_view.html",
        "show_detail_action": True,
        "show_list_action": True,
        **attrs,
    }
    return type("StubInlineCreateView", (InlineFormsetMixin, MVPCreateView), base_attrs)


# ---------------------------------------------------------------------------
# T014 — inline_model guard
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineModelGuard:
    """A view with no ``inline_model`` raises ``ImproperlyConfigured`` naming it."""

    def test_missing_inline_model_raises_improperly_configured(self):
        product = ProductFactory()
        view_cls = _inline_update_view_class(inline_model=None)

        with pytest.raises(ImproperlyConfigured, match="inline_model"):
            _dispatch(view_cls, method="GET", view_kwargs={"pk": product.pk})


# ---------------------------------------------------------------------------
# T015 — GET renders the parent form, existing rows and inline_extra blanks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineGetRendering:
    """GET renders the parent's form and one row per existing related record,
    plus ``inline_extra`` blank rows (FR-009)."""

    def test_get_renders_parent_form_and_existing_rows_plus_extra(self):
        product = ProductFactory(name="Widget")
        OrderLineFactory(product=product, quantity=2)
        OrderLineFactory(product=product, quantity=5)
        view_cls = _inline_update_view_class()

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": product.pk})
        html = _rendered_html(response)

        assert _field_value(html, "name") == "Widget"
        quantities = _all_field_values(html, r"^form-\d+-quantity$")
        assert quantities.count("2") == 1
        assert quantities.count("5") == 1
        # 2 existing rows + 1 inline_extra blank row (default)
        assert len(quantities) == 3
        assert _field_value(html, "form-TOTAL_FORMS") == "3"
