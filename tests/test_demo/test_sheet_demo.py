"""Tests for the demo's sheet page, which shows each way a sheet is used.

Source: demo/templates/demo/components/sheet.html, demo/component_docs.py
"""

import re

import pytest
from django.urls import reverse

SHEETS = [
    "item_sheet",
    "note_sheet",
    "first_sheet",
    "second_sheet",
    "step_sheet",
    "full_sheet",
    "fixed_sheet",
]


@pytest.fixture
def page(client):
    """Return the rendered sheet page."""
    response = client.get(reverse("component-doc", kwargs={"slug": "sheet"}))
    assert response.status_code == 200
    return response.content.decode()


def sheet_tag(page, sheet_id):
    """Return the opening tag of the sheet with this id."""
    match = re.search(rf"<dialog[^>]*id=\"{sheet_id}\"[^>]*>", page)
    assert match, f"no sheet {sheet_id} on the page"
    return match.group(0)


@pytest.mark.django_db
class TestSheetDemo:
    def test_every_example_draws_its_sheet(self, page):
        missing = [
            sheet_id
            for sheet_id in SHEETS
            if "data-mvp-sheet" not in sheet_tag(page, sheet_id)
        ]

        assert not missing, f"sheets the page should draw: {missing}"

    def test_the_step_example_asks_for_a_step_that_swaps_the_head(self, client, page):
        step = page[page.index('id="step_sheet"') :]
        step = step[: step.index("</dialog>")]
        answer = client.get(reverse("sheet-demo-step")).content.decode()

        assert 'hx-get="/components/sheet/step/"' in step
        assert 'id="step_sheet-title"' in step and 'id="step_sheet-title"' in answer
        assert 'id="step_sheet-lead"' in step and 'id="step_sheet-lead"' in answer
        assert answer.count("hx-swap-oob") == 2
