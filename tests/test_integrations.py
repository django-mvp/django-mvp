"""Tests for mvp.integrations — guarded optional-dependency modules.

Integrations are deliberately NOT extras: each lives in a dedicated module
under mvp.integrations that core never imports, so its third-party dependency
is only required when a project explicitly imports the integration.
"""

import re

import django_filters
import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test.utils import CaptureQueriesContext

from demo.models import Product
from mvp.filters import SearchFilter, SortFilter
from mvp.integrations import missing_dependency
from mvp.views.list import MVPListView
from tests.factories import ProductFactory


def _plain_table_view_class():
    """A table view declared exactly as a project would, no ordering."""
    pytest.importorskip("django_tables2")
    from demo.models import Product
    from demo.tables import ProductTable
    from mvp.integrations.django_tables.views import MVPTableView

    class PlainTableView(MVPTableView):
        model = Product
        table_class = ProductTable

    return PlainTableView


def _prefetching_table_view_class(paginate_by=5, table_pagination=None):
    """A paginated table view whose queryset carries a prefetch, so a repeated
    row query shows up as a repeated prefetch too."""
    pytest.importorskip("django_tables2")
    from demo.models import Product
    from demo.tables import ProductTable
    from mvp.integrations.django_tables.views import MVPTableView

    resolved_paginate_by = paginate_by
    resolved_table_pagination = table_pagination

    class PrefetchingTableView(MVPTableView):
        model = Product
        table_class = ProductTable
        paginate_by = resolved_paginate_by
        table_pagination = resolved_table_pagination

        def get_queryset(self):
            return super().get_queryset().prefetch_related("category")

    return PrefetchingTableView


def _table_view_context(rf, query="", **kwargs):
    """Dispatch a table view and return the context it built."""
    view = _prefetching_table_view_class(**kwargs)()
    view.setup(rf.get(f"/{query}"))
    view.request.user = AnonymousUser()
    return view.get(view.request).context_data


class TestIntegrationIsolation:
    def test_missing_dependency_message_names_module_and_pip_package(self):
        err = missing_dependency("django_tables", "django-tables2")
        assert isinstance(err, ImproperlyConfigured)
        assert "mvp.integrations.django_tables" in str(err)
        assert "pip install django-tables2" in str(err)

    def test_core_views_have_no_optional_dependency_imports(self):
        import ast
        from pathlib import Path

        import mvp

        # django_filters is a dependency of the package (ADR 0033); the core
        # list view builds its filterset with it. The others stay optional.
        views_dir = Path(next(iter(mvp.__path__))) / "views"
        optional = {"django_tables2"}

        for module_path in views_dir.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    assert name.split(".")[0] not in optional, (
                        f"{module_path.name} imports optional package '{name}' — move that code to mvp/integrations/"
                    )


class TestOptionalIntegrations:
    @pytest.mark.django_db
    def test_filtered_list_view_clear_filters_url_drops_only_filter_fields(self, rf):
        import django_filters

        from demo.models import Product
        from mvp.filters import SearchFilter, SortFilter
        from mvp.views.list import MVPListView

        class ProductFilter(django_filters.FilterSet):
            q = SearchFilter(fields=["name"])
            o = SortFilter(options=[("name_asc", "Name (A-Z)", "name")])

            class Meta:
                model = Product
                fields = ["name"]

        class ProductFilteredView(MVPListView):
            model = Product
            filterset_class = ProductFilter
            paginate_by = 5

        ProductFactory.create_batch(6, name="Widget")
        view = ProductFilteredView()
        view.setup(
            rf.get(
                "/",
                {"name": "Widget", "q": "widget", "o": "name_asc", "page": "2"},
            )
        )
        response = view.get(view.request)
        context = response.context_data
        assert context["applied_filter_count"] == 2
        clear_url = context["clear_filters_url"]
        assert clear_url.startswith("/?")
        query = clear_url.split("?", 1)[1]
        params = dict(pair.split("=") for pair in query.split("&"))
        assert "name" not in params
        assert "q" not in params
        assert "page" not in params
        assert params["o"] == "name_asc"

    @pytest.mark.django_db
    def test_filter_panel_renders_clear_link_only_when_filters_applied(self, rf):
        from bs4 import BeautifulSoup

        from demo.models import Product
        from mvp.views.list import MVPListView

        class ProductFilteredView(MVPListView):
            model = Product
            filterset_fields = ["name"]
            list_item_template = "cards/product_card.html"

        ProductFactory(name="Widget")

        def panel_links(params):
            view = ProductFilteredView()
            view.setup(rf.get("/", params))
            response = view.get(view.request)
            html = response.render().content.decode()
            panel = BeautifulSoup(html, "html.parser").find(id="filters")
            return response.context_data, panel.find_all("a")

        unfiltered_context, unfiltered_links = panel_links({})
        assert "clear_filters_url" not in unfiltered_context
        assert unfiltered_links == []

        filtered_context, filtered_links = panel_links({"name": "Widget"})
        assert [a["href"] for a in filtered_links] == [
            filtered_context["clear_filters_url"]
        ]


