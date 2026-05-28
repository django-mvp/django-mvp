"""Integration tests for NextURLMixin: redirect verification and form behaviour.

Converted from end-to-end Playwright tests to Django test-client integration tests.

Covers:
  US1 — MVPCreateView: zero-config model create page (T021)
  US2 — Redirected Back to the Right Place (T022, T023)
  US3 — CRUD Action Shorthand Destinations (T035a, T035b)
  US6 — MVPUpdateView: model-aware title and success message (T007-T009)
  US3/US4 — Delete link visibility on update page (T012, T014)
"""

import pytest
from django.urls import reverse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    from demo.models import Category

    return Category.objects.create(name="Form Cat", slug="form-cat-integ")


@pytest.fixture
def product(category):
    from demo.models import Product

    return Product.objects.create(
        name="Edit Product",
        slug="edit-product-integ",
        category=category,
        description="A product for edit integration tests",
        price="9.99",
        stock=5,
    )


def _product_post_data(category, *, name="Created Product", slug="created-product-integ"):
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


# ---------------------------------------------------------------------------
# US1 — MVPCreateView: zero-config model create page (T021)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US1_create_page_title_is_model_aware(client):
    """[US1] GET /products/create/ — page contains 'Create Product'."""
    response = client.get(reverse("product-create"))
    assert b"Create Product" in response.content


@pytest.mark.django_db
def test_US1_success_message_is_title_cased(client, category):
    """[US1] POST valid create form — flash message contains 'Product successfully created.'"""
    from django.contrib.messages import get_messages

    response = client.post(
        reverse("product-create"),
        _product_post_data(category, name="Flash Product", slug="flash-product-integ"),
    )
    assert response.status_code == 302
    # Follow redirect and check message appears in content
    response = client.get(response["Location"])
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert "Product successfully created." in messages


@pytest.mark.django_db
def test_US1_breadcrumb_links_to_list(client):
    """[US1] GET /products/create/ — first breadcrumb href points to /products/."""
    response = client.get(reverse("product-create"))
    breadcrumbs = response.context["page"]["breadcrumbs"]
    assert len(breadcrumbs) >= 1
    assert breadcrumbs[0].get("href") == reverse("product-list")


# ---------------------------------------------------------------------------
# US2 — Redirected Back to the Right Place (T022, T023)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US2_create_with_url_next_redirects_to_url(client, category):
    """[US2] POST with next=/products/ in body — redirect lands at /products/.

    NextURLMixin reads 'next' from POST body on POST requests, not from the
    query string.
    """
    data = _product_post_data(category, name="Next URL Product", slug="next-url-product-integ")
    data["next"] = "/products/"
    response = client.post(reverse("product-create"), data)
    assert response.status_code == 302
    assert response["Location"] == "/products/"


@pytest.mark.django_db
def test_US2_failed_form_preserves_next_url(client, category):
    """[US2] Failed POST re-renders the form with the next destination preserved."""
    url = reverse("product-create") + "?next=/products/"
    # Submit empty data — form validation fails, re-renders the page.
    response = client.post(url, {})
    assert response.status_code == 200
    assert "/products/create/" in response.wsgi_request.path
    # The hidden next input must still carry the destination value.
    assert b'name="next"' in response.content
    assert b"/products/" in response.content


# ---------------------------------------------------------------------------
# US3 — CRUD Action Shorthand Destinations (T035a, T035b)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US3_create_with_list_shorthand_redirects_to_list(client, category):
    """[US3] POST with next='list' in body — redirect lands at the product list URL."""
    data = _product_post_data(category, name="List Redirect Product", slug="list-redirect-integ")
    data["next"] = "list"
    response = client.post(reverse("product-create"), data)
    assert response.status_code == 302
    assert response["Location"] == reverse("product-list")


@pytest.mark.django_db
def test_US3_create_with_detail_shorthand_redirects_to_detail(client, category):
    """[US3] POST with next='detail' in body — redirect lands at the new object's detail URL."""
    from demo.models import Product

    data = _product_post_data(category, name="Detail Redirect Product", slug="detail-redirect-integ")
    data["next"] = "detail"
    response = client.post(reverse("product-create"), data)
    assert response.status_code == 302
    product = Product.objects.get(slug="detail-redirect-integ")
    assert response["Location"] == reverse("product-detail", kwargs={"pk": product.pk})


# ---------------------------------------------------------------------------
# US6 — MVPUpdateView: model-aware title and success message (T007-T009)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US6_update_page_title_is_model_aware(client, product):
    """[US6/T007] GET update URL — page contains 'Update Product'."""
    url = reverse("product-update", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b"Update Product" in response.content


@pytest.mark.django_db
def test_US6_update_success_message_appears(client, product, category):
    """[US6/T008] POST valid update — flash message 'product successfully updated.' appears.

    Note: MVPUpdateView inherits get_success_message() from MVPModelFormBase which
    uses the lowercase verbose_name. MVPCreateView overrides it to title-case; the
    update view does not.
    """
    from django.contrib.messages import get_messages

    url = reverse("product-update", kwargs={"pk": product.pk})
    data = _product_post_data(category, name="Updated Product Name", slug="edit-product-integ")
    response = client.post(url, data)
    assert response.status_code == 302
    response = client.get(response["Location"])
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("successfully updated" in m for m in messages)


@pytest.mark.django_db
def test_US6_update_breadcrumb_has_three_items(client, product):
    """[US6/T009] GET update URL — breadcrumb context has exactly three items."""
    url = reverse("product-update", kwargs={"pk": product.pk})
    response = client.get(url)
    breadcrumbs = response.context["page"]["breadcrumbs"]
    assert len(breadcrumbs) == 3
    # First two items are links; last item is plain text (current page).
    assert breadcrumbs[0].get("href") is not None, "First breadcrumb must be a link (list)"
    assert breadcrumbs[1].get("href") is not None, "Second breadcrumb must be a link (detail)"
    assert breadcrumbs[2].get("href") is None, "Third breadcrumb must be plain text (no link)"


# ---------------------------------------------------------------------------
# US3 — Delete link visible on update page when delete view configured (T012)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US3_update_delete_link_visible_when_configured(client, product):
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
def test_US4_update_delete_link_absent_when_not_configured(client):
    """[US4/T014] GET category update URL (no delete view) — no delete link rendered."""
    from demo.models import Category

    cat = Category.objects.create(name="No Delete Cat", slug="no-delete-cat-integ")
    url = reverse("category-update", kwargs={"pk": cat.pk})
    response = client.get(url)
    # CategoryUpdateView has has_delete_permission=False → get_delete_url() returns ''.
    content = response.content.decode()
    # No anchor pointing to a delete URL should appear.
    import re

    delete_links = re.findall(r'href="[^"]*delete[^"]*"', content)
    assert delete_links == [], (
        f"Expected no delete link on category update page, but found: {delete_links}"
    )

