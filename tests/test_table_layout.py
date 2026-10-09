"""Tests for the full-screen table layout (issue #254).

The table area (``cotton/mvp/addons/django_table.html``) and the view template
(``table_view.html``) together give a table view its own scrolling region
inside the app shell, instead of scrolling the whole window. See
specs/027-table-layout-and-column-styling/research.md R5 for the height
chain this relies on, and R1/R6/R7 for the pinned-row and accessibility
requirements this file tests.
"""

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from mvp.fixtures import _beautiful_soup
from tests.factories import ProductFactory

REPO_ROOT = Path(__file__).resolve().parent.parent


def _empty_product_table():
    pytest.importorskip("django_tables2")
    from demo.tables import ProductTable

    return ProductTable([])


def _table_view_class(table_class=None, paginate_by=25, **attrs):
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

    for name, value in attrs.items():
        setattr(DemoTableView, name, value)
    return DemoTableView


def _render_table_view(rf, template_name=None, query="", **kwargs):
    """Instantiate, dispatch and fully render a table view, returning HTML."""
    view_class = _table_view_class(**kwargs)
    view = view_class()
    if template_name:
        view.template_name = template_name
    view.setup(rf.get(f"/products/{query}"))
    response = view.get(view.request)
    response.render()
    return response.content.decode()


