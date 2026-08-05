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
from django.urls import reverse

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


# ---------------------------------------------------------------------------
# T016 — valid submission persists both parts, exactly once, redirect (FR-012)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineValidSubmission:
    """Both parts persist on a valid submission, the parent saves exactly
    once, and the redirect follows the inherited ``get_success_url`` chain
    (FR-012), including on the create path with an object-dependent URL."""

    def test_update_valid_submission_persists_parent_and_rows(self):
        product = ProductFactory(name="Original")
        existing = OrderLineFactory(product=product, quantity=1)
        view_cls = _inline_update_view_class(success_url="list")
        data = {
            "name": "Updated Name",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": str(existing.pk),
            "form-0-quantity": "5",
            "form-1-quantity": "7",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": product.pk}
        )

        assert response.status_code == 302
        assert response["Location"] == reverse("product-list")
        product.refresh_from_db()
        assert product.name == "Updated Name"
        assert set(product.order_lines.values_list("quantity", flat=True)) == {5, 7}

    def test_parent_is_saved_exactly_once(self, monkeypatch):
        product = ProductFactory(name="Original")
        save_calls = []
        original_save = Product.save

        def counting_save(self, *args, **kwargs):
            save_calls.append(1)
            return original_save(self, *args, **kwargs)

        monkeypatch.setattr(Product, "save", counting_save)
        view_cls = _inline_update_view_class(success_url="list")
        data = {
            "name": "Counted Once",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "3",
        }

        _dispatch(view_cls, method="POST", data=data, view_kwargs={"pk": product.pk})

        assert len(save_calls) == 1

    def test_create_with_detail_shorthand_redirects_to_new_object(self):
        view_cls = _inline_create_view_class(success_url="detail")
        data = {
            "name": "Brand New",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "3",
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 302
        new_product = Product.objects.get(name="Brand New")
        assert response["Location"] == reverse(
            "product-detail", kwargs={"pk": new_product.pk}
        )
        assert list(new_product.order_lines.values_list("quantity", flat=True)) == [3]


# ---------------------------------------------------------------------------
# T017 — a failure partway through saving rows rolls back the parent too
# ---------------------------------------------------------------------------


class _SimulatedRowFailure(Exception):
    """Raised by a monkeypatched ``OrderLine.save`` to force a partial-save."""


@pytest.mark.django_db
class TestInlineTransactionAtomicity:
    """A failure while saving rows leaves the parent's changes unpersisted
    (FR-011, SC-006), and no success message survives the rollback."""

    def test_row_save_failure_rolls_back_parent_and_queues_no_message(
        self, monkeypatch
    ):
        product = ProductFactory(name="Original")
        original_save = OrderLine.save

        def failing_save(self, *args, **kwargs):
            if self.quantity == 999:
                raise _SimulatedRowFailure("boom")
            return original_save(self, *args, **kwargs)

        monkeypatch.setattr(OrderLine, "save", failing_save)
        view_cls = _inline_update_view_class(success_url="list")
        data = {
            "name": "Changed Name",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "5",
            "form-1-quantity": "999",
        }
        request = _build_request(method="POST", data=data)

        with pytest.raises(_SimulatedRowFailure):
            view_cls.as_view()(request, pk=product.pk)

        product.refresh_from_db()
        assert product.name == "Original"
        assert not OrderLine.objects.filter(quantity=5).exists()
        assert not OrderLine.objects.filter(quantity=999).exists()
        assert list(request._messages) == []


# ---------------------------------------------------------------------------
# T018 — invalid parent form with valid rows: nothing persists, both
# parts re-render with submitted values (FR-013)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineInvalidParentForm:
    """An invalid parent form with a valid row persists nothing, and the page
    re-renders with every submitted value present in both parts (FR-013)."""

    def test_invalid_parent_persists_nothing_and_preserves_both_parts(self):
        view_cls = _inline_create_view_class(success_url="list")
        too_long_name = "x" * 250  # Product.name has max_length=200
        data = {
            "name": too_long_name,
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "4",
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 200
        html = _rendered_html(response)
        assert _field_value(html, "name") == too_long_name
        assert _field_value(html, "form-0-quantity") == "4"
        assert Product.objects.count() == 0
        assert OrderLine.objects.count() == 0


# ---------------------------------------------------------------------------
# T019 - the mirror case: valid parent form, invalid row (FR-010, FR-013)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineInvalidRow:
    """A valid parent form with an invalid row persists nothing; the page
    re-renders with every submitted value present in both parts, and the row
    carries its error (FR-010, FR-013). This is the branch ``form_valid``
    adds over Django's default: without it, the formset is never checked."""

    def test_invalid_row_persists_nothing_and_carries_its_error(self):
        view_cls = _inline_create_view_class(success_url="list")
        data = {
            "name": "Valid Parent Name",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "-1",  # PositiveIntegerField rejects negatives
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 200
        html = _rendered_html(response)
        assert _field_value(html, "name") == "Valid Parent Name"
        assert _field_value(html, "form-0-quantity") == "-1"
        assert "greater than or equal to 0" in html
        assert Product.objects.count() == 0
        assert OrderLine.objects.count() == 0


# ---------------------------------------------------------------------------
# T020 - create case: a new parent is created and its rows attached to it
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineCreateAttachesRows:
    """Given no parent record, a create submission carrying rows creates a
    new parent and attaches its rows to it (FR-014, US3 scenario 5).
    ``BaseInlineFormSet.save_new`` reads ``formset.instance`` at save time, so
    the assignment must happen after the parent is saved."""

    def test_create_attaches_all_new_rows_to_the_newly_created_parent(self):
        view_cls = _inline_create_view_class(success_url="list")
        data = {
            "name": "Fresh Product",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "2",
            "form-1-quantity": "6",
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 302
        new_product = Product.objects.get(name="Fresh Product")
        assert list(
            new_product.order_lines.order_by("quantity").values_list(
                "quantity", flat=True
            )
        ) == [2, 6]
        assert all(
            line.product_id == new_product.pk for line in new_product.order_lines.all()
        )


# ---------------------------------------------------------------------------
# T021 - inline_max_num is a real cap, and absolute_max stays at Django's
# default so a within-cap submission is not silently truncated
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineMaxNumCap:
    """``inline_max_num`` is enforced on the server, not only in the browser.
    Equally important: a submission that is within the cap once removals are
    counted is accepted - this is what pins ``absolute_max`` to Django's
    default rather than a derivation from the cap."""

    def test_exceeding_max_num_is_rejected_with_set_level_error(self):
        view_cls = _inline_create_view_class(success_url="list", inline_max_num=3)
        data = {
            "name": "Capped Product",
            "form-TOTAL_FORMS": "4",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-quantity": "1",
            "form-1-quantity": "2",
            "form-2-quantity": "3",
            "form-3-quantity": "4",
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 200
        html = _rendered_html(response)
        assert "Please submit at most 3 forms." in html
        assert Product.objects.count() == 0
        assert OrderLine.objects.count() == 0

    def test_within_cap_after_removals_is_accepted(self):
        product = ProductFactory(name="Existing")
        existing = OrderLineFactory(product=product, quantity=1)
        view_cls = _inline_update_view_class(success_url="list", inline_max_num=3)
        # 5 forms submitted (1 existing + 4 new), 2 of the new rows marked
        # DELETE -> 3 forms remain, exactly at the cap.
        data = {
            "name": "Existing",
            "form-TOTAL_FORMS": "5",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": str(existing.pk),
            "form-0-quantity": "1",
            "form-1-quantity": "2",
            "form-2-quantity": "3",
            "form-2-DELETE": "on",
            "form-3-quantity": "4",
            "form-4-quantity": "5",
            "form-4-DELETE": "on",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": product.pk}
        )

        assert response.status_code == 302
        assert set(product.order_lines.values_list("quantity", flat=True)) == {1, 2, 4}
