"""Tests for MVPDeleteView — all four deletion scenarios."""

import pytest
from django.urls import reverse
from urllib.parse import parse_qs, urlparse

from mvp.forms import DeleteConfirmForm


class TestDeleteConfirmForm:
    def test_form_valid_when_field_provided(self):
        form = DeleteConfirmForm(data={"confirmation": "some-value"})
        assert form.is_valid()

    def test_form_invalid_when_field_empty(self):
        form = DeleteConfirmForm(data={"confirmation": ""})
        assert not form.is_valid()
        assert "confirmation" in form.errors


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

from demo.models import Category, OrderLine, Product  # noqa: E402


@pytest.fixture
def category(db):
    return Category.objects.create(name="Test Cat", slug="test-cat-del")


@pytest.fixture
def product(category):
    return Product.objects.create(
        name="Test Product",
        slug="test-product-del",
        category=category,
        description="A test product",
        price="9.99",
        sku="TP-DEL-001",
    )


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

    def test_post_deletes_object(self, client, product):
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Product.objects.filter(pk=product.pk).exists()


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

    def test_next_url_defaults_to_list_when_absent(self, client, product):
        """No ?next param → next_url falls back to the list URL."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["next_url"] == reverse("product-list")


# ---------------------------------------------------------------------------
# Scenario 2: Related-objects summary
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDeleteViewRelatedObjects:
    def test_related_objects_hidden_when_flag_off(self, client, product):
        """show_related_objects=False (default) → related_objects is empty."""
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


# ---------------------------------------------------------------------------
# Scenario 3: Protected object
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDeleteViewProtected:
    def test_get_shows_protected_flag_when_orderline_exists(self, client, product):
        """A product with an OrderLine (PROTECT) must show is_protected=True."""
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["is_protected"] is True

    def test_get_lists_protected_objects(self, client, product):
        """protected_objects contains the blocking OrderLine instances."""
        line = OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert line in response.context["protected_objects"]

    def test_post_does_not_delete_protected_object(self, client, product):
        """POSTing to delete a protected product must NOT delete it."""
        OrderLine.objects.create(product=product, quantity=1)
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.post(url)
        # Re-renders the page (200) instead of redirecting
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
        url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        response = client.post(url, data={"confirmation": "wrong-value"})
        assert response.context["confirmation_error"] != ""

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


def test_mvp_delete_view_in_public_api():
    from mvp.views import MVPDeleteView  # noqa: F401 — must not raise

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
