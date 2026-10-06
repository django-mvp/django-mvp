"""Tests for mvp.integrations — guarded optional-dependency modules.

Integrations are deliberately NOT extras: each lives in a dedicated module
under mvp.integrations that core never imports, so its third-party dependency
is only required when a project explicitly imports the integration.
"""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test.utils import CaptureQueriesContext

from mvp.integrations import missing_dependency
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

    def test_core_views_do_not_export_integration_views(self):
        import mvp.views

        assert not hasattr(mvp.views, "MVPFilteredListView")
        assert not hasattr(mvp.views, "MVPTableView")
        assert "MVPFilteredListView" not in mvp.views.__all__

    def test_core_views_have_no_optional_dependency_imports(self):
        import ast
        from pathlib import Path

        import mvp

        views_dir = Path(next(iter(mvp.__path__))) / "views"
        optional = {"django_tables2", "django_filters"}

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
    def test_django_tables_integration_imports(self):
        pytest.importorskip("django_tables2")
        from mvp.integrations.django_tables.views import MVPTableView, MVPTableViewMixin

        assert MVPTableViewMixin.base_template_name == "table_view.html"
        assert issubclass(MVPTableView, MVPTableViewMixin)

    def test_django_filters_integration_imports(self):
        pytest.importorskip("django_filters")
        from django_filters.views import FilterView

        from mvp.integrations.django_filters.views import MVPFilteredListView
        from mvp.views.list import MVPListViewMixin

        assert issubclass(MVPFilteredListView, MVPListViewMixin)
        assert issubclass(MVPFilteredListView, FilterView)
        # The applied-filters context logic belongs to the core mixin, so that a
        # view composing it with FilterView gets the filter chrome too. Keeping
        # that logic on this class alone is what left the demo's own pages
        # without a filter badge. Isolation is a rule about imports, not about
        # where the code sits, and
        # TestIntegrationIsolation.test_core_views_have_no_optional_dependency_imports
        # is what enforces it.
        assert hasattr(MVPFilteredListView, "get_active_filters")
        assert hasattr(MVPListViewMixin, "get_active_filters")

    @pytest.mark.django_db
    def test_sortable_headers_render_two_distinct_sort_glyphs(self, rf):
        pytest.importorskip("django_tables2")
        from django.template import Context, Template

        from demo.tables import ProductTable

        html = Template("{% load django_tables2 %}{% render_table table %}").render(
            Context({"table": ProductTable([]), "request": rf.get("/")})
        )

        ascending = set(
            re.findall(r'<i class="([^"]*)\s+sort-icon sort-icon-asc"', html)
        )
        descending = set(
            re.findall(r'<i class="([^"]*)\s+sort-icon sort-icon-desc"', html)
        )

        assert len(ascending) == 1, (
            f"headers disagree on the ascending icon: {ascending}"
        )
        assert len(descending) == 1, (
            f"headers disagree on the descending icon: {descending}"
        )
        assert ascending != descending, (
            f"both directions render the same glyph ({ascending}), so a sorted "
            "column cannot show which way it sorted"
        )

    @pytest.mark.django_db
    def test_filtered_list_view_injects_applied_filters(self, rf):
        pytest.importorskip("django_filters")
        from demo.models import Product
        from mvp.integrations.django_filters.views import MVPFilteredListView

        class ProductFilteredView(MVPFilteredListView):
            model = Product
            filterset_fields = ["name"]

        view = ProductFilteredView()
        view.setup(rf.get("/", {"name": "Widget"}))
        response = view.get(view.request)
        context = response.context_data
        assert "applied_filters" in context

    @pytest.mark.django_db
    def test_filtered_list_view_has_no_clear_filters_url_when_nothing_applied(self, rf):
        pytest.importorskip("django_filters")
        from demo.models import Product
        from mvp.integrations.django_filters.views import MVPFilteredListView

        class ProductFilteredView(MVPFilteredListView):
            model = Product
            filterset_fields = ["name"]

        view = ProductFilteredView()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        assert "clear_filters_url" not in response.context_data

    @pytest.mark.django_db
    def test_filtered_list_view_clear_filters_url_drops_only_filter_fields(self, rf):
        pytest.importorskip("django_filters")
        from demo.models import Product
        from mvp.integrations.django_filters.views import MVPFilteredListView

        class ProductFilteredView(MVPFilteredListView):
            model = Product
            filterset_fields = ["name"]
            search_fields = ["name"]
            order_by = [("name_asc", "Name (A-Z)", "name")]
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
        assert context["applied_filter_count"] == 1
        clear_url = context["clear_filters_url"]
        assert clear_url.startswith("/?")
        query = clear_url.split("?", 1)[1]
        params = dict(pair.split("=") for pair in query.split("&"))
        assert "name" not in params
        assert "page" not in params
        assert params["q"] == "widget"
        assert params["o"] == "name_asc"

    @pytest.mark.django_db
    def test_filter_action_template_renders_clear_link_only_when_filters_applied(
        self, rf
    ):
        pytest.importorskip("django_filters")
        from demo.models import Product
        from mvp.integrations.django_filters.views import MVPFilteredListView

        class ProductFilteredView(MVPFilteredListView):
            model = Product
            filterset_fields = ["name"]
            template_name = "cotton/mvp/page/list/actions/filter.html"

        unfiltered = ProductFilteredView()
        unfiltered.setup(rf.get("/"))
        unfiltered_response = unfiltered.get(unfiltered.request)
        unfiltered_html = unfiltered_response.render().content.decode()
        assert "clear_filters_url" not in unfiltered_response.context_data
        assert 'href="/?' not in unfiltered_html

        filtered = ProductFilteredView()
        filtered.setup(rf.get("/", {"name": "Widget"}))
        filtered_response = filtered.get(filtered.request)
        filtered_html = filtered_response.render().content.decode()
        clear_url = filtered_response.context_data["clear_filters_url"]
        assert f'href="{clear_url}"' in filtered_html


