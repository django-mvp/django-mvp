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


# ---------------------------------------------------------------------------
# US1 — MVPCreateView: zero-config model create page E2E (T021)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US1_create_page_title_is_model_aware(page, live_server):
    """[US1] Navigate to /products/create/ — page title element contains 'Create Product'.

    Verifies FR-001: get_page_title() derives the title from verbose_name rather than
    returning the old static 'Create Entry' fallback.
    """
    page.goto(f"{live_server.url}/products/create/")
    page.wait_for_load_state("networkidle")
    title_text = page.locator("h1, .page-title, [data-testid='page-title']").first.inner_text()
    assert "Create Product" in title_text, f"Expected 'Create Product' in page title, got: {title_text!r}"


@pytest.mark.django_db(transaction=True)
def test_US1_success_message_is_title_cased(page, live_server, category):
    """[US1] Fill and submit create form — flash message contains 'Product successfully created.'

    Verifies FR-004: get_success_message() title-cases verbose_name so the flash reads
    'Product successfully created.' rather than 'product successfully created.'
    """
    page.goto(f"{live_server.url}/products/create/")
    _fill_product_form(page, category, name="E2E Flash Product", slug="e2e-flash-product")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    # The flash message should contain the title-cased model name
    body_text = page.content()
    assert "Product successfully created." in body_text, (
        "Expected 'Product successfully created.' in flash message body"
    )


@pytest.mark.django_db(transaction=True)
def test_US1_breadcrumb_links_to_list(page, live_server):
    """[US1] Navigate to /products/create/ — first breadcrumb <a> href points to /products/.

    Verifies FR-006: breadcrumb degradation handled by base class — list link present when
    has_list_permission is truthy.
    """
    page.goto(f"{live_server.url}/products/create/")
    page.wait_for_load_state("networkidle")
    # First breadcrumb item should be an <a> linking to the product list
    breadcrumb_link = page.locator(".breadcrumb a").first
    href = breadcrumb_link.get_attribute("href")
    assert href is not None, "First breadcrumb item should be an <a> tag"
    assert href.endswith("/products/"), f"Expected breadcrumb href to end with /products/, got: {href!r}"


# ---------------------------------------------------------------------------
# US6 — MVPUpdateView: model-aware title and success message (T007-T009)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US6_update_page_title_is_model_aware(page, live_server, product):
    """[US6/T007] Navigate to the product update URL — page title contains 'Update Product'.

    Verifies FR-001: MVPUpdateView.page_title = _("Update %(verbose_name)s") produces a
    model-aware heading instead of the old static 'Update Entry' fallback.
    """
    update_url = f"{live_server.url}/products/{product.pk}/edit/"
    page.goto(update_url)
    page.wait_for_load_state("networkidle")
    title_text = page.locator("h1, .page-title, [data-testid='page-title']").first.inner_text()
    assert "Update Product" in title_text, f"Expected 'Update Product' in page title, got: {title_text!r}"


@pytest.mark.django_db(transaction=True)
def test_US6_update_success_message_is_title_cased(page, live_server, product):
    """[US6/T008] Submit valid product update form — flash contains 'Product successfully updated.'

    Verifies FR-004: the success flash uses title-cased verbose_name so the message reads
    'Product successfully updated.' not 'product successfully updated.'
    """
    update_url = f"{live_server.url}/products/{product.pk}/edit/"
    page.goto(update_url)
    page.wait_for_load_state("networkidle")
    # Clear and update the name field
    page.fill("input[name=name]", "E2E Updated Product")
    # Submit via the "Save entry" button (value=list redirects to list)
    page.click("button[type=submit][value=list]")
    page.wait_for_load_state("networkidle")
    body_text = page.content()
    assert "Product successfully updated." in body_text, (
        f"Expected 'Product successfully updated.' in flash message, got page content snippet:\n{body_text[:500]}"
    )


@pytest.mark.django_db(transaction=True)
def test_US6_update_breadcrumb_has_three_items(page, live_server, product):
    """[US6/T009] Navigate to product update URL — breadcrumb has exactly three items.

    Verifies FR-002: three-level breadcrumb (list → detail → update form title).
    Second item links to the detail view; third item has no link.
    """
    update_url = f"{live_server.url}/products/{product.pk}/edit/"
    page.goto(update_url)
    page.wait_for_load_state("networkidle")
    breadcrumb_items = page.locator(".breadcrumb li")
    count = breadcrumb_items.count()
    assert count == 3, f"Expected 3 breadcrumb items, got {count}"
    # First item should be a link (to list)
    first_link = breadcrumb_items.nth(0).locator("a")
    assert first_link.count() > 0, "First breadcrumb item should be an <a> link (list)"
    # Second item should be a link (to detail — has_detail_permission=True on ProductUpdateView)
    second_link = breadcrumb_items.nth(1).locator("a")
    assert second_link.count() > 0, "Second breadcrumb item should be an <a> link (detail)"
    # Third item should have no link (current page)
    third_link = breadcrumb_items.nth(2).locator("a")
    assert third_link.count() == 0, "Third breadcrumb item should be plain text (no link)"


# ---------------------------------------------------------------------------
# US3 — Delete link visible on update page when delete view configured (T012)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US3_update_delete_link_visible_when_configured(page, live_server, product):
    """[US3/T012] Navigate to product update URL — Delete button is visible and href has back/next.

    Verifies FR-003: the delete button rendered by the update page includes ?back= and ?next=
    query parameters, enabling the delete view to redirect correctly after deletion.
    """
    update_url = f"{live_server.url}/products/{product.pk}/edit/"
    page.goto(update_url)
    page.wait_for_load_state("networkidle")
    # The delete button should be visible
    delete_link = page.locator("a[href*='delete']").first
    assert delete_link.is_visible(), "Delete button should be visible on the update page"
    href = delete_link.get_attribute("href")
    assert "?back=" in href or "&back=" in href, f"Delete link should contain ?back= param, got: {href!r}"
    assert "next=" in href, f"Delete link should contain next= param, got: {href!r}"


# ---------------------------------------------------------------------------
# US4 — Delete link absent when delete view not configured (T014)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US4_update_delete_link_absent_when_not_configured(page, live_server):
    """[US4/T014] Navigate to category update URL (no delete view) — no delete button rendered.

    Verifies FR-009 template fix: the Delete button guard uses {% if delete_url %} so
    the button is hidden when get_delete_url() returns '' (has_delete_permission=False).
    """
    from demo.models import Category

    cat = Category.objects.create(name="E2E No Delete Cat", slug="e2e-no-delete-cat")
    update_url = f"{live_server.url}/categories/{cat.pk}/edit/"
    page.goto(update_url)
    page.wait_for_load_state("networkidle")
    # No delete link should appear anywhere on the page
    delete_links = page.locator("a[href*='delete'], button[data-action*='delete']")
    assert delete_links.count() == 0, (
        f"Expected no delete button on category update page (no delete view configured), "
        f"but found {delete_links.count()} delete element(s)"
    )