class TestTableArea:
    def _render(self, cotton_render_string):
        table = _empty_product_table()
        return cotton_render_string(
            "<c-mvp.addons.django-table :table='table' />", context={"table": table}
        )

    def test_carries_the_pinned_row_class(self, cotton_render_string):
        html = self._render(cotton_render_string)
        region = _beautiful_soup()(html, "html.parser").find(attrs={"role": "region"})
        assert region is not None
        assert "table-pin-rows" in region.get("class", [])

    def test_accessible_name_can_be_set_by_the_caller(self, cotton_render_string):
        table = _empty_product_table()
        html = cotton_render_string(
            "<c-mvp.addons.django-table :table='table' label='Products' />",
            context={"table": table},
        )
        region = _beautiful_soup()(html, "html.parser").find(attrs={"role": "region"})
        assert region["aria-label"] == "Products"

    def test_accessible_name_falls_back_to_a_default(self, cotton_render_string):
        html = self._render(cotton_render_string)
        region = _beautiful_soup()(html, "html.parser").find(attrs={"role": "region"})
        assert region["aria-label"]

    def test_scrolls_on_both_axes(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert "overflow-auto" in html

    def test_is_a_keyboard_reachable_tab_stop(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert 'tabindex="0"' in html

    def test_is_announced_as_a_scrollable_region(self, cotton_render_string):
        html = self._render(cotton_render_string)
        assert 'role="region"' in html


class TestTableViewTemplate:
    @pytest.mark.django_db
    def test_renders_as_a_filled_page(self, rf, product):
        html = _render_table_view(rf)
        assert "mvp-page-fill" in html

    @pytest.mark.django_db
    def test_action_bar_carries_the_page_title(self, rf, product):
        html = _render_table_view(rf)
        soup = _beautiful_soup()(html, "html.parser")
        title = soup.find(class_="page-title")
        assert title is not None
        assert "Products" in title.get_text()

    @pytest.mark.django_db
    def test_no_action_list_leaks_into_the_page(self, rf, product):
        html = _render_table_view(rf)
        assert "['search'" not in html
        assert "&#x27;search&#x27;" not in html
        assert "&#39;search&#39;" not in html

    @pytest.mark.django_db
    def test_the_app_footer_is_empty_on_a_table_view(self, rf, product):
        html = _render_table_view(rf)
        soup = _beautiful_soup()(html, "html.parser")
        assert soup.find("footer") is None

    @pytest.mark.django_db
    def test_the_heading_is_a_plain_heading(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        headings = soup.find_all("h1")
        assert len(headings) == 1
        assert "Products" in headings[0].get_text()
        assert headings[0].find_parent("nav", class_="breadcrumbs") is None

    @pytest.mark.django_db
    def test_the_title_bar_is_the_only_row_above_the_table(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        bar = soup.find(class_="page-title")
        assert bar is not None
        assert bar.find("h1") is not None
        trail = soup.find("nav", class_="breadcrumbs")
        assert trail is not None
        assert trail.find_parent(class_="mvp-header") is not None, (
            "the page body draws no trail of its own — the app header has it"
        )

    @pytest.mark.django_db
    def test_toolbar_carries_the_result_count(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        summary = soup.find(class_="mvp-table-toolbar").find(class_="mvp-list-summary")
        assert "1" in summary.get_text().split()

    @pytest.mark.django_db
    def test_pagination_bar_carries_the_range_being_shown(self, rf, product):
        ProductFactory.create_batch(4)
        html = _render_table_view(rf, paginate_by=2, query="?page=2")
        soup = _beautiful_soup()(html, "html.parser")
        count = soup.find(class_="mvp-list-footer").find(string=re.compile(r"\d+–\d+"))
        assert count is not None, "the pagination bar did not render"
        assert "3–4" in count
        assert "5" in count

    @pytest.mark.django_db
    def test_a_single_page_renders_no_pagination_bar(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        assert soup.find(class_="mvp-list-footer") is None

    @pytest.mark.django_db
    def test_unpaginated_view_renders_no_pagination_bar(self, rf, product):
        soup = _beautiful_soup()(
            _render_table_view(rf, paginate_by=None), "html.parser"
        )
        count = soup.find(class_="mvp-page-fill").find(string=re.compile(r"\d+-\d+"))
        assert count is None

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
    def test_footer_cells_are_styled_like_the_cells_above_them(self, rf, product):
        import django_tables2 as tables

        from demo.models import Product

        class FootedProductTable(tables.Table):
            price = tables.Column(footer="Total")

            class Meta:
                model = Product
                template_name = "django_tables2/bootstrap5-mvp.html"
                fields = ("price",)

        html = _render_table_view(rf, table_class=FootedProductTable)
        soup = _beautiful_soup()(html, "html.parser")
        cell = soup.find("tfoot").find("td")
        assert "text-end" in cell.get("class", []), "DecimalField, so trailing"
        assert "mvp-col-nowrap" in cell.get("class", [])

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

    @pytest.mark.django_db
    def test_project_can_override_the_content_wrapper(self, rf, product):
        html = _render_table_view(
            rf, template_name="tests/table_view_content_wrapper_override.html"
        )
        assert "override-content-wrapper" in html
        assert "mvp-page-fill" in html, "the shell wrapper survives the bypass"
        assert 'role="region"' not in html, "the default table area is gone"


class TestTheTablePageNamesItsParts:
    """The page and its pager carry classes of their own, which the packaged
    stylesheet paints from and a project's stylesheet can select on."""

    @pytest.mark.django_db
    def test_the_filled_page_is_marked_as_a_table_page(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        page = soup.find(class_="mvp-page-fill")
        assert "mvp-table-page" in page["class"]

    @pytest.mark.django_db
    def test_the_pagination_bar_is_marked_as_the_table_pager(self, rf, product):
        ProductFactory.create_batch(4)
        html = _render_table_view(rf, paginate_by=2)
        soup = _beautiful_soup()(html, "html.parser")
        assert "mvp-table-pager" in soup.find(class_="mvp-list-footer")["class"]


class TestColumnBehaviourClasses:
    def _table(self):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        class BehaviourTable(tables.Table):
            grow = tables.Column(attrs={"td": {"class": "mvp-col-grow"}})
            shrink = tables.Column(attrs={"td": {"class": "mvp-col-shrink"}})
            wrap = tables.Column(attrs={"td": {"class": "mvp-col-wrap"}})
            nowrap = tables.Column(attrs={"td": {"class": "mvp-col-nowrap"}})
            maxwidth = tables.Column(attrs={"td": {"class": "mvp-col-max-md"}})
            plain = tables.Column()

            class Meta:
                template_name = "django_tables2/bootstrap5-mvp.html"

        return BehaviourTable(
            [
                {
                    "grow": "a",
                    "shrink": "b",
                    "wrap": "c",
                    "nowrap": "d",
                    "maxwidth": "e",
                    "plain": "f",
                }
            ]
        )

    def _row_cells(self, cotton_render_string, table):
        html = cotton_render_string(
            "<c-mvp.addons.django-table :table='table' />", context={"table": table}
        )
        soup = _beautiful_soup()(html, "html.parser")
        row = soup.find("tbody").find("tr")
        return row.find_all("td")

    def test_each_declared_behaviour_class_renders_on_its_cell(
        self, cotton_render_string
    ):
        cells = self._row_cells(cotton_render_string, self._table())
        assert "mvp-col-grow" in cells[0].get("class", [])
        assert "mvp-col-shrink" in cells[1].get("class", [])
        assert "mvp-col-wrap" in cells[2].get("class", [])
        assert "mvp-col-nowrap" in cells[3].get("class", [])
        assert "mvp-col-max-md" in cells[4].get("class", [])

    def test_project_wrap_default_off_applies_to_a_column_declaring_neither_class(
        self, cotton_render_string
    ):
        cells = self._row_cells(cotton_render_string, self._table())
        assert "mvp-col-nowrap" in cells[5].get("class", [])
        assert "mvp-col-wrap" not in cells[5].get("class", [])

    def test_project_wrap_default_on_applies_to_a_column_declaring_neither_class(
        self, cotton_render_string, monkeypatch
    ):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["table"], "wrap", True)
        cells = self._row_cells(cotton_render_string, self._table())
        assert "mvp-col-wrap" in cells[5].get("class", [])
        assert "mvp-col-nowrap" not in cells[5].get("class", [])

    def test_column_level_class_overrides_the_project_default(
        self, cotton_render_string, monkeypatch
    ):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["table"], "wrap", True)
        cells = self._row_cells(cotton_render_string, self._table())
        assert "mvp-col-nowrap" in cells[3].get("class", [])
        assert "mvp-col-wrap" not in cells[3].get("class", [])


class TestDocumentedClassesMatchShipped:
    def _documented_classes(self):
        text = (REPO_ROOT / "docs" / "styling.md").read_text()
        return set(re.findall(r"`(mvp-col-[a-z0-9-]+)`", text))

    def _shipped_classes(self):
        text = (REPO_ROOT / "mvp" / "static" / "css" / "django-mvp.css").read_text()
        return set(re.findall(r"\.(mvp-col-[a-z0-9-]+)\s*\{", text))

    def test_shipped_set_is_not_empty(self):
        assert self._shipped_classes()

    def test_every_shipped_class_is_documented(self):
        shipped = self._shipped_classes()
        documented = self._documented_classes()
        assert shipped <= documented, f"undocumented: {shipped - documented}"

    def test_every_documented_class_is_shipped(self):
        shipped = self._shipped_classes()
        documented = self._documented_classes()
        assert documented <= shipped, (
            f"documented but unshipped: {documented - shipped}"
        )


class TestColumnBehaviourDemoPage:
    @pytest.mark.django_db
    def test_renders_200(self, client, product):
        pytest.importorskip("django_tables2")
        from django.urls import reverse

        response = client.get(reverse("table-column-behaviour"))
        assert response.status_code == 200


class TestInferredAlignment:
    def _table_class(self):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        from demo.models import Product

        class AlignmentTable(tables.Table):
            action = tables.Column(orderable=False, empty_values=())
            # IntegerField would normally infer "text-end" -- pinned here to
            # prove the column's own declared class wins over the inference.
            stock = tables.Column(attrs={"td": {"class": "text-start"}})

            class Meta:
                model = Product
                template_name = "django_tables2/bootstrap5-mvp.html"
                fields = ("name", "price", "is_featured", "stock")

        return AlignmentTable

    def _table(self):
        from demo.models import Product

        return self._table_class()(Product.objects.all())

    def _render(self, cotton_render_string, table):
        html = cotton_render_string(
            "<c-mvp.addons.django-table :table='table' />", context={"table": table}
        )
        return _beautiful_soup()(html, "html.parser")

    def _cells_by_column(self, soup, table):
        names = list(table.columns.names())
        row = soup.find("tbody").find("tr")
        return dict(zip(names, row.find_all("td")))

    def _heads_by_column(self, soup, table):
        names = list(table.columns.names())
        head_row = soup.find("thead").find("tr")
        return dict(zip(names, head_row.find_all("th")))

    @pytest.mark.django_db
    def test_text_column_cells_are_leading(self, cotton_render_string, product):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        cells = self._cells_by_column(soup, table)
        assert "text-start" in cells["name"].get("class", [])

    @pytest.mark.django_db
    def test_numeric_column_cells_are_trailing(self, cotton_render_string, product):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        cells = self._cells_by_column(soup, table)
        assert "text-end" in cells["price"].get("class", [])

    @pytest.mark.django_db
    def test_boolean_column_cells_are_centred(self, cotton_render_string, product):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        cells = self._cells_by_column(soup, table)
        assert "text-center" in cells["is_featured"].get("class", [])

    @pytest.mark.django_db
    def test_action_column_cells_are_centred(self, cotton_render_string, product):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        cells = self._cells_by_column(soup, table)
        assert "text-center" in cells["action"].get("class", [])

    @pytest.mark.django_db
    def test_heading_carries_the_same_alignment_as_its_cells(
        self, cotton_render_string, product
    ):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        heads = self._heads_by_column(soup, table)
        assert "text-end" in heads["price"].get("class", [])

    @pytest.mark.django_db
    def test_explicit_column_class_wins_over_the_inferred_one(
        self, cotton_render_string, product
    ):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        cells = self._cells_by_column(soup, table)
        assert "text-start" in cells["stock"].get("class", [])
        assert "text-end" not in cells["stock"].get("class", [])

    @pytest.mark.django_db
    def test_an_explicit_class_on_the_cells_carries_to_the_heading(
        self, cotton_render_string, product
    ):
        table = self._table()
        soup = self._render(cotton_render_string, table)
        heads = self._heads_by_column(soup, table)
        assert "text-start" in heads["stock"].get("class", [])
        assert "text-end" not in heads["stock"].get("class", [])

    def test_table_over_non_model_data_renders_unchanged(self, cotton_render_string):
        table_class = self._table_class()
        table = table_class(
            [
                {
                    "name": "a",
                    "price": "1",
                    "is_featured": True,
                    "action": "x",
                    "stock": "5",
                }
            ]
        )
        soup = self._render(cotton_render_string, table)
        cells = self._cells_by_column(soup, table)
        alignment_classes = {"text-start", "text-center", "text-end"}
        for name in ("name", "price", "is_featured", "action"):
            assert not alignment_classes & set(cells[name].get("class", []))
        # "stock" keeps its own declared class -- untouched either way.
        assert "text-start" in cells["stock"].get("class", [])


class TestRowHeaderCells:
    def _table(self, row_headers=None):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        declared = row_headers

        class RowHeaderTable(tables.Table):
            icon = tables.Column(attrs={"td": {"class": "mvp-col-shrink"}})
            name = tables.Column()
            price = tables.Column()

            class Meta:
                template_name = "django_tables2/bootstrap5-mvp.html"
                if declared is not None:
                    row_headers = declared

        return RowHeaderTable([{"icon": "i", "name": "a", "price": "1"}])

    def _row(self, cotton_render_string, table):
        html = cotton_render_string(
            "<c-mvp.addons.django-table :table='table' />", context={"table": table}
        )
        return _beautiful_soup()(html, "html.parser").find("tbody").find("tr")

    def test_a_declared_column_renders_as_a_row_header(self, cotton_render_string):
        row = self._row(cotton_render_string, self._table(("icon",)))
        headers = row.find_all("th")
        assert len(headers) == 1
        assert headers[0].get("scope") == "row"
        assert headers[0].get_text(strip=True) == "i"

    def test_every_other_column_stays_a_data_cell(self, cotton_render_string):
        row = self._row(cotton_render_string, self._table(("icon",)))
        cells = row.find_all("td")
        assert [cell.get_text(strip=True) for cell in cells] == ["a", "1"]

    def test_a_table_declaring_none_renders_no_row_headers(self, cotton_render_string):
        row = self._row(cotton_render_string, self._table())
        assert row.find_all("th") == []
        assert len(row.find_all("td")) == 3

    def test_a_row_header_keeps_the_column_behaviour_classes_of_its_cells(
        self, cotton_render_string
    ):
        row = self._row(cotton_render_string, self._table(("icon",)))
        classes = row.find("th").get("class", [])
        assert "mvp-col-shrink" in classes

    def test_several_columns_can_be_declared(self, cotton_render_string):
        row = self._row(cotton_render_string, self._table(("icon", "name")))
        assert [th.get_text(strip=True) for th in row.find_all("th")] == ["i", "a"]

    def test_a_single_name_may_be_given_as_a_string(self, cotton_render_string):
        row = self._row(cotton_render_string, self._table("icon"))
        assert [th.get_text(strip=True) for th in row.find_all("th")] == ["i"]

    def test_the_column_heading_is_still_a_column_header(self, cotton_render_string):
        html = cotton_render_string(
            "<c-mvp.addons.django-table :table='table' />",
            context={"table": self._table(("icon",))},
        )
        soup = _beautiful_soup()(html, "html.parser")
        headings = soup.find("thead").find_all("th")
        assert [heading.get("scope") for heading in headings] == ["col"] * 3

    @pytest.mark.parametrize("localize", [None, True, False])
    @pytest.mark.parametrize("value", [Decimal("12345.6"), date(2026, 9, 15)])
    def test_a_row_header_renders_its_value_the_way_a_data_cell_does(
        self, cotton_render_string, localize, value
    ):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables
        from django.utils.translation import override

        class ParityTable(tables.Table):
            pinned = tables.Column(localize=localize)
            plain = tables.Column(localize=localize)

            class Meta:
                template_name = "django_tables2/bootstrap5-mvp.html"
                row_headers = ("pinned",)

        table = ParityTable([{"pinned": value, "plain": value}])
        with override("de"):
            row = self._row(cotton_render_string, table)
        assert row.find("th").get_text(strip=True) == row.find("td").get_text(
            strip=True
        )

    def test_an_unknown_column_name_is_refused(self, cotton_render_string):
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="nonexistent"):
            self._row(cotton_render_string, self._table(("icon", "nonexistent")))


class TestFalseyColumnHeading:
    def _headings(self, cotton_render_string):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        class HeadingTable(tables.Table):
            named = tables.Column()
            false_heading = tables.Column(verbose_name=False)
            empty_heading = tables.Column(verbose_name="")
            unsortable = tables.Column(verbose_name=False, orderable=False)

            class Meta:
                template_name = "django_tables2/bootstrap5-mvp.html"

        table = HeadingTable(
            [
                {
                    "named": "a",
                    "false_heading": "b",
                    "empty_heading": "c",
                    "unsortable": "d",
                }
            ]
        )
        html = cotton_render_string(
            "<c-mvp.addons.django-table :table='table' />", context={"table": table}
        )
        soup = _beautiful_soup()(html, "html.parser")
        return soup.find("thead").find_all("th")

    def test_a_false_heading_prints_nothing(self, cotton_render_string):
        assert self._headings(cotton_render_string)[1].get_text(strip=True) == ""

    def test_an_empty_heading_prints_nothing(self, cotton_render_string):
        assert self._headings(cotton_render_string)[2].get_text(strip=True) == ""

    def test_a_false_heading_on_an_unsortable_column_prints_nothing(
        self, cotton_render_string
    ):
        assert self._headings(cotton_render_string)[3].get_text(strip=True) == ""

    def test_the_heading_cell_itself_is_still_rendered(self, cotton_render_string):
        assert len(self._headings(cotton_render_string)) == 4

    def test_an_orderable_column_keeps_its_sort_control(self, cotton_render_string):
        heading = self._headings(cotton_render_string)[1]
        assert heading.find("a") is not None


TOOLBAR_PANEL = "mvpTableToolbarPanel"


class TestTableToolbar:
    @pytest.mark.django_db
    def test_the_toggle_names_the_panel_it_opens_and_closes(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        toggle = soup.find("button", attrs={"aria-controls": TOOLBAR_PANEL})
        assert toggle is not None
        assert soup.find(id=TOOLBAR_PANEL) is not None

    @pytest.mark.django_db
    def test_search_and_the_add_action_are_inside_the_panel(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        panel = soup.find(id=TOOLBAR_PANEL)
        assert panel.find(attrs={"name": "q"}) is not None
        assert panel.find("a", href="/products/create/") is not None

    @pytest.mark.django_db
    def test_a_view_with_nothing_to_put_in_the_panel_has_no_panel_or_toggle(
        self, rf, product
    ):
        html = _render_table_view(rf, search_fields=None, show_create_action=False)
        soup = _beautiful_soup()(html, "html.parser")

        assert soup.find(class_="mvp-table-toolbar").find("h1") is not None
        assert soup.find(id=TOOLBAR_PANEL) is None
        assert soup.find("button", attrs={"aria-controls": TOOLBAR_PANEL}) is None

    @pytest.mark.django_db
    def test_an_applied_search_is_drawn_with_a_link_that_removes_it(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf, query="?q=lamp"), "html.parser")

        refinements = soup.find(id=TOOLBAR_PANEL).find(class_="mvp-list-refinements")
        assert refinements.find("a", href="/products/") is not None

    @pytest.mark.django_db
    def test_the_bar_says_how_many_filters_are_applied(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf, query="?q=lamp"), "html.parser")

        note = soup.find(class_="mvp-table-toolbar-note")
        assert "1" in note.get_text().split()
        assert note.find_parent(id=TOOLBAR_PANEL) is None, (
            "it shows with the panel closed"
        )

    @pytest.mark.django_db
    def test_the_bar_says_nothing_when_no_filter_is_applied(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        assert soup.find(class_="mvp-table-toolbar-note") is None

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "block",
        [
            "page.toolbar",
            "page.summary",
            "page.panel",
            "page.search",
            "page.controls",
            "page.refinements",
        ],
    )
    def test_a_project_can_replace_one_part_of_the_toolbar(self, rf, product, block):
        html = _render_table_view(
            rf,
            template_name="tests/table_view_part_override.html",
            query="?q=product",
            extra_context={"override": block},
        )
        soup = _beautiful_soup()(html, "html.parser")

        assert soup.find(id="override") is not None
        assert soup.find(attrs={"role": "region"}) is not None, "the table is kept"


class TestTableFillerRow:
    @pytest.mark.django_db
    def test_a_table_with_rows_ends_in_a_filler_row_hidden_from_readers(
        self, rf, product
    ):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        rows = soup.find("tbody").find_all("tr")
        assert "mvp-table-filler" in rows[-1]["class"]
        assert rows[-1].get("aria-hidden") == "true"
        assert rows[-1].get_text(strip=True) == ""

    @pytest.mark.django_db
    def test_the_filler_cell_spans_every_column(self, rf, product):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        cell = soup.find(class_="mvp-table-filler").find("td")
        assert int(cell["colspan"]) == len(soup.find("thead").find_all("th"))

    @pytest.mark.django_db
    def test_a_table_with_no_records_offers_the_create_action_in_its_body(self, rf):
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        filler = soup.find("tbody").find(class_="mvp-table-filler")
        assert filler.get("aria-hidden") is None
        assert filler.find("a", href="/products/create/") is not None

    @pytest.mark.django_db
    def test_a_search_matching_nothing_offers_to_clear_it_in_the_body(
        self, rf, product
    ):
        html = _render_table_view(rf, query="?q=zzzz&sort=name")
        soup = _beautiful_soup()(html, "html.parser")

        empty = soup.find("tbody").find(class_="mvp-list-empty")
        assert empty.find("a", href="/products/?sort=name") is not None
        assert empty.find("a", href="/products/create/") is None


class TestRowHeaderFooterCell:
    def _render(self, cotton_render_string, row_headers):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        class TotalledTable(tables.Table):
            name = tables.Column(footer="Total")
            price = tables.Column(footer="30")

            class Meta:
                template_name = "django_tables2/bootstrap5-mvp.html"

        TotalledTable.Meta.row_headers = row_headers
        TotalledTable._meta.row_headers = row_headers
        table = TotalledTable([{"name": "Lamp", "price": 30}])
        html = cotton_render_string(
            '<c-mvp.addons.django-table :table="table" />', context={"table": table}
        )
        return _beautiful_soup()(html, "html.parser")

    def test_the_footer_cell_of_a_row_header_column_is_a_row_header(
        self, cotton_render_string
    ):
        soup = self._render(cotton_render_string, ("name",))

        cells = soup.find("tfoot").find("tr").find_all(["th", "td"])
        assert [cell.name for cell in cells] == ["th", "td"]
        assert cells[0]["scope"] == "row"

    def test_the_heading_of_a_row_header_column_is_marked(self, cotton_render_string):
        soup = self._render(cotton_render_string, ("name",))

        headings = soup.find("thead").find_all("th")
        assert headings[0].has_attr("data-row-header")
        assert not headings[1].has_attr("data-row-header")

    def test_a_table_with_no_row_headers_keeps_plain_footer_cells(
        self, cotton_render_string
    ):
        soup = self._render(cotton_render_string, ())

        cells = soup.find("tfoot").find("tr").find_all(["th", "td"])
        assert [cell.name for cell in cells] == ["td", "td"]