class TestFilterChromeOnAFilteredListView:
    @pytest.fixture
    def filtered_view(self):
        import django_filters

        from demo.models import Product
        from mvp.filters import SearchFilter, SortFilter
        from mvp.views.list import MVPListView

        class ProductFilter(django_filters.FilterSet):
            q = SearchFilter(fields=["name"])
            o = SortFilter(options=[("name", "Name", "name")])

            class Meta:
                model = Product
                fields = ["name", "price"]

        class FilteredProductView(MVPListView):
            model = Product
            filterset_class = ProductFilter
            list_item_template = "cards/product_card.html"
            paginate_by = None

        return FilteredProductView

    @pytest.mark.django_db
    def test_neither_is_drawn_when_no_filter_is_applied(self, filtered_view, rf):
        view = filtered_view()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        assert response.context_data["applied_filter_count"] == 0
        assert "clear_filters_url" not in response.context_data

    @pytest.mark.django_db
    def test_a_view_with_no_filterset_gets_no_filter_context(self, rf):
        from demo.models import Product
        from mvp.views.list import MVPListView

        class PlainProductView(MVPListView):
            model = Product

        view = PlainProductView()
        view.setup(rf.get("/"))
        context = view.get(view.request).context_data
        assert "applied_filters" not in context
        assert "applied_filter_count" not in context
        assert "clear_filters_url" not in context


class TestTableViewOrdering:
    @pytest.fixture(autouse=True)
    def require_django_tables2(self):
        pytest.importorskip("django_tables2")

    def test_the_message_names_the_class_and_where_the_ordering_belongs(self):
        from demo.models import Product
        from demo.tables import ProductTable
        from mvp.integrations.django_tables.views import MVPTableView

        with pytest.raises(ImproperlyConfigured) as excinfo:

            class BadlyOrderedTableView(MVPTableView):
                model = Product
                table_class = ProductTable
                order_by = [("name_asc", "Name (A-Z)", "name")]

        message = str(excinfo.value)
        assert "BadlyOrderedTableView" in message
        assert "Meta.order_by" in message

class TestTableViewPagination:
    def test_query_count_does_not_grow_with_the_rows_on_the_page(
        self, db, rf, django_assert_num_queries
    ):
        def render_page():
            view = _prefetching_table_view_class()()
            view.setup(rf.get("/"))
            view.request.user = AnonymousUser()
            view.get(view.request).render()

        ProductFactory()
        render_page()  # warms the caches, so the count below is steady
        with CaptureQueriesContext(connection) as one_row:
            render_page()

        ProductFactory.create_batch(2)
        with django_assert_num_queries(len(one_row)):
            render_page()

    def test_only_the_rows_on_the_page_are_fetched(self, db, rf):
        ProductFactory.create_batch(8)

        with CaptureQueriesContext(connection) as queries:
            view = _prefetching_table_view_class()()
            view.setup(rf.get("/"))
            view.request.user = AnonymousUser()
            view.get(view.request).render()

        row_queries = [
            query["sql"]
            for query in queries
            if 'FROM "demo_product"' in query["sql"] and "COUNT(" not in query["sql"]
        ]
        assert row_queries
        assert all("LIMIT" in sql for sql in row_queries)

    def test_result_count_counts_every_page_of_the_table(self, db, rf):
        ProductFactory.create_batch(8)

        context = _table_view_context(rf)

        assert context["result_count"] == 8

    def test_result_count_of_an_unpaginated_table_is_its_row_count(self, db, rf):
        ProductFactory.create_batch(8)

        context = _table_view_context(rf, paginate_by=None)

        assert context["result_count"] == 8

    @pytest.mark.parametrize("query", ["", "?sort=name"])
    def test_footer_describes_the_rows_that_are_on_the_page(self, db, rf, query):
        ProductFactory.create_batch(8)
        context = _table_view_context(rf, query)

        assert context["page_obj"] is context["table"].page
        assert context["page_obj"].paginator.count == 8
        assert (context["page_obj"].start_index(), context["page_obj"].end_index()) == (
            1,
            5,
        )

    @pytest.mark.parametrize(
        "page,expected_slice", [(1, slice(0, 5)), (2, slice(5, 8))]
    )
    def test_a_column_sort_orders_the_page_the_footer_counts(
        self, db, rf, page, expected_slice
    ):
        from demo.models import Product

        ProductFactory.create_batch(8)
        context = _table_view_context(rf, f"?sort=name&page={page}")

        rendered = [row.record.name for row in context["page_obj"].object_list]
        by_name = list(Product.objects.order_by("name").values_list("name", flat=True))
        assert rendered == by_name[expected_slice]

    @pytest.mark.parametrize("page", ["999", "0", "not-a-number"])
    def test_a_page_that_does_not_exist_is_a_missing_page(self, db, rf, page):
        from django.http import Http404

        ProductFactory.create_batch(8)

        with pytest.raises(Http404):
            _table_view_context(rf, f"?page={page}")

    def test_an_empty_page_parameter_is_the_first_page(self, db, rf):
        ProductFactory.create_batch(8)
        context = _table_view_context(rf, "?page=")

        assert context["page_obj"].number == 1

    @pytest.mark.parametrize(
        "config",
        [{"table_pagination": False}, {"paginate_by": None}],
        ids=["pagination-off", "no-page-size"],
    )
    def test_an_unpaginated_view_paginates_nowhere(self, db, rf, config):
        ProductFactory.create_batch(8)
        context = _table_view_context(rf, "", **config)

        assert context["page_obj"] is None
        assert context["is_paginated"] is False
        assert len(context["table"].rows) == 8


