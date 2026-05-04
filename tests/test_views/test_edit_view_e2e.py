"""E2E tests for NextURLMixin: full round-trip redirect verification.

Covers:
  US2 — Redirected Back to the Right Place (T022, T023)
  US3 — CRUD Action Shorthand Destinations E2E (T035a, T035b)

These tests require:
  - pytest-playwright installed and browsers downloaded (``playwright install``)
  - The ``e2e`` marker is registered in pytest configuration

Run with: ``pytest tests/test_views/test_edit_view_e2e.py -m e2e``
Skip in CI without playwright: ``pytest -m "not e2e"``
"""

import pytest

pytest_playwright = pytest.importorskip("playwright", reason="playwright not installed — skip e2e tests")

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    from demo.models import Category

    return Category.objects.create(name="E2E Form Cat", slug="e2e-form-cat")


@pytest.fixture
def product(category):
    from demo.models import Product

    return Product.objects.create(
        name="E2E Edit Product",
        slug="e2e-edit-product",
        category=category,
        description="A product for E2E edit tests",
        price="9.99",
        stock=5,
    )


def _fill_product_form(page, category, *, name="E2E Created Product", slug="e2e-created-product"):
    """Fill in the product creation form fields."""
    page.fill("input[name=name]", name)
    page.fill("input[name=slug]", slug)
    page.fill("textarea[name=description]", "E2E test description")
    page.fill("input[name=price]", "12.99")
    page.fill("input[name=stock]", "3")
    # Select the category in the <select> element
    page.select_option("select[name=category]", str(category.pk))


# ---------------------------------------------------------------------------
# US2 — Redirected Back to the Right Place
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US2_create_with_url_next_redirects_to_url(page, live_server, category):
    """[US2] Navigate to create URL with ?next=/products/, submit form, land at /products/.

    Verifies the full create→redirect round-trip when a URL destination is embedded
    in the query string.
    """

    create_url = f"{live_server.url}/products/create/?next=/products/"
    page.goto(create_url)
    _fill_product_form(page, category)
    page.press("input[name=name]", "Enter")  # submit via Enter (no button shorthand)
    page.wait_for_load_state("networkidle")
    assert page.url.endswith("/products/"), f"Expected /products/, got {page.url}"


@pytest.mark.django_db(transaction=True)
def test_US2_failed_form_preserves_next_url(page, live_server, category):
    """[US2] Failed form submission re-renders the form with next_url still present.

    Verifies that the destination is preserved for retry when validation fails.
    """
    create_url = f"{live_server.url}/products/create/?next=/products/"
    page.goto(create_url)
    # Deliberately leave required fields empty and submit — form validation fails
    page.click("button[type=submit][value=list]")
    page.wait_for_load_state("networkidle")
    # The form re-renders on the same URL
    assert "/products/create/" in page.url
    # The hidden next input must still carry the destination value
    hidden_next = page.query_selector("input[name=next][type=hidden]")
    assert hidden_next is not None, "Hidden next input must be present after failed submission"
    assert hidden_next.get_attribute("value") == "/products/"


# ---------------------------------------------------------------------------
# US3 — CRUD Action Shorthand Destinations E2E
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US3_create_with_list_shorthand_redirects_to_list(page, live_server, category):
    """[US3] Navigate to create URL with ?next=list, submit form, land at list URL.

    Required by Constitution §VIII and SC-003.
    """

    create_url = f"{live_server.url}/products/create/?next=list"
    page.goto(create_url)
    _fill_product_form(page, category, name="E2E List Redirect", slug="e2e-list-redirect")
    page.press("input[name=name]", "Enter")
    page.wait_for_load_state("networkidle")
    assert page.url.endswith("/products/"), f"Expected list URL /products/, got {page.url}"


@pytest.mark.django_db(transaction=True)
def test_US3_create_with_detail_shorthand_redirects_to_detail(page, live_server, category):
    """[US3] Navigate to create URL with ?next=detail, submit form, land at new object's detail URL.

    Required by Constitution §VIII.
    """
    create_url = f"{live_server.url}/products/create/?next=detail"
    page.goto(create_url)
    _fill_product_form(page, category, name="E2E Detail Redirect", slug="e2e-detail-redirect")
    page.press("input[name=name]", "Enter")
    page.wait_for_load_state("networkidle")
    # Detail URL for a product is /products/<pk>/
    assert "/products/" in page.url
    assert page.url.rstrip("/").split("/")[-1].isdigit(), f"Expected detail URL like /products/<pk>/, got {page.url}"
