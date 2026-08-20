"""Tests for mvp.integrations — guarded optional-dependency modules.

Integrations are deliberately NOT extras: each lives in a dedicated module
under mvp.integrations that core never imports, so its third-party dependency
is only required when a project explicitly imports the integration.
"""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured

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
    """Core views never import an optional integration."""

    def test_missing_dependency_message_names_module_and_pip_package(self):
        err = missing_dependency("django_tables", "django-tables2")
        assert isinstance(err, ImproperlyConfigured)
        assert "mvp.integrations.django_tables" in str(err)
        assert "pip install django-tables2" in str(err)

    def test_core_views_do_not_export_integration_views(self):
        """Integration views must not leak into the core public API."""
        import mvp.views

        assert not hasattr(mvp.views, "MVPFilteredListView")
        assert not hasattr(mvp.views, "MVPTableView")
        assert "MVPFilteredListView" not in mvp.views.__all__

    def test_core_views_have_no_optional_dependency_imports(self):
        """No module under mvp/views/ may contain an import of an optional package.

        Optional-package imports belong exclusively in mvp/integrations/ — that is
        the whole point of the guarded-module design.
        """
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
    """Each guarded integration module imports and works when its package is present."""

    def test_django_tables_integration_imports(self):
        """With django-tables2 installed (dev env), the integration works."""
        pytest.importorskip("django_tables2")
        from mvp.integrations.django_tables.views import MVPTableView, MVPTableViewMixin

        assert MVPTableViewMixin.base_template_name == "table_view.html"
        assert issubclass(MVPTableView, MVPTableViewMixin)

    def test_django_filters_integration_imports(self):
        """With django-filter installed (dev env), the integration works."""
        pytest.importorskip("django_filters")
        from django_filters.views import FilterView

        from mvp.integrations.django_filters.views import MVPFilteredListView
        from mvp.views.list import MVPListViewMixin

        assert issubclass(MVPFilteredListView, MVPListViewMixin)
        assert issubclass(MVPFilteredListView, FilterView)
        # the applied-filters context logic moved here from MVPListViewMixin
        assert hasattr(MVPFilteredListView, "get_active_filters")
        assert not hasattr(MVPListViewMixin, "get_active_filters")

    @pytest.mark.django_db
    def test_sortable_headers_render_two_distinct_sort_glyphs(self, rf):
        """A sortable header carries both directions and shows one at a time.

        Which one shows is decided by CSS from the ``.asc``/``.desc`` class
        django-tables2 puts on the cell, so if the two resolve to the same
        glyph the header looks right until a column is clicked and then never
        changes. That is what was reported.

        Deliberately asserts the two differ rather than naming the glyphs. The
        icon classes are configuration a project is free to replace, so pinning
        them here would fail the next time the pack changes without anything
        being wrong.
        """
        pytest.importorskip("django_tables2")
        from django.template import Context, Template

        from demo.tables import ProductTable

        html = Template("{% load django_tables2 %}{% render_table table %}").render(
            Context({"table": ProductTable([]), "request": rf.get("/")})
        )

        ascending = set(re.findall(r'<i class="([^"]*)\s+sort-icon sort-icon-asc"', html))
        descending = set(re.findall(r'<i class="([^"]*)\s+sort-icon sort-icon-desc"', html))

        assert len(ascending) == 1, f"headers disagree on the ascending icon: {ascending}"
        assert len(descending) == 1, f"headers disagree on the descending icon: {descending}"
        assert ascending != descending, (
            f"both directions render the same glyph ({ascending}), so a sorted "
            "column cannot show which way it sorted"
        )

    @pytest.mark.django_db
    def test_filtered_list_view_injects_applied_filters(self, rf):
        """MVPFilteredListView adds applied_filters context for the filter badge."""
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
        assert context["applied_filter_count"] == len(context["applied_filters"])


class TestTableViewOrdering:
    """A table view class must not declare its own ordering — that belongs
    on the table class, which already has a safe, whitelisted mechanism for
    it. Red before the view mixin refuses the declaration."""

    def test_declaring_an_ordering_is_refused(self):
        pytest.importorskip("django_tables2")
        from demo.models import Product
        from demo.tables import ProductTable
        from mvp.integrations.django_tables.views import MVPTableView

        class OrderedTableView(MVPTableView):
            model = Product
            table_class = ProductTable
            order_by = [("name_asc", "Name (A-Z)", "name")]

        with pytest.raises(ImproperlyConfigured, match="table"):
            OrderedTableView()

    def test_a_table_view_with_no_ordering_instantiates_cleanly(self):
        view_class = _plain_table_view_class()
        view_class()  # must not raise


