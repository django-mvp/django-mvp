"""Integration tests for MVPDeleteView â€” all four deletion scenarios.

Converted from end-to-end Playwright tests to Django test-client integration tests.

Covers:
  US1 â€” Basic delete: warning present, Delete button present, redirect to list
  US2 â€” Related objects: grouped summary visible, overflow note present
  US3 â€” Protected object: Delete button absent, blocking message present
  US4 â€” Type-to-confirm: inline error on wrong value, redirect on correct value
"""

import pytest
from django.urls import reverse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    from demo.models import Category

    return Category.objects.create(name="Del Cat", slug="del-cat-integ")


@pytest.fixture
def product(category):
    from demo.models import Product

    return Product.objects.create(
        name="Delete Product",
        slug="delete-product-integ",
        category=category,
        description="A product for delete integration tests",
        price="9.99",
        stock=5,
    )


# ---------------------------------------------------------------------------
# US1 â€” Basic delete page (T008)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US1_delete_page_has_permanent_deletion_warning(client, product):
    """[US1] GET delete page â€” permanent-deletion warning is visible."""
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b"permanently" in response.content


@pytest.mark.django_db
def test_US1_delete_page_has_delete_button(client, product):
    """[US1] GET delete page â€” Delete submit button is present."""
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b'type="submit"' in response.content


@pytest.mark.django_db
def test_US1_delete_page_breadcrumb_has_three_levels(client, product):
    """[US1] GET delete page â€” breadcrumb context has three items (List â†’ obj â†’ Delete)."""
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert len(response.context["page"]["breadcrumbs"]) == 3


@pytest.mark.django_db
def test_US1_submit_delete_redirects_to_list_and_object_absent(client, product):
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


@pytest.mark.django_db
def test_US2_related_objects_section_visible(client, product):
    """[US2] show_related_objects=True — related-items section is visible.

    Uses the Category delete view (products CASCADE on category deletion).
    The 'product' fixture ensures the category has at least one related product.
    """
    url = reverse("category-delete-related", kwargs={"pk": product.category.pk})
    response = client.get(url)
    assert b"related records will also be permanently deleted" in response.content


@pytest.mark.django_db
def test_US2_overflow_note_appears_when_related_objects_exceed_cap(client, category):
    """[US2] Overflow note appears when related objects exceed related_objects_max_per_group."""
    from demo.models import Product

    # CategoryDeleteWithRelatedView has related_objects_max_per_group=3; create 4.
    for i in range(4):
        Product.objects.create(
            name=f"Overflow Product {i}",
            slug=f"overflow-product-integ-{i}",
            sku=f"OVF-{i:03d}",
            category=category,
            description="Overflow test",
            price="1.00",
        )

    url = reverse("category-delete-related", kwargs={"pk": category.pk})
    response = client.get(url)
    assert b"more" in response.content


# ---------------------------------------------------------------------------
# US3 â€” Protected object (T015)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US3_protected_page_shows_protection_alert(client, product):
    """[US3] GET delete page for a PROTECT-blocked record â€” protection alert visible."""
    from demo.models import OrderLine

    OrderLine.objects.create(product=product, quantity=1)
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b"cannot be deleted" in response.content


@pytest.mark.django_db
def test_US3_protected_page_has_no_delete_button(client, product):
    """[US3] GET delete page for a PROTECT-blocked record â€” Delete button is absent."""
    from demo.models import OrderLine

    OrderLine.objects.create(product=product, quantity=1)
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    # The view sets is_protected=True which hides the submit button in the template.
    # We verify via context rather than raw HTML since other page elements (sidebar
    # settings form) may also contain type="submit".
    assert response.context["is_protected"] is True
    assert b'delete-submit-btn' not in response.content


# ---------------------------------------------------------------------------
# US4 â€” Type-to-confirm (T023)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US4_wrong_confirmation_shows_inline_error(client, product):
    """[US4] POST wrong confirmation text â€” form error message is shown."""
    url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
    response = client.post(url, {"confirmation": "wrong-value"})
    content = response.content.decode()
    assert "does not match" in content or "value you entered" in content


@pytest.mark.django_db
def test_US4_correct_confirmation_deletes_and_redirects(client, product):
    """[US4] POST correct confirmation text â€” redirect to list, object deleted."""
    from demo.models import Product

    pk = product.pk
    url = reverse("product-delete-confirm", kwargs={"pk": pk})
    response = client.post(url, {"confirmation": str(product)})
    assert response.status_code == 302
    assert not Product.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_US4_confirmation_input_visible_with_prompt(client, product):
    """[US4] GET type-to-confirm page â€” confirmation input and prompt text visible."""
    url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
    response = client.get(url)
    content = response.content.decode()
    assert "id_confirmation" in content
    assert str(product) in content

