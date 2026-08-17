"""Tests for the full-screen table layout (issue #254).

The table area (``cotton/addons/django_table.html``) and the view template
(``table_view.html``) together give a table view its own scrolling region
inside the app shell, instead of scrolling the whole window. See
specs/027-table-layout-and-column-styling/research.md R5 for the height
chain this relies on, and R1/R6/R7 for the pinned-row and accessibility
requirements this file tests.
"""

import re
from pathlib import Path

import pytest

from mvp.fixtures import _beautiful_soup

REPO_ROOT = Path(__file__).resolve().parent.parent


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
        """On the scroll region itself, not merely somewhere in the markup:
        bootstrap5-mvp.html puts the same class on the <table>, so a bare
        substring check stays green with the region's copy deleted."""
        html = self._render(cotton_render_string)
        region = _beautiful_soup()(html, "html.parser").find(attrs={"role": "region"})
        assert region is not None
        assert "table-pin-rows" in region.get("class", [])

    def test_accessible_name_can_be_set_by_the_caller(self, cotton_render_string):
        """A page with two tables needs two names. The default is emitted
        before {{ attrs }} and HTML keeps the first of a repeated attribute,
        so a caller's own aria-label has to replace it, not follow it."""
        table = _empty_product_table()
        html = cotton_render_string(
            "<c-addons.django-table :table='table' label='Products' />",
            context={"table": table},
        )
        region = _beautiful_soup()(html, "html.parser").find(attrs={"role": "region"})
        assert region["aria-label"] == "Products"

    def test_accessible_name_falls_back_to_a_default(self, cotton_render_string):
        html = self._render(cotton_render_string)
        region = _beautiful_soup()(html, "html.parser").find(attrs={"role": "region"})
        assert region["aria-label"] == "Scrollable table"

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
        """Both live in the same bar, and DOM order inside that bar is what
        decides which end each sits at. Measured inside .page-title, not
        across the document: page_view.html also renders the page title into
        <head><title>, so a whole-document index comparison holds whatever
        order the bar is in."""
        html = _render_table_view(rf)
        bar = _beautiful_soup()(html, "html.parser").find(class_="page-title")
        children = [c for c in bar.find_all("div", recursive=False)]
        assert len(children) == 2
        heading, actions = children
        assert "Products" in heading.get_text()
        assert "Add" in actions.get_text()

    @pytest.mark.django_db
    def test_no_action_list_leaks_into_the_page(self, rf, product):
        """The view's action set is a Python list in the template context, and
        <c-toolbar> renders {{ actions }} in its trailing slot. A Cotton slot
        falls through to the context variable of the same name when the caller
        fills no slot, so a context key called `actions` printed its own repr
        beside the breadcrumbs. Assert on the rendered repr rather than on the
        context key, so the test still bites if the key comes back."""
        html = _render_table_view(rf)
        assert "['search'" not in html
        assert "&#x27;search&#x27;" not in html
        assert "&#39;search&#39;" not in html

    @pytest.mark.django_db
    def test_the_bars_are_padded_and_the_table_is_not(self, rf, product):
        """table_view.html bypasses <c-container>, which is where every other
        page picks up its px-4, so the bars have to carry it themselves. The
        table must not: it reaches the edges of the space the shell gives it,
        so its scrollbar hugs the shell edge and its rows use the full width.
        Padding on the page would inset the scroll region along with the
        bars, which is the thing this asserts against."""
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")

        page = soup.find(class_="mvp-page-fill")
        assert page is not None
        assert "px-4" not in page.get("class", [])

        title_bar = soup.find(class_="page-title").parent
        assert "px-4" in title_bar.get("class", [])

        region = soup.find(attrs={"role": "region"})
        assert "px-4" not in region.get("class", [])
        assert not any("px-4" in a.get("class", []) for a in region.parents)

    @pytest.mark.django_db
    def test_the_content_column_adds_no_gap_of_its_own(self, rf, product):
        """A gap between the bars and the table is space neither controls.
        The bars carry their own spacing, so the column runs at zero and the
        table meets them."""
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        region = soup.find(attrs={"role": "region"})
        content = region.parent
        assert "gap-0" in content.get("class", [])
        assert not any(
            c.startswith("gap-") and c != "gap-0" for c in content.get("class", [])
        )

    @pytest.mark.django_db
    def test_the_pagination_bar_is_padded_vertically(self, rf, product):
        """px-4 alone leaves the count and the pagination controls sitting
        hard against the table above them and the shell edge below."""
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        bar = soup.find(class_="mvp-page-fill").find_all("div", recursive=True)
        footer_bar = [d for d in bar if "py-4" in d.get("class", [])]
        assert footer_bar, "the pagination bar carries no vertical padding"
        assert "Showing" in footer_bar[-1].get_text()

    @pytest.mark.django_db
    def test_the_app_footer_is_empty_on_a_table_view(self, rf, product):
        """The shell's footer belongs to a page that ends. This one does not:
        the viewport is fully spent on the table, so a footer under it either
        steals rows or never comes into view."""
        html = _render_table_view(rf)
        soup = _beautiful_soup()(html, "html.parser")
        assert soup.find("footer") is None

    @pytest.mark.django_db
    def test_the_breadcrumb_trail_ends_in_the_heading(self, rf, product):
        """The trail and the heading said the same word on two rows. The last
        crumb is the heading now — one row, and still exactly one <h1>, which
        is the part that would have been quietly traded away by dropping the
        heading instead."""
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        trail = soup.find("nav", class_="breadcrumbs")
        assert trail is not None

        headings = soup.find_all("h1")
        assert len(headings) == 1
        assert "Products" in headings[0].get_text()
        assert headings[0].find_parent("nav", class_="breadcrumbs") is trail

        crumbs = trail.find_all("li")
        assert len(crumbs) >= 2, "the parent crumbs must survive the fold"
        assert crumbs[-1].find("h1") is not None
        assert "Home" in crumbs[0].get_text()

    @pytest.mark.django_db
    def test_the_trail_is_the_only_row_above_the_table(self, rf, product):
        """One bar, not two. Asserted structurally rather than by counting
        pixels: the breadcrumbs sit inside the title bar."""
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        bar = soup.find(class_="page-title")
        assert bar.find("nav", class_="breadcrumbs") is not None

    @pytest.mark.django_db
    def test_the_bars_span_the_table_width(self, rf, product):
        """The title and pagination bars have to be full-width for their
        trailing halves to reach the trailing edge. A <c-toolbar> sizes each
        slot to its content, so wrapping either bar in one silently parks the
        actions next to the title instead."""
        soup = _beautiful_soup()(_render_table_view(rf), "html.parser")
        bar = soup.find(class_="page-title")
        assert "w-full" in bar.get("class", [])
        assert "w-full" in bar.parent.get("class", [])

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
    def test_footer_cells_are_styled_like_the_cells_above_them(self, rf, product):
        """A totals row sits directly under the column it totals, so it has
        to take the same alignment and wrap treatment. The footer cell is a
        third cell kind django-tables2 renders from its own attrs dict, and
        it is easy to leave behind when the heading and body cells move to a
        shared code path."""
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

    @pytest.mark.django_db
    def test_project_can_override_the_content_wrapper(self, rf, product):
        """page.content-wrapper wraps the whole title/table/pagination
        region. The table view overrode it before this layout existed, so a
        project may already be overriding it in turn — re-declaring it is
        what keeps that working rather than rendering nothing, silently."""
        html = _render_table_view(
            rf, template_name="tests/table_view_content_wrapper_override.html"
        )
        assert "override-content-wrapper" in html
        assert "mvp-page-fill" in html, "the shell wrapper survives the bypass"
        assert 'role="region"' not in html, "the default table area is gone"


