# Integrations

django-mvp integrates with third-party packages the same way across the board:
**guarded modules, not packaging extras.** Each integration lives in its own module
under `mvp.integrations`, is never imported by the core package, and only requires its
third-party dependency when *you* import it. Importing without the dependency raises
`ImproperlyConfigured` with install instructions.

```text
mvp/integrations/
├── django_tables/     requires django-tables2
└── django_filters/    requires django-filter
```

## django-tables2

```bash
pip install django-tables2
```

```python
from mvp.integrations.django_tables.views import MVPTableView


class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    search_fields = ["name"]
```

`MVPTableView` combines the full MVP list behavior (search, ordering, pagination, page
chrome) with django-tables2 rendering via the `table_view.html` base template and the
[`c-addons.django-table`](components.md#actions-user-misc) component.
`MVPTableViewMixin` is available for composing with other view classes.

## django-filter

```bash
pip install django-filter
```

```python
from mvp.integrations.django_filters.views import MVPFilteredListView


class ProductListView(MVPFilteredListView):
    model = Product
    filterset_class = ProductFilter   # or filterset_fields = [...]
    search_fields = ["name"]
```

On top of `MVPListView` behavior, the view injects `applied_filters` /
`applied_filter_count` into the context, which the list page's filter button uses to
badge the number of active filters.

## Crispy forms

Form rendering is runtime-detected rather than module-guarded: install
[django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms) with
the Tailwind template pack and MVP form views pick it up automatically:

```bash
pip install django-crispy-forms crispy-tailwind
```

```python
INSTALLED_APPS += ["crispy_forms", "crispy_tailwind"]
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"
```

See [Views — forms](views.md#forms-create--update--generic) for the renderer
resolution order.

## Writing your own integration

Follow the same pattern in your project (or in a PR):

```python
# mvp/integrations/<package>/views.py
from mvp.integrations import missing_dependency

try:
    from some_package import Something
except ImportError as e:
    raise missing_dependency("<package>", "some-package") from e
```

django-mvp deliberately only ships integrations for packages used across its author's
projects — anything else belongs in your own codebase, following this pattern.
