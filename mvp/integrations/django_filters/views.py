"""django-filter integration: filterable list views.

Usage::

    from mvp.integrations.django_filters.views import MVPFilteredListView


    class ProductListView(MVPFilteredListView):
        model = Product
        filterset_class = ProductFilter
"""

from mvp.integrations import missing_dependency
from mvp.views.list import MVPListViewMixin

try:
    from django_filters.views import FilterView
except ImportError as e:
    raise missing_dependency("django_filters", "django-filter") from e


class MVPFilteredListView(MVPListViewMixin, FilterView):
    """List view combining MVP list behavior with django-filter's FilterView."""

    def get_context_data(self, **kwargs):
        """Add ``applied_filters`` / ``applied_filter_count`` to the context.

        Consumed by ``c-page.list.actions.filter`` to badge the filter button
        with the number of active filters.
        """
        context = super().get_context_data(**kwargs)
        if context.get("filter", None):
            active = self.get_active_filters()
            context["applied_filters"] = active
            context["applied_filter_count"] = len(active)
        return context

    def get_active_filters(self):
        """Return a dict of filters that are actually applied.

        Filters out empty / null / default-like values.
        """
        active = {}
        if not hasattr(self.filterset.form, "cleaned_data"):
            return active

        for name, value in self.filterset.form.cleaned_data.items():
            if value in (None, "", [], (), False):
                continue
            active[name] = value

        return active