class TestColumnBehaviourClasses:
    """A column's declared behaviour classes render on its cells, and the
    project-wide wrap default (mvp.config.MVP_CONFIG['table']['wrap'])
    fills in only for a column that names neither wrap class of its own —
    a column-level class always wins (FR-012, FR-014, FR-015). Red before
    T018."""

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
            "<c-addons.django-table :table='table' />", context={"table": table}
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
    """Every column behaviour class docs/styling.md documents exists in the
    built stylesheet, and every one the built stylesheet ships is documented
    — checked in both directions (FR-016, SC-005). Red before T019."""

    def _documented_classes(self):
        text = (REPO_ROOT / "docs" / "styling.md").read_text()
        return set(re.findall(r"`(mvp-col-[a-z0-9-]+)`", text))

    def _shipped_classes(self):
        text = (REPO_ROOT / "mvp" / "static" / "css" / "django-mvp.css").read_text()
        return set(re.findall(r"\.(mvp-col-[a-z0-9-]+)\s*\{", text))

    def test_shipped_set_is_not_empty(self):
        """Sanity check on the extraction itself, independent of the docs."""
        assert self._shipped_classes()

    def test_every_shipped_class_is_documented(self):
        shipped = self._shipped_classes()
        documented = self._documented_classes()
        assert shipped <= documented, f"undocumented: {shipped - documented}"

    def test_every_documented_class_is_shipped(self):
        shipped = self._shipped_classes()
        documented = self._documented_classes()
        assert documented <= shipped, f"documented but unshipped: {documented - shipped}"


