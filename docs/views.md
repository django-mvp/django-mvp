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

### Placeholder default

`MVPTemplateView` defaults `template_name` to a packaged placeholder page instead
of leaving it unset, so wiring up a menu or URL ahead of writing the real template
renders a page that says so instead of a 500:

```python
class AboutView(MVPTemplateView):
    page_title = "About us"
    # no template_name yet — renders the placeholder, not a 500
```

Set `template_name` once the real template exists. The placeholder never shows
again. Under `settings.DEBUG` the placeholder also names the view class and the
URL path that rendered it — that detail is left out in production so the
placeholder doesn't advertise internal view names.

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

The list template renders the action row (see
[`c-page.list.actions`](components.md#page-structure)), the grid, the empty state, and
pagination. `SearchMixin`, `OrderMixin` and `SearchOrderMixin` are also usable on any
plain Django `ListView`.

Each control in the action row follows the thing it drives, so there is no separate list
to keep in step with the view. `search_fields` draws the search box, `order_by` the sort
menu, a `FilterSet` the filter dialog, and `show_create_action` the add button. Leave one
unconfigured and its control does not appear.

Search reads the first ten words of `?q=` and ignores the rest. The query grows by one
branch per word per field and the term arrives from the URL, so the limit keeps its size
out of a visitor's hands. Raise `max_search_words` on the view if longer terms are
genuinely useful.

The empty state follows the create action. Its message is there to point at the "Add
new" button, so a user whose create action is hidden sees the heading on its own:

```python
from django.utils.translation import gettext_lazy as _


class ProductListView(MVPListView):
    model = Product

    empty_state_heading = _("No products")
    empty_state_message = _("Add your first product to get started.")
```

Set `empty_state_message` to `None` to drop the paragraph for everyone and leave the
heading alone. To say something to read-only visitors instead, override
`get_empty_state_message()`.

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

- **Form rendering** — always through django-crispy-forms with the Tailwind template
  pack, which is a hard runtime dependency rather than an optional integration (see
  [ADR 0006](adr/0006-crispy-forms-is-a-runtime-dependency.md)). A form carrying a
  `helper` is rendered through it; otherwise the default crispy rendering applies.
  There is no per-view renderer setting.
- **Success URL chain** — explicit `success_url` → the object's detail view → the list
  view → back where you came from. A validated `?next=` parameter (open-redirect safe,
  via `NextURLMixin`) wins over all of them.
- Model form views derive page titles and success messages from the model's
  `verbose_name`.

### A parent and its related rows

`MVPInlineCreateView` and `MVPInlineUpdateView` put a record and one or more sets of related
rows on one page, validated and saved together. Each set is declared as its own `InlineFormSet`
class and listed on `inlines`:

```python
class OrderLineInline(InlineFormSet):
    model = OrderLine
    fields = ["quantity"]


class ProductOrderLinesView(MVPInlineUpdateView):
    model = Product
    fields = ["name", "category"]
    inlines = [OrderLineInline]
```

No template markup, no formset construction, no save logic — the same page chrome, renderer
detection and success-URL chain as any other form view. `fields = []` on an update view edits
only the declared sets, leaving the parent's own fields off the page. See
[Formsets](formsets.md) for the whole path from the models to a rendered page, more than one
set on a page, the rows-only page, and the standalone case for a formset with no parent record
at all.

## Delete flows

`MVPDeleteView` handles the hard parts of deletion:

- shows a summary of related objects that will be deleted with the target,
- blocks deletion (with an explanatory page) when protected relations exist,
- optional type-to-confirm for dangerous deletes (`require_confirmation = True`).

### Type-to-confirm

Set `require_confirmation = True` and the page asks the user to type the record's name
before the Delete button becomes active. The string they must type defaults to
`str(object)`; override `get_confirmation_value()` to ask for something else, and
`confirmation_label` to change the field's label.

```python
class ProjectDeleteView(MVPDeleteView):
    model = Project
    require_confirmation = True
    confirmation_label = _("Project name")

    def get_confirmation_value(self):
        return self.object.slug
```

The check is enforced on the server as well as in the browser: a POST whose value does
not match — including an empty one — re-renders the page with an error and deletes
nothing. The browser only decides whether the button is clickable.

A record that is blocked by a protected relation asks for no confirmation, because it
offers no Delete button to enable.

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

The htmx library itself ships with django-mvp, in the bundled front-end runtime, so you
do not add a script tag for it. It runs on every page, which means `hx-*` attributes are
live anywhere in your markup. If a page of yours renders HTML you did not author, such as
user-submitted rich text, sanitize it as you already would, and be aware that `hx-*`
attributes are now among the things worth stripping. htmx's own defaults
apply unchanged, including `selfRequestsOnly`, which keeps htmx requests on your own
origin.

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
