"""Tests for mvp.integrations — guarded optional-dependency modules.

Integrations are deliberately NOT extras: each lives in a dedicated module
under mvp.integrations that core never imports, so its third-party dependency
is only required when a project explicitly imports the integration.
"""

import pytest
from django.core.exceptions import ImproperlyConfigured

from mvp.integrations import missing_dependency


def test_missing_dependency_message_names_module_and_pip_package():
    err = missing_dependency("django_tables", "django-tables2")
    assert isinstance(err, ImproperlyConfigured)
    assert "mvp.integrations.django_tables" in str(err)
    assert "pip install django-tables2" in str(err)


def test_core_views_do_not_export_integration_views():
    """Integration views must not leak into the core public API."""
    import mvp.views

    assert not hasattr(mvp.views, "MVPFilteredListView")
    assert not hasattr(mvp.views, "MVPTableView")
    assert "MVPFilteredListView" not in mvp.views.__all__


def test_core_views_have_no_optional_dependency_imports():
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
                    f"{module_path.name} imports optional package '{name}' — "
                    "move that code to mvp/integrations/"
                )


def test_django_tables_integration_imports():
    """With django-tables2 installed (dev env), the integration works."""
    pytest.importorskip("django_tables2")
    from mvp.integrations.django_tables.views import MVPTableView, MVPTableViewMixin

    assert MVPTableViewMixin.base_template_name == "table_view.html"
    assert issubclass(MVPTableView, MVPTableViewMixin)


def test_django_filters_integration_imports():
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
def test_filtered_list_view_injects_applied_filters(rf):
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