class TestFilterChromeOnAComposedView:
    @pytest.fixture
    def filtered_view(self):
        pytest.importorskip("django_filters")
        from django_filters.views import FilterView

        from demo.models import Product
        from mvp.views.list import MVPListViewMixin

        class ComposedProductView(MVPListViewMixin, FilterView):
            model = Product
            filterset_fields = ["name", "price"]
            search_fields = ["name"]
            template_name = "cotton/mvp/page/list/actions/filter.html"

        return ComposedProductView

    def render(self, view_class, rf, params):
        view = view_class()
        view.setup(rf.get("/", params))
        return view.get(view.request).render().content.decode()

    @pytest.mark.django_db
    def test_the_button_is_badged_with_the_number_of_applied_filters(
        self, filtered_view, rf
    ):
        view = filtered_view()
        view.setup(rf.get("/", {"name": "Widget", "price": "9.99"}))
        context = view.get(view.request).context_data
        assert context["applied_filter_count"] == 2

    @pytest.mark.django_db
    def test_the_modal_offers_a_way_to_clear_an_applied_filter(self, filtered_view, rf):
        view = filtered_view()
        view.setup(rf.get("/", {"name": "Widget"}))
        response = view.get(view.request)
        clear_url = response.context_data["clear_filters_url"]
        html = response.render().content.decode()
        assert f'href="{clear_url}"' in html

    @pytest.mark.django_db
    def test_neither_is_drawn_when_no_filter_is_applied(self, filtered_view, rf):
        view = filtered_view()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        assert response.context_data["applied_filter_count"] == 0
        assert "clear_filters_url" not in response.context_data

    @pytest.mark.django_db
    def test_clearing_keeps_the_search_and_drops_the_filters(self, filtered_view, rf):
        view = filtered_view()
        view.setup(rf.get("/", {"q": "code", "name": "Widget", "page": "3"}))
        clear_url = view.get(view.request).context_data["clear_filters_url"]
        assert clear_url == "/?q=code"

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

    def test_declaring_an_ordering_is_refused_at_class_definition(self):
        from demo.models import Product
        from demo.tables import ProductTable
        from mvp.integrations.django_tables.views import MVPTableView

        with pytest.raises(ImproperlyConfigured, match="table"):

            class OrderedTableView(MVPTableView):
                model = Product
                table_class = ProductTable
                order_by = [("name_asc", "Name (A-Z)", "name")]

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

    def test_a_table_view_with_no_ordering_defines_and_instantiates_cleanly(self):
        view_class = _plain_table_view_class()
        view_class()  # must not raise


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
        with CaptureQueriesContext(connection) as one_row:
            render_page()

        ProductFactory.create_batch(7)
        with django_assert_num_queries(len(one_row)):
            render_page()

    @pytest.mark.parametrize("query", ["", "?sort=name", "?sort=-name"])
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

    def test_no_sort_control_is_drawn(self, rf, db):
        assert "ordering-option" not in self._render(rf)

    def test_search_still_draws_when_the_view_configures_it(self, rf, db):
        assert 'name="q"' in self._render(rf, search_fields=["name"])
        assert 'name="q"' not in self._render(rf)
