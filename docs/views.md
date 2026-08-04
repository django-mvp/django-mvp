# Views

django-mvp ships enhanced class-based views so common pages work out of the box:
consistent page chrome (title, breadcrumbs), list pages with search/ordering/pagination,
styled forms with smart rendering, and safe delete flows.

**Composition model:** concrete views (`MVP*View`) are exported from `mvp.views`;
the mixins they're built from are importable from their modules
(`mvp.views.base`, `mvp.views.list`, ...) for composing your own views — the standard
Django pattern, no factories.

```python
from mvp.views import (
    MVPTemplateView, MVPHomeView,
    MVPListView, MVPDetailView,
    MVPFormView, MVPCreateView, MVPUpdateView, MVPDeleteView,
)
```

## Page basics

Every MVP view includes `PageMixin`, which injects a `page` context dict
(`title`, `subtitle`, `class`, `breadcrumbs`) consumed by the page templates:

```python
class AboutView(MVPTemplateView):
    template_name = "about.html"
    page_title = "About us"
    page_subtitle = "Who we are"
```

`MVPHomeView` renders a dashboard template for authenticated users and a landing
template for anonymous visitors.

## List pages

```python
class ProductListView(MVPListView):
    model = Product
    # done — paginated (24/page), with an empty state and page chrome
```

Add behavior declaratively:

```python
class ProductListView(MVPListView):
    model = Product

    # Django-admin-style multi-word search (?q=)
    search_fields = ["name", "description", "owner__username"]

    # Whitelist-only ordering (?o=) — raw query values never reach the ORM
    order_by = [
        ("name_asc",  "Name (A-Z)", "name"),
        ("name_desc", "Name (Z-A)", "-name"),
        ("newest",    "Newest first", "-created"),
    ]

    # Card grid + per-item template ("<app>/<model>_list_item.html" by default)
    grid = {"md": 2, "xl": 3}
    list_item_template = "shop/product_card.html"

    # Inline "create" modal on the list page
    create_form_class = ProductForm
    show_create_action = lambda self, user: user.is_staff
```

The list template renders the action row (`search`, `sort`, `create`, `filter` —
see [`c-page.list.actions`](components.md#page-structure)), the grid, the empty state,
and pagination. `SearchMixin`, `OrderMixin` and `SearchOrderMixin` are also usable on
any plain Django `ListView`.

For filtering with django-filter or table rendering with django-tables2, see
[Integrations](integrations.md).

## Forms: create / update / generic

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "category", "price"]

class ProductUpdateView(MVPUpdateView):
    model = Product
    form_class = ProductForm
```

- **Renderer auto-detection** — forms render via django-crispy-forms or django-formset
  when installed, falling back to Django's standard rendering. Override per view with
  `form_renderer = "crispy" | "formset" | "django"`.
- **Success URL chain** — explicit `success_url` → the object's detail view → the list
  view → back where you came from. A validated `?next=` parameter (open-redirect safe,
  via `NextURLMixin`) wins over all of them.
- Model form views derive page titles and success messages from the model's
  `verbose_name`.

## Delete flows

`MVPDeleteView` handles the hard parts of deletion:

- shows a summary of related objects that will be deleted with the target,
- blocks deletion (with an explanatory page) when protected relations exist,
- optional type-to-confirm for dangerous deletes (`require_confirmation = True`).

## Detail pages and CRUD URLs

`MVPDetailView` (via `CRUDDirectoryMixin`) builds a `directory` of CRUD URLs for the
current object — each gated by a `show_<action>_action` check — which the templates
use for edit/delete buttons. Each flag is a boolean or a callable taking the request
user. URL names are resolved from `MVP_CONFIG`:

```python
MVP_CONFIG = {
    "view_names": {
        "list": "{model_name}-list",      # defaults shown
        "detail": "{model_name}-detail",
        "create": "{model_name}-create",
        "update": "{model_name}-update",
        "delete": "{model_name}-delete",
    },
}
```

### Action links are not access control

`show_<action>_action` decides whether a link is drawn on the page you are looking at.
It has no effect on the view that link points at. The two live on different classes:

```python
class ProductDetailView(MVPDetailView):
    model = Product

    def show_delete_action(self, user):
        return user.is_staff  # hides the button on this page


class ProductDeleteView(PermissionRequiredMixin, MVPDeleteView):
    model = Product
    permission_required = "shop.delete_product"  # refuses the request
```

Without that second half, anyone who knows or guesses the URL can POST to the delete
view whether or not the button was drawn for them. django-mvp deliberately ships no
authorization layer of its own. Reach for:

- `LoginRequiredMixin`, for pages that need any authenticated user.
- `PermissionRequiredMixin`, for Django's model-level permissions.
- `UserPassesTestMixin`, for a one-off predicate.
- [django-guardian](https://django-guardian.readthedocs.io/) or
  [django-rules](https://github.com/dfunckt/django-rules), for object-level rules.

Where the predicate already exists on the target view, call it from the display flag so
the rule stays in one place:

```python
def show_delete_action(self, user):
    return user.has_perm("shop.delete_product")
```

> **Renamed in 0.16.** These attributes were `has_<action>_permission`. The old names
> still work and still decide visibility, and are removed in 0.18. Using one raises
> `mvp.warnings.MVPDeprecationWarning`. Python ignores that by default, as it does any
> `DeprecationWarning`, so add
> `filterwarnings = ["error::mvp.warnings.MVPDeprecationWarning"]` to your pytest config
> to find every call site at once.

## htmx

With [django-htmx](https://django-htmx.readthedocs.io/) installed and its middleware
active, `HtmxFormMixin` (`mvp.views.htmx`) upgrades form views: invalid submissions
re-render only the form partial, successful ones return an `HX-Redirect` or a
success partial, and server-triggered events go out via `HX-Trigger`. The views degrade
gracefully when the request isn't from htmx.

## Error handlers

```python
# urls.py
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```

Styled error pages, no sidebar, with a home link and (on the 500 page) a support
contact from `DEFAULT_FROM_EMAIL`.
