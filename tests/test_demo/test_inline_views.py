"""Tests for the two demo pages FS-025 US5 adds: a page carrying two row
sets, and a rows-only page.

Both are dispatched through real HTTP requests (the test client against
``demo/urls.py``), not ``as_view()`` directly, since the acceptance is that
the pages render and accept a submission through the actual routing.

Source: demo/views.py (``ProjectCreateView``, ``ProductOrderLinesRowsOnlyView``)
Spec: specs/025-multiple-related-sets/spec.md — User Story 5, FR-025;
specs/025-multiple-related-sets/tasks.md — T059
"""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from demo.models import OrderLine, Project, ProjectNote, ProjectTask
from tests.factories import ProductFactory


def _has_field(html, field_name):
    """Whether an input, textarea or select named ``field_name`` is present."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.find(attrs={"name": field_name}) is not None


@pytest.mark.django_db
class TestProjectCreateViewRendersTwoSets:
    """The two-set demo page renders a project's task and note sets, each
    under its own default heading."""

    def test_renders_200(self, client):
        response = client.get(reverse("project-create"))

        assert response.status_code == 200

    def test_renders_both_sets_under_their_default_headings(self, client):
        response = client.get(reverse("project-create"))
        html = response.content.decode()

        tasks_index = html.index(str(ProjectTask._meta.verbose_name_plural))
        notes_index = html.index(str(ProjectNote._meta.verbose_name_plural))
        assert tasks_index < notes_index


@pytest.mark.django_db
class TestProjectCreateViewSubmission:
    """A valid submission creates the project and both sets' rows together."""

    def test_submission_creates_the_project_and_both_sets_rows(self, client):
        response = client.post(
            reverse("project-create"),
            data={
                "name": "Website revamp",
                "tasks-TOTAL_FORMS": "1",
                "tasks-INITIAL_FORMS": "0",
                "tasks-MIN_NUM_FORMS": "0",
                "tasks-MAX_NUM_FORMS": "1000",
                "tasks-0-title": "Design mockups",
                "notes-TOTAL_FORMS": "1",
                "notes-INITIAL_FORMS": "0",
                "notes-MIN_NUM_FORMS": "0",
                "notes-MAX_NUM_FORMS": "1000",
                "notes-0-text": "Kickoff meeting notes",
            },
        )

        assert response.status_code == 302
        project = Project.objects.get(name="Website revamp")
        assert ProjectTask.objects.filter(
            project=project, title="Design mockups"
        ).exists()
        assert ProjectNote.objects.filter(
            project=project, text="Kickoff meeting notes"
        ).exists()


@pytest.mark.django_db
class TestProductOrderLinesRowsOnlyViewRendersNoParentField:
    """The rows-only demo page renders no input for any of the parent
    product's own fields."""

    def test_renders_200(self, client):
        product = ProductFactory()

        response = client.get(
            reverse("product-order-lines-rows-only", kwargs={"pk": product.pk})
        )

        assert response.status_code == 200

    def test_renders_no_parent_field(self, client):
        product = ProductFactory()

        response = client.get(
            reverse("product-order-lines-rows-only", kwargs={"pk": product.pk})
        )
        html = response.content.decode()

        assert not _has_field(html, "name")
        assert not _has_field(html, "category")

    def test_still_renders_the_order_line_set(self, client):
        product = ProductFactory()

        response = client.get(
            reverse("product-order-lines-rows-only", kwargs={"pk": product.pk})
        )
        html = response.content.decode()

        # OrderLineInline sets its own title ("Order lines"), so this is the
        # heading rendered rather than the model's raw verbose_name_plural.
        assert "Order lines" in html


@pytest.mark.django_db
class TestProductOrderLinesRowsOnlyViewSubmission:
    """A valid submission on the rows-only page saves its rows and leaves
    the product's own field values unchanged."""

    def test_submission_saves_rows_and_leaves_the_products_own_fields_unchanged(
        self, client
    ):
        product = ProductFactory(name="Original name")

        response = client.post(
            reverse("product-order-lines-rows-only", kwargs={"pk": product.pk}),
            data={
                "order_lines-TOTAL_FORMS": "1",
                "order_lines-INITIAL_FORMS": "0",
                "order_lines-MIN_NUM_FORMS": "0",
                "order_lines-MAX_NUM_FORMS": "1000",
                "order_lines-0-quantity": "4",
            },
        )

        assert response.status_code == 302
        product.refresh_from_db()
        assert product.name == "Original name"
        assert OrderLine.objects.filter(product=product, quantity=4).exists()

    def test_submission_touches_the_products_auto_now_field(self, client):
        product = ProductFactory()
        original_updated_at = product.updated_at

        client.post(
            reverse("product-order-lines-rows-only", kwargs={"pk": product.pk}),
            data={
                "order_lines-TOTAL_FORMS": "1",
                "order_lines-INITIAL_FORMS": "0",
                "order_lines-MIN_NUM_FORMS": "0",
                "order_lines-MAX_NUM_FORMS": "1000",
                "order_lines-0-quantity": "2",
            },
        )

        product.refresh_from_db()
        assert product.updated_at > original_updated_at