class TestTableViewActions:
    def _render(self, rf, **attrs):
        view_class = _plain_table_view_class()
        view = type("RenderedTableView", (view_class,), attrs)()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        return response.content.decode()

    def test_search_still_draws_when_the_view_configures_it(self, rf, db):
        assert 'name="q"' in self._render(
            rf, filterset_class=SortedProductFilter, toolbar_filters=["q"]
        )
        assert 'name="q"' not in self._render(rf)


class SortedProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    o = SortFilter(
        options=[
            ("name", "Name (A-Z)", ["name", "pk"]),
            ("-name", "Name (Z-A)", ["-name", "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields = ["status"]


class TestTableViewDropsTheSort:
    """One filterset serves a list page and a table page; the table drops its sort."""

    @pytest.fixture(autouse=True)
    def require_django_tables2(self):
        pytest.importorskip("django_tables2")

    def _table_view(self, rf, query="", **attrs):
        view_class = type(
            "SortedTableView",
            (_plain_table_view_class(),),
            {"filterset_class": SortedProductFilter, **attrs},
        )
        view = view_class()
        view.setup(rf.get(f"/{query}"))
        view.request.user = AnonymousUser()
        return view

    def _render(self, view):
        response = view.get(view.request)
        response.render()
        return response.content.decode()

    def test_a_table_on_a_filterset_with_a_sort_renders_no_sort_control(self, rf, db):
        ProductFactory(name="Lamp")

        html = self._render(self._table_view(rf))

        assert 'name="o"' not in html

    def test_a_sort_value_is_ignored_and_the_tables_ordering_stands(self, rf, db):
        for name in ("Bowl", "Chair", "Atlas"):
            ProductFactory(name=name)
        view = self._table_view(rf, "?o=name", ordering=["-name"])

        context = view.get(view.request).context_data

        rows = [row.record.name for row in context["table"].rows]
        assert rows == ["Chair", "Bowl", "Atlas"]

    def test_a_column_sort_still_orders_the_rows(self, rf, db):
        for name in ("Bowl", "Chair", "Atlas"):
            ProductFactory(name=name)
        view = self._table_view(rf, "?o=-name&sort=name")

        context = view.get(view.request).context_data

        rows = [row.record.name for row in context["table"].rows]
        assert rows == ["Atlas", "Bowl", "Chair"]

    def test_the_sort_named_for_the_toolbar_is_skipped_silently(self, rf, db):
        ProductFactory(name="Lamp")
        view = self._table_view(rf, "?o=name", toolbar_filters=["q", "o"])

        html = self._render(view)

        assert 'name="q"' in html
        assert 'name="o"' not in html

    def test_the_same_filterset_on_a_list_view_still_sorts(self, rf, db):
        for name in ("Bowl", "Chair", "Atlas"):
            ProductFactory(name=name)
        view_class = type(
            "SortedListView",
            (MVPListView,),
            {
                "model": Product,
                "filterset_class": SortedProductFilter,
                "toolbar_filters": ["q", "o"],
                "list_item_template": "cards/product_card.html",
            },
        )
        view = view_class()
        view.setup(rf.get("/?o=name"))
        view.request.user = AnonymousUser()

        response = view.get(view.request)
        response.render()

        names = [product.name for product in response.context_data["object_list"]]
        assert names == ["Atlas", "Bowl", "Chair"]
        assert 'name="o"' in response.content.decode()
