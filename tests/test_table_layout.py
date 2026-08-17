"""Tests for the full-screen table layout (issue #254).

The table area (``cotton/addons/django_table.html``) and the view template
(``table_view.html``) together give a table view its own scrolling region
inside the app shell, instead of scrolling the whole window. See
specs/027-table-layout-and-column-styling/research.md R5 for the height
chain this relies on, and R1/R6/R7 for the pinned-row and accessibility
requirements this file tests.
"""

import pytest

from mvp.fixtures import _beautiful_soup


def _empty_product_table():
    pytest.importorskip("django_tables2")
    from demo.tables import ProductTable

    return ProductTable([])


def _table_view_class(table_class=None, paginate_by=25):
    """A table view declared against the current integration: model +
    table_class only, plus what's needed to make its actions visible."""
    pytest.importorskip("django_tables2")
    from demo.models import Product
    from demo.tables import ProductTable
    from mvp.integrations.django_tables.views import MVPTableView

    resolved_table_class = table_class or ProductTable
    resolved_paginate_by = paginate_by

    class DemoTableView(MVPTableView):
        model = Product
        table_class = resolved_table_class
        paginate_by = resolved_paginate_by
        search_fields = ["name"]
        show_create_action = True

    return DemoTableView


def _render_table_view(rf, template_name=None, **kwargs):
    """Instantiate, dispatch and fully render a table view, returning HTML."""
    view_class = _table_view_class(**kwargs)
    view = view_class()
    if template_name:
        view.template_name = template_name
    view.setup(rf.get("/"))
    response = view.get(view.request)
    response.render()
    return response.content.decode()


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


class TestTableViewTemplate:
    """table_view.html renders a filled page: an action bar above the table
    area, a count-and-pagination bar below, no card, and the flex chain
    between the shell and the scroll container held with no non-flex
    wrapper in it. Red before T009."""

    @pytest.mark.django_db
    def test_renders_as_a_filled_page(self, rf, product):
        html = _render_table_view(rf)
        assert "mvp-page-fill" in html

    @pytest.mark.django_db
    def test_no_card_wraps_the_table(self, rf, product):
        """No ancestor of the scroll container is a card. Checked by walking
        ancestors rather than a blanket string search, because an action's
        own modal (filter, create) legitimately uses card styling for its
        dialog surface — that is not the table being wrapped in one."""
        html = _render_table_view(rf)
        soup = _beautiful_soup()(html, "html.parser")
        region = soup.find(attrs={"role": "region"})
        assert region is not None
        assert not any("card" in a.get("class", []) for a in region.parents)

    @pytest.mark.django_db
    def test_action_bar_carries_the_page_title(self, rf, product):
        html = _render_table_view(rf)
        soup = _beautiful_soup()(html, "html.parser")
        title = soup.find(class_="page-title")
        assert title is not None
        assert "Products" in title.get_text()

    @pytest.mark.django_db
    def test_title_is_leading_and_actions_are_trailing(self, rf, product):
        """Both live in the same bar; DOM order matches the leading/trailing
        layout <c-page.title> already renders (title div, then actions)."""
        html = _render_table_view(rf)
        assert html.index("Products") < html.index(">Add<")

    @pytest.mark.django_db
    def test_pagination_bar_carries_the_result_count(self, rf, product):
        html = _render_table_view(rf)
        assert "Showing" in html

    @pytest.mark.django_db
    def test_unpaginated_view_renders_no_pagination_bar(self, rf, product):
        html = _render_table_view(rf, paginate_by=None)
        assert "Showing" not in html
        assert "Navigation page results" not in html

    @pytest.mark.django_db
    def test_a_table_with_no_footer_renders_no_footer_row(self, rf, product):
        import django_tables2 as tables

        from demo.models import Product

        class FooterlessProductTable(tables.Table):
            name = tables.Column()

            class Meta:
                model = Product
                template_name = "django_tables2/bootstrap5-mvp.html"
                fields = ("name",)

        html = _render_table_view(rf, table_class=FooterlessProductTable)
        assert "<tfoot" not in html

    @pytest.mark.django_db
    def test_a_table_declaring_a_footer_renders_its_footer_row(self, rf, product):
        import django_tables2 as tables

        from demo.models import Product

        class FootedProductTable(tables.Table):
            name = tables.Column(footer="Total")

            class Meta:
                model = Product
                template_name = "django_tables2/bootstrap5-mvp.html"
                fields = ("name",)

        html = _render_table_view(rf, table_class=FootedProductTable)
        assert "<tfoot" in html
        assert "Total" in html

    @pytest.mark.django_db
    def test_no_non_flex_wrapper_sits_between_the_page_and_the_scroll_container(
        self, rf, product
    ):
        html = _render_table_view(rf)
        soup = _beautiful_soup()(html, "html.parser")
        region = soup.find(attrs={"role": "region"})
        assert region is not None

        content = region.parent
        assert "flex" in content.get("class", [])
        assert "min-h-0" in content.get("class", [])

        page = content.parent
        assert "mvp-page-fill" in page.get("class", [])

    @pytest.mark.django_db
    def test_project_can_override_every_named_block(self, rf, product):
        html = _render_table_view(
            rf, template_name="tests/table_view_block_override.html"
        )

        assert "mvp-page-fill" in html, "the shell wrapper survives the bypass"
        for marker in (
            "override-header",
            "override-title",
            "override-actions",
            "override-content",
            "override-footer",
        ):
            assert marker in html

        assert 'role="region"' not in html, "the default table area is gone"


class TestExistingViewsNeedNoChange:
    """SC-008's only evidence: a table view and table class written against
    the current integration, with no attribute added and nothing
    subclassed, render the new layout. The only permitted edit anywhere in
    this story is removing a declared ordering (see TestTableViewOrdering
    in tests/test_integrations.py)."""

    @pytest.mark.django_db
    def test_the_demo_table_view_renders_the_new_layout_unmodified(
        self, rf, product
    ):
        pytest.importorskip("django_tables2")
        from demo.views import DataTablesView

        view = DataTablesView()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        html = response.content.decode()

        assert "mvp-page-fill" in html
        assert "table-pin-rows" in html

        soup = _beautiful_soup()(html, "html.parser")
        region = soup.find(attrs={"role": "region"})
        assert region is not None
        assert not any("card" in a.get("class", []) for a in region.parents)
