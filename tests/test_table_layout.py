"""Tests for the full-screen table layout (issue #254).

The table area (``cotton/addons/django_table.html``) and the view template
(``table_view.html``) together give a table view its own scrolling region
inside the app shell, instead of scrolling the whole window. See
specs/027-table-layout-and-column-styling/research.md R5 for the height
chain this relies on, and R1/R6/R7 for the pinned-row and accessibility
requirements this file tests.
"""

import pytest


def _empty_product_table():
    pytest.importorskip("django_tables2")
    from demo.tables import ProductTable

    return ProductTable([])


class TestTableArea:
    """cotton/addons/django_table.html renders the scroll container the
    table area needs: pinned rows, scrolling on both axes, a stable
    scrollbar gutter and keyboard-reachable accessibility. Red before T008."""

    def _render(self, cotton_render_string):
        table = _empty_product_table()
        return cotton_render_string(
            "<c-addons.django-table :table='table' />", context={"table": table}
        )

    def test_carries_the_pinned_row_class(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert "table-pin-rows" in html

    def test_scrolls_on_both_axes(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert "overflow-auto" in html

    def test_reserves_a_stable_scrollbar_gutter(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert "scrollbar-gutter: stable" in html

    def test_is_a_keyboard_reachable_tab_stop(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert 'tabindex="0"' in html

    def test_is_announced_as_a_scrollable_region(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert 'role="region"' in html

    def test_has_a_translatable_accessible_name(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert 'aria-label="Scrollable table"' in html
