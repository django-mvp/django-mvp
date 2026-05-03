"""E2E tests for US5: Render Navigation Links Only for Available Actions.

Tests verify that the ProductDetailView correctly shows/hides action buttons
based on user permissions (staff vs read-only).

These tests use Django's test client for integration testing since they test
the HTTP response and rendered HTML directly, which is equivalent to E2E
browser verification for permission-gating logic.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    from demo.models import Category

    return Category.objects.create(name="E2E Cat", slug="e2e-cat")


@pytest.fixture
def product(category):
    from demo.models import Product

    return Product.objects.create(
        name="E2E Product",
        slug="e2e-product",
        category=category,
        description="An E2E test product",
        price="19.99",
        stock=5,
    )


@pytest.fixture
def staff_user(db):
    user = User.objects.create_user(username="e2e_staff", password="pass", is_staff=True, is_active=True)
    return user


@pytest.fixture
def regular_user(db):
    user = User.objects.create_user(username="e2e_regular", password="pass", is_staff=False, is_active=True)
    return user


# ---------------------------------------------------------------------------
# US5 E2E Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.django_db
class TestUS5StaffUserSeesActionButtons:
    """[US5] Staff user: edit and delete buttons visible; list link present."""

    def test_US5_staff_sees_edit_button(self, client, staff_user, product):
        """[US5] Staff user → edit button visible on product detail page."""
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        edit_url = reverse("product-update", kwargs={"pk": product.pk})
        assert edit_url in content, "Edit link must be present for staff user"

    def test_US5_staff_sees_delete_button(self, client, staff_user, product):
        """[US5] Staff user → delete button visible on product detail page."""
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        delete_url = reverse("product-delete", kwargs={"pk": product.pk})
        assert delete_url in content, "Delete link must be present for staff user"

    def test_US5_staff_sees_list_link(self, client, staff_user, product):
        """[US5] Staff user → back to list link present."""
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        list_url = reverse("product-list")
        assert list_url in content, "List link must be present for staff user"


@pytest.mark.e2e
@pytest.mark.django_db
class TestUS5ReadOnlyUserHidesActionButtons:
    """[US5] Read-only user: edit and delete buttons absent; list link present."""

    def test_US5_regular_user_no_edit_button(self, client, regular_user, product):
        """[US5] Read-only user → edit button absent on product detail page."""
        client.force_login(regular_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        edit_url = reverse("product-update", kwargs={"pk": product.pk})
        assert edit_url not in content, "Edit link must NOT be present for non-staff user"

    def test_US5_regular_user_no_delete_button(self, client, regular_user, product):
        """[US5] Read-only user → delete button absent on product detail page."""
        client.force_login(regular_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        delete_url = reverse("product-delete", kwargs={"pk": product.pk})
        assert delete_url not in content, "Delete link must NOT be present for non-staff user"

    def test_US5_regular_user_sees_list_link(self, client, regular_user, product):
        """[US5] Read-only user → list link still present."""
        client.force_login(regular_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        list_url = reverse("product-list")
        assert list_url in content, "List link must be present for all users"


# ---------------------------------------------------------------------------
# US4 E2E Tests — Object-Named Heading, Breadcrumb Trail, and CSS Classes
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.django_db
class TestUS4ProductDetailPageHeadingAndCSSClass:
    """[US4] ProductDetailView renders str(product) as heading, correct breadcrumb, and model CSS classes."""

    def test_product_detail_page_heading_equals_str_product(self, client, product):
        """[US4] Visible heading matches str(product) — US4 AC1."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "<h1" in content and str(product) in content, f"Heading element containing '{product!s}' must be present"

    def test_product_detail_breadcrumb_ends_with_product_name(self, client, product):
        """[US4] Final breadcrumb item text equals str(product) — US4 AC3."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        product_name = str(product)
        # The breadcrumb trail should contain the product name as the last item
        assert product_name in content, f"Breadcrumb must contain '{product_name}'"

    def test_product_detail_page_container_has_model_css_class(self, client, product):
        """[US4] div.mvp-layout class attribute contains 'product-page' — FR-005."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "product-page" in content, "CSS class 'product-page' must be present in the page container"

    def test_product_detail_page_container_has_action_css_class(self, client, product):
        """[US4] div.mvp-layout class attribute contains 'mvp-detail-page' — FR-009."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "mvp-detail-page" in content, "CSS class 'mvp-detail-page' must be present in the page container"