class TestColumnBehaviourDemoPage:
    """The demo shows each column behaviour class against a column that
    makes its effect obvious (FR-022). Red before T021."""

    @pytest.mark.django_db
    def test_renders_200(self, client, product):
        pytest.importorskip("django_tables2")
        from django.urls import reverse

        response = client.get(reverse("table-column-behaviour"))
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_renders_a_column_for_each_behaviour_class(self, client, product):
        pytest.importorskip("django_tables2")
        from django.urls import reverse

        response = client.get(reverse("table-column-behaviour"))
        html = response.content.decode()
        for klass in (
            "mvp-col-grow",
            "mvp-col-shrink",
            "mvp-col-wrap",
            "mvp-col-nowrap",
            "mvp-col-max-md",
        ):
            assert klass in html

    @pytest.mark.django_db
    def test_renders_inferred_alignment_on_undeclared_columns(self, client, product):
        """The price, is_featured and actions columns declare no alignment
        class of their own -- FR-017's numeric, boolean and action kinds
        are inferred rather than set by hand (issue #256). Red before
        T026."""
        pytest.importorskip("django_tables2")
        from django.urls import reverse

        response = client.get(reverse("table-column-behaviour"))
        soup = _beautiful_soup()(response.content.decode(), "html.parser")
        from demo.tables import ColumnBehaviourTable

        names = list(ColumnBehaviourTable([]).columns.names())
        row = soup.find("tbody").find("tr")
        cells = dict(zip(names, row.find_all("td")))
        # Asserted per column, not as substrings of the whole page: one
        # working kind would otherwise stand in for all three.
        assert "text-end" in cells["price"].get("class", [])
        assert "text-center" in cells["is_featured"].get("class", [])
        assert "text-center" in cells["actions"].get("class", [])


class TestInferredAlignment:
    """The shipped table template infers a column's alignment from its
    model field kind: text leading, numeric trailing, boolean and action
    columns centred. The heading carries the same class as its cells, an
    explicit alignment class in a column's attrs wins, and a table over
    non-queryset data renders unchanged (FR-017-FR-021, issue #256). Red
    before T025."""

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
            "<c-addons.django-table :table='table' />", context={"table": table}
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
        """Declaring the class on "td" alone is how django-tables2 authors
        write it, and the demo table does exactly that. The heading has to
        follow it rather than fall back to the inference, or — worse — to no
        alignment at all, which is the misalignment this feature exists to
        remove (FR-019 with FR-020)."""
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
