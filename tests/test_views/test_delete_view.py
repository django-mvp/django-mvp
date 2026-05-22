"""Tests for MVPDeleteView — all four deletion scenarios."""

from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse

from mvp.forms import DeleteConfirmForm


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
        form = DeleteConfirmForm(data={"confirmation": "correct"}, confirmation_value="correct")
        assert form.is_valid()

    def test_form_invalid_when_confirmation_does_not_match(self):
        """(b) Non-matching confirmation_value → form is invalid."""
        form = DeleteConfirmForm(data={"confirmation": "wrong"}, confirmation_value="correct")
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_invalid_when_confirmation_empty_with_value(self):
        """(c) Empty input with confirmation_value set → invalid (required field)."""
        form = DeleteConfirmForm(data={"confirmation": ""}, confirmation_value="correct")
        assert not form.is_valid()
        assert "confirmation" in form.errors

    def test_form_valid_when_confirmation_value_is_none(self):
        """(d) confirmation_value=None → no match check, any non-empty value is valid."""
        form = DeleteConfirmForm(data={"confirmation": "x"}, confirmation_value=None)
        assert form.is_valid()


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

    def test_page_icon_is_delete(self, client, product):
        """(g) page icon is 'delete' — FR-012 AdminLTE integration."""
        url = reverse("product-delete", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.context["page"]["icon"] == "delete"

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
        """(b) display list is capped at related_objects_max_per_group (3 in demo view)."""
        # Create 5 products; cap is 3 in CategoryDeleteWithRelatedView
        for i in range(5):
            Product.objects.create(
                name=f"Cap Product {i}",
                slug=f"cap-product-{i}",
                category=category,
                description="Test",
                price="1.00",
                sku=f"SKU-CAP-{i}",
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        # Should have one group (Products)
        assert len(related) == 1
        label, display_list, overflow = related[0]
        assert len(display_list) == 3  # capped at 3

    def test_overflow_count_is_correct(self, client, category):
        """(c) overflow count equals total - cap when objects exceed cap."""
        for i in range(5):
            Product.objects.create(
                name=f"Overflow Prod {i}",
                slug=f"overflow-prod-{i}",
                category=category,
                description="Test",
                price="1.00",
                sku=f"SKU-OVF-{i}",
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        _label, _display_list, overflow = related[0]
        assert overflow == 2  # 5 - 3 = 2

    def test_overflow_note_in_html(self, client, category):
        """(d) overflow note appears in rendered HTML when objects exceed cap."""
        for i in range(5):
            Product.objects.create(
                name=f"Html Overflow {i}",
                slug=f"html-overflow-{i}",
                category=category,
                description="Test",
                price="1.00",
                sku=f"SKU-HTML-{i}",
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        assert "and 2 more" in response.content.decode()

    def test_no_overflow_note_when_within_cap(self, client, category):
        """(e) No overflow note when objects <= cap."""
        for i in range(2):
            Product.objects.create(
                name=f"No Overflow {i}",
                slug=f"no-overflow-{i}",
                category=category,
                description="Test",
                price="1.00",
                sku=f"SKU-NOV-{i}",
            )
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.get(url)
        related = response.context["related_objects"]
        _label, _display_list, overflow = related[0]
        assert overflow == 0
        assert "more" not in response.content.decode() or "0 more" not in response.content.decode()

    def test_post_deletes_when_cascade_related_objects_exist(self, client, category):
        """(g) POST deletes correctly when cascade-related objects exist."""
        product_pk = Product.objects.create(
            name="Cascade Delete Me",
            slug="cascade-del-me",
            category=category,
            description="Test",
            price="1.00",
            sku="SKU-CASCADE-ME",
        ).pk
        url = reverse("category-delete-related", kwargs={"pk": category.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Category.objects.filter(pk=category.pk).exists()
        assert not Product.objects.filter(pk=product_pk).exists()


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
        assert 'btn-danger' not in content

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


def test_mvp_delete_view_in_public_api():
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
            "has_list_permission": True,
            "has_detail_permission": True,
            "has_create_permission": True,
            "has_update_permission": True,
            "has_delete_permission": True,
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
        assert isinstance(result, str), "get_delete_url() must return a string, not raise"
        assert "delete" in result, "delete_url should still contain the delete path"
