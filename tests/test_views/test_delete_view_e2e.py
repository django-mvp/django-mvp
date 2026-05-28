"""Integration tests for MVPDeleteView — all four deletion scenarios.

Converted from end-to-end Playwright tests to Django test-client integration tests.

Covers:
  US1 — Basic delete: warning present, Delete button present, redirect to list
  US2 — Related objects: grouped summary visible, overflow note present
  US3 — Protected object: Delete button absent, blocking message present
  US4 — Type-to-confirm: inline error on wrong value, redirect on correct value
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
# US1 — Basic delete page (T008)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US1_delete_page_has_permanent_deletion_warning(client, product):
    """[US1] GET delete page — permanent-deletion warning is visible."""
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b"permanently" in response.content


@pytest.mark.django_db
def test_US1_delete_page_has_delete_button(client, product):
    """[US1] GET delete page — Delete submit button is present."""
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b'type="submit"' in response.content


@pytest.mark.django_db
def test_US1_delete_page_breadcrumb_has_three_levels(client, product):
    """[US1] GET delete page — breadcrumb context has three items (List → obj → Delete)."""
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert len(response.context["page"]["breadcrumbs"]) == 3


@pytest.mark.django_db
def test_US1_submit_delete_redirects_to_list_and_object_absent(client, product):
    """[US1] POST delete form — redirect to product list, object no longer exists."""
    from demo.models import Product

    pk = product.pk
    url = reverse("product-delete", kwargs={"pk": pk})
    response = client.post(url)
    assert response.status_code == 302
    assert response["Location"] == reverse("product-list")
    assert not Product.objects.filter(pk=pk).exists()


# ---------------------------------------------------------------------------
# US2 — Related objects summary (T013)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US2_related_objects_section_visible(client, product):
    """[US2] show_related_objects=True — related-items section is visible."""
    url = reverse("product-delete-related", kwargs={"pk": product.pk})
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
            category=category,
            description="Overflow test",
            price="1.00",
        )

    url = reverse("category-delete-related", kwargs={"pk": category.pk})
    response = client.get(url)
    assert b"more" in response.content


# ---------------------------------------------------------------------------
# US3 — Protected object (T015)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US3_protected_page_shows_protection_alert(client, product):
    """[US3] GET delete page for a PROTECT-blocked record — protection alert visible."""
    from demo.models import OrderLine

    OrderLine.objects.create(product=product, quantity=1)
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    assert b"cannot be deleted" in response.content


@pytest.mark.django_db
def test_US3_protected_page_has_no_delete_button(client, product):
    """[US3] GET delete page for a PROTECT-blocked record — Delete button is absent."""
    from demo.models import OrderLine

    OrderLine.objects.create(product=product, quantity=1)
    url = reverse("product-delete", kwargs={"pk": product.pk})
    response = client.get(url)
    # The view sets is_protected=True which hides the submit button in the template
    assert response.context["is_protected"] is True
    assert b'type="submit"' not in response.content


# ---------------------------------------------------------------------------
# US4 — Type-to-confirm (T023)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_US4_wrong_confirmation_shows_inline_error(client, product):
    """[US4] POST wrong confirmation text — form error message is shown."""
    url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
    response = client.post(url, {"confirmation": "wrong-value"})
    content = response.content.decode()
    assert "does not match" in content or "value you entered" in content


@pytest.mark.django_db
def test_US4_correct_confirmation_deletes_and_redirects(client, product):
    """[US4] POST correct confirmation text — redirect to list, object deleted."""
    from demo.models import Product

    pk = product.pk
    url = reverse("product-delete-confirm", kwargs={"pk": pk})
    response = client.post(url, {"confirmation": str(product)})
    assert response.status_code == 302
    assert not Product.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_US4_confirmation_input_visible_with_prompt(client, product):
    """[US4] GET type-to-confirm page — confirmation input and prompt text visible."""
    url = reverse("product-delete-confirm", kwargs={"pk": product.pk})
    response = client.get(url)
    content = response.content.decode()
    assert "id_confirmation" in content
    assert str(product) in content



# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    from demo.models import Category

    return Category.objects.create(name="E2E Del Cat", slug="e2e-del-cat")


@pytest.fixture
def product(category):
    from demo.models import Product

    return Product.objects.create(
        name="E2E Delete Product",
        slug="e2e-delete-product",
        category=category,
        description="A product for E2E delete tests",
        price="9.99",
        stock=5,
    )


# ---------------------------------------------------------------------------
# US1 — Basic delete page (T008)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US1_delete_page_has_permanent_deletion_warning(page, live_server, product):
    """[US1] Navigate to basic delete page — permanent-deletion warning is visible.

    Verifies the warning alert is rendered before the user commits.
    """
    delete_url = f"{live_server.url}/products/{product.pk}/delete/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    content = page.content()
    assert "permanently" in content, "Expected permanent-deletion warning on basic delete page"


@pytest.mark.django_db(transaction=True)
def test_US1_delete_page_has_delete_button(page, live_server, product):
    """[US1] Navigate to basic delete page — Delete submit button is present.

    Verifies the Delete button is rendered for a safe-to-delete object.
    """
    delete_url = f"{live_server.url}/products/{product.pk}/delete/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
    assert submit_btn.count() > 0 or page.locator('[type="submit"]').count() > 0, (
        "Expected Delete submit button on basic delete page"
    )


@pytest.mark.django_db(transaction=True)
def test_US1_delete_page_breadcrumb_has_three_levels(page, live_server, product):
    """[US1] Navigate to basic delete page — breadcrumb has three levels (List → obj → Delete).

    Verifies get_breadcrumbs() returns a three-item trail.
    """
    delete_url = f"{live_server.url}/products/{product.pk}/delete/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    crumbs = page.locator(".breadcrumb-item")
    assert crumbs.count() == 3, f"Expected 3 breadcrumb items, got {crumbs.count()}"


@pytest.mark.django_db(transaction=True)
def test_US1_submit_delete_redirects_to_list_and_object_absent(page, live_server, product):
    """[US1] Submit delete form — redirect to /products/, object no longer appears.

    Verifies the full delete→redirect round-trip.
    """
    from demo.models import Product

    pk = product.pk
    delete_url = f"{live_server.url}/products/{pk}/delete/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    page.click('[type="submit"]')
    page.wait_for_load_state("networkidle")
    # Should redirect to the product list
    assert page.url.endswith("/products/"), f"Expected redirect to /products/, got {page.url}"
    # Object should no longer exist
    assert not Product.objects.filter(pk=pk).exists(), "Product should have been deleted"


# ---------------------------------------------------------------------------
# US2 — Related objects summary (T013)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US2_related_objects_section_visible(page, live_server, product):
    """[US2] show_related_objects=True — grouped related-items section is visible.

    Verifies the related-objects summary is rendered when the flag is set.
    """
    delete_url = f"{live_server.url}/products/{product.pk}/delete/related/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    content = page.content()
    assert "related records will also be permanently deleted" in content, (
        "Expected related-objects summary section on delete page with show_related_objects=True"
    )


@pytest.mark.django_db(transaction=True)
def test_US2_overflow_note_appears_when_related_objects_exceed_cap(page, live_server, category):
    """[US2] Overflow note appears when related objects exceed related_objects_max_per_group.

    Creates 4 products (cap is 3) then navigates to the category delete page
    to verify the overflow note is displayed.
    """
    from demo.models import Product

    # CategoryDeleteWithRelatedView has related_objects_max_per_group=3
    for i in range(4):
        Product.objects.create(
            name=f"Overflow Product {i}",
            slug=f"overflow-product-{i}",
            category=category,
            description="Overflow test",
            price="1.00",
        )

    delete_url = f"{live_server.url}/categories/{category.pk}/delete/related/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    content = page.content()
    assert "more" in content, "Expected overflow note ('… and N more') when related objects exceed cap"


# ---------------------------------------------------------------------------
# US3 — Protected object (T015)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US3_protected_page_shows_protection_alert(page, live_server, product):
    """[US3] Navigate to delete page for a protected record — protection alert visible.

    Verifies the 'This record cannot be deleted' message is shown.
    """
    from demo.models import OrderLine

    OrderLine.objects.create(product=product, quantity=1)
    delete_url = f"{live_server.url}/products/{product.pk}/delete/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    content = page.content()
    assert "cannot be deleted" in content, "Expected protection alert on delete page for protected record"


@pytest.mark.django_db(transaction=True)
def test_US3_protected_page_has_no_delete_button(page, live_server, product):
    """[US3] Navigate to delete page for a protected record — Delete button is absent.

    Verifies the Delete button is hidden when the object is PROTECT-blocked.
    """
    from demo.models import OrderLine

    OrderLine.objects.create(product=product, quantity=1)
    delete_url = f"{live_server.url}/products/{product.pk}/delete/"
    page.goto(delete_url)
    page.wait_for_load_state("networkidle")
    submit_buttons = page.locator('button[type="submit"]')
    assert submit_buttons.count() == 0, (
        f"Expected no Delete button for protected record, found {submit_buttons.count()}"
    )


# ---------------------------------------------------------------------------
# US4 — Type-to-confirm (T023)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_US4_wrong_confirmation_shows_inline_error(page, live_server, product):
    """[US4] Submit wrong confirmation text — inline error adjacent to confirmation field.

    Verifies the form error is shown when the typed value doesn't match.
    """
    confirm_url = f"{live_server.url}/products/{product.pk}/delete/confirm/"
    page.goto(confirm_url)
    page.wait_for_load_state("networkidle")
    # Fill in a wrong value and submit via direct POST (JS disables button, so bypass)
    page.evaluate("""() => {
        const input = document.getElementById('id_confirmation');
        if (input) { input.value = 'wrong-value'; }
        const btn = document.getElementById('delete-submit-btn');
        if (btn) { btn.disabled = false; }
    }""")
    page.click("#delete-submit-btn")
    page.wait_for_load_state("networkidle")
    content = page.content()
    assert "does not match" in content or "value you entered" in content, (
        "Expected inline confirmation error message when wrong value submitted"
    )


@pytest.mark.django_db(transaction=True)
def test_US4_correct_confirmation_deletes_and_redirects(page, live_server, product):
    """[US4] Submit correct confirmation text — redirect to list, object deleted.

    Verifies the full type-to-confirm → delete → redirect round-trip.
    """
    from demo.models import Product

    pk = product.pk
    expected_value = str(product)
    confirm_url = f"{live_server.url}/products/{pk}/delete/confirm/"
    page.goto(confirm_url)
    page.wait_for_load_state("networkidle")
    # Fill in the correct value and enable the button
    page.evaluate(f"""() => {{
        const input = document.getElementById('id_confirmation');
        if (input) {{ input.value = {expected_value!r}; }}
        const btn = document.getElementById('delete-submit-btn');
        if (btn) {{ btn.disabled = false; }}
    }}""")
    page.click("#delete-submit-btn")
    page.wait_for_load_state("networkidle")
    assert page.url.endswith("/products/"), f"Expected redirect to /products/, got {page.url}"
    assert not Product.objects.filter(pk=pk).exists(), "Product should have been deleted after correct confirmation"


@pytest.mark.django_db(transaction=True)
def test_US4_confirmation_input_visible_with_prompt(page, live_server, product):
    """[US4] Navigate to type-to-confirm page — confirmation input and prompt text visible.

    Verifies require_confirmation=True renders the confirmation input and prompt string.
    """
    confirm_url = f"{live_server.url}/products/{product.pk}/delete/confirm/"
    page.goto(confirm_url)
    page.wait_for_load_state("networkidle")
    content = page.content()
    # Prompt text and confirmation input should be present
    assert "id_confirmation" in content, "Expected confirmation input (id_confirmation) in page"
    assert str(product) in content, f"Expected confirmation value '{product}' in page prompt"