class TestTableViewPagination:
    """A table page runs its row query, and any prefetches on it, once.

    Red before the mixin owns a single paginator: ``ListView`` slices the
    queryset for ``page_obj`` and django-tables2 slices it again for the
    table, and a slice of a queryset cannot reuse the first slice's result
    cache (issue #276).
    """

    def test_row_query_and_prefetches_run_once_per_page(
        self, db, rf, django_assert_num_queries
    ):
        ProductFactory.create_batch(8)
        view = _prefetching_table_view_class()()
        view.setup(rf.get("/"))
        view.request.user = AnonymousUser()

        # One COUNT for the paginator, one SELECT for the page's rows, one
        # SELECT for the prefetched categories.
        with django_assert_num_queries(3):
            view.get(view.request).render()

    @pytest.mark.parametrize("query", ["", "?sort=name", "?sort=-name"])
    def test_footer_describes_the_rows_that_are_on_the_page(self, db, rf, query):
        """The footer reads ``page_obj``, so its page has to be the table's
        page — including under a column sort, which only the table applies."""
        ProductFactory.create_batch(8)
        context = _table_view_context(rf, query)

        assert context["page_obj"] is context["table"].page
        assert context["page_obj"].paginator.count == 8
        assert (context["page_obj"].start_index(), context["page_obj"].end_index()) == (
            1,
            5,
        )

    @pytest.mark.parametrize("page,expected_slice", [(1, slice(0, 5)), (2, slice(5, 8))])
    def test_a_column_sort_orders_the_page_the_footer_counts(
        self, db, rf, page, expected_slice
    ):
        """Under a sort, a page holds its own rows in that order — not the
        equivalent slice of the view's own ordering."""
        from demo.models import Product

        ProductFactory.create_batch(8)
        context = _table_view_context(rf, f"?sort=name&page={page}")

        rendered = [row.record.name for row in context["page_obj"].object_list]
        by_name = list(Product.objects.order_by("name").values_list("name", flat=True))
        assert rendered == by_name[expected_slice]

    @pytest.mark.parametrize("page", ["999", "0", "not-a-number"])
    def test_a_page_that_does_not_exist_is_a_missing_page(self, db, rf, page):
        """A list view in this package answers ``?page=999`` with a 404, and a
        table view has to agree — django-tables2 would otherwise land quietly
        on the last page."""
        from django.http import Http404

        ProductFactory.create_batch(8)

        with pytest.raises(Http404):
            _table_view_context(rf, f"?page={page}")

    def test_an_empty_page_parameter_is_the_first_page(self, db, rf):
        """``?page=`` names no page rather than a bad one, exactly as an
        absent parameter does."""
        ProductFactory.create_batch(8)
        context = _table_view_context(rf, "?page=")

        assert context["page_obj"].number == 1

    @pytest.mark.parametrize(
        "config",
        [{"table_pagination": False}, {"paginate_by": None}],
        ids=["pagination-off", "no-page-size"],
    )
    def test_an_unpaginated_view_paginates_nowhere(self, db, rf, config):
        """Turning pagination off, or naming no page size at all, leaves the
        table whole and the page chrome with nothing to describe. Red before
        the mixin owned the decision: the table paginated at its own default
        while the view believed it was unpaginated."""
        ProductFactory.create_batch(8)
        context = _table_view_context(rf, "", **config)

        assert context["page_obj"] is None
        assert context["is_paginated"] is False
        assert len(context["table"].rows) == 8


class TestTableViewActions:
    """A table view draws no sort control, and does so for the same reason a
    list view does — nothing configured it.

    ``order_by`` is refused on a table view, so ``order_by_choices`` is never
    in its context and the sort action's own condition is false. This used to
    be stated twice: once by that refusal, and again by a shorter action list
    on the view. The list is gone, so the two can no longer disagree."""

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

    def test_the_view_carries_no_action_list_of_its_own(self):
        """The list view sets none either — both read the same sub-components."""
        from mvp.views.list import MVPListViewMixin

        view = _plain_table_view_class()()
        assert not hasattr(view, "actions")
        assert not hasattr(MVPListViewMixin, "actions")
