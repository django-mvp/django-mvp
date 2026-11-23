"""Tests for the demo's sheet page, which shows each way a sheet is used.

Source: demo/templates/demo/components/sheet.html, demo/component_docs.py
"""

import re
from pathlib import Path

import pytest
from django.urls import reverse

DEMO_TEMPLATES = (
    Path(__file__).parents[2] / "demo" / "templates" / "demo" / "components"
)

SHEETS = [
    "item_sheet",
    "note_sheet",
    "first_sheet",
    "second_sheet",
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
    @pytest.mark.parametrize("sheet_id", SHEETS)
    def test_every_example_draws_its_sheet(self, page, sheet_id):
        assert "data-mvp-sheet" in sheet_tag(page, sheet_id)

    def test_the_menu_example_holds_a_menu_and_a_confirmation_view(self, page):
        assert 'data-mvp-sheet-view="menu"' in page
        assert 'data-mvp-sheet-view="confirm"' in page
        assert "mvp-sheet-menu" in page

    def test_the_form_example_holds_a_form_whose_save_closes_the_sheet(self, page):
        note = page[page.index('id="note_sheet"') :]
        note = note[: note.index("</dialog>")]
        form = re.search(r"<form[^>]*>", note)
        assert form
        assert "close()" in form.group(0)
        assert "action=" not in form.group(0)

    def test_the_second_sheet_is_opened_from_inside_the_first(self, page):
        first = page[page.index('id="first_sheet"') :]
        first = first[: first.index("</dialog>")]
        assert 'data-for="second_sheet"' in first

    def test_the_full_example_asks_for_the_full_height(self, page):
        assert "data-mvp-sheet-full" in sheet_tag(page, "full_sheet")

    def test_the_fixed_example_keeps_its_resting_height(self, page):
        assert "data-mvp-sheet-fixed" in sheet_tag(page, "fixed_sheet")

    @pytest.mark.parametrize("sheet_id", SHEETS)
    def test_every_example_has_a_trigger_that_carries_a_fallback_address(
        self, page, sheet_id
    ):
        triggers = re.findall(rf'<a[^>]*data-for="{sheet_id}"[^>]*>', page)
        assert triggers
        assert all('href="/components/sheet/"' in trigger for trigger in triggers)

    def test_the_examples_carry_no_inline_script_or_style(self):
        source = (DEMO_TEMPLATES / "sheet.html").read_text()

        assert "<script" not in source
        assert "<style" not in source
        assert "style=" not in source

    def test_the_component_index_lists_the_sheet(self, client):
        response = client.get(reverse("custom-components"))

        assert (
            reverse("component-doc", kwargs={"slug": "sheet"})
            in response.content.decode()
        )
