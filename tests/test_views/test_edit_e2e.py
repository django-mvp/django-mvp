"""Real-browser tests for delete-page layout (issue #268).

Both claims here are about computed layout, which is why they run in a browser.
A rendered-HTML assertion can say which elements are present and which classes
they carry, but neither defect is visible at that level:

- An alert is a column grid, so every direct child becomes its own column. A
  message written as text with an emphasised word inside it produced three
  columns, and the browser spread them across the alert's width. The markup was
  correct in every other sense.
- The pre-form content and the form sat flush against each other. Nothing in
  the markup says so — only the boxes the browser computed do.

Source: mvp/templates/form_view.html, mvp/templates/delete_view.html
"""

import pytest
from django.urls import reverse

from demo.models import OrderLine
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1440, "height": 900}

# The icon plus one content column. Anything more means the message was split.
EXPECTED_ALERT_COLUMNS = 2


def _alert_columns(page):
    """Return the alert's resolved grid columns, as a list of track sizes."""
    return page.evaluate("""
        () => getComputedStyle(document.querySelector('[role=alert]'))
                .gridTemplateColumns.split(' ')
    """)


def _gap_above_form(page):
    """Return the vertical distance between the pre-form content and the form."""
    return page.evaluate("""
        () => {
          const form = document.querySelector('.mvp-delete-page form');
          const previous = form.previousElementSibling;
          return Math.round(form.getBoundingClientRect().top
                            - previous.getBoundingClientRect().bottom);
        }
    """)


@pytest.mark.django_db(transaction=True)
class TestDeletePageAlertLayout:
    """The warning message reads as one paragraph, not as spread-out columns."""

    def test_warning_alert_has_one_content_column(self, page, live_server, product):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{reverse('product-delete', kwargs={'pk': product.pk})}")

        columns = _alert_columns(page)

        assert len(columns) == EXPECTED_ALERT_COLUMNS, (
            f"alert resolved to {len(columns)} columns ({columns}); the message "
            "is being split across them instead of flowing as one block"
        )

    def test_blocked_alert_has_one_content_column(self, page, live_server, product):
        """The same claim for the alert that lists what is blocking deletion.

        It carries a heading, a sentence and a list, which is three columns
        under the same rule.
        """
        OrderLine.objects.create(product=product, quantity=1)
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{reverse('product-delete', kwargs={'pk': product.pk})}")

        columns = _alert_columns(page)

        assert len(columns) == EXPECTED_ALERT_COLUMNS, (
            f"alert resolved to {len(columns)} columns ({columns})"
        )


@pytest.mark.django_db(transaction=True)
class TestDeletePageSpacing:
    """The content above the form is not flush against it."""

    def test_form_is_spaced_from_the_content_above_it(
        self, page, live_server, product
    ):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}{reverse('product-delete', kwargs={'pk': product.pk})}")

        assert _gap_above_form(page) > 0, (
            "the form starts where the warning ends, so the actions read as part "
            "of the alert"
        )

    def test_confirmation_page_is_spaced_from_the_content_above_it(
        self, page, live_server, product
    ):
        page.set_viewport_size(DESKTOP)
        path = reverse("product-delete-confirm", kwargs={"pk": product.pk})
        page.goto(f"{live_server.url}{path}")

        assert _gap_above_form(page) > 0
