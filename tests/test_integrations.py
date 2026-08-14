"""Tests for mvp.integrations — guarded optional-dependency modules.

Integrations are deliberately NOT extras: each lives in a dedicated module
under mvp.integrations that core never imports, so its third-party dependency
is only required when a project explicitly imports the integration.
"""

import re

import pytest
from django.core.exceptions import ImproperlyConfigured

from mvp.integrations import missing_dependency


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
