# Views

django-mvp ships enhanced class-based views so common pages work out of the box:
consistent page chrome (title, breadcrumbs), list pages with search/ordering/pagination,
styled forms with smart rendering, and safe delete flows.

**Composition model:** concrete views (`MVP*View`) are exported from `mvp.views`, along with
`MVPFormBase` and `MVPModelFormBase` — base classes for building a form view on top of a
Django base class the package doesn't ship one for. The mixins they're all built from are
importable from their own modules (`mvp.views.base`, `mvp.views.list`, ...) for composing
your own views — the standard Django pattern, no factories.

```python
from mvp.views import (
    MVPTemplateView, MVPHomeView,
    MVPListView, MVPDetailView,
    MVPFormView, MVPCreateView, MVPUpdateView, MVPDeleteView,
)
```

## Page basics

Every MVP view includes `PageMixin`, which injects a `page` context dict
(`title`, `subtitle`, `class`, `breadcrumbs`, `info`, `info_actions`) consumed by
the page templates. `breadcrumbs` is drawn by the app header rather than the page
body — see [Breadcrumbs](layout.md#breadcrumbs) — and the rest by the page itself:

```python
class AboutView(MVPTemplateView):
    template_name = "about.html"
    page_title = "About us"
    page_subtitle = "Who we are"
```

`page_class` works the same way: `get_page_class()` always prefixes it with `mvp-page`, so
`page_class = "products-list"` renders as `class="mvp-page products-list"`. There's no
`page_icon` — a couple of packaged templates read `page.icon`, but nothing sets it, so it
always renders empty.

`MVPHomeView` renders a dashboard template for authenticated users and a landing
template for anonymous visitors, from the one URL, with no redirect. Override
`dashboard_template_name` and `landing_template_name` to point at your own templates;
setting either to `None` raises `ImproperlyConfigured` instead of silently disabling that
half of the view. `get_dashboard_context()` and `get_landing_context()` are the matching
hooks — each takes the already-built context and must return it:

```python
class HomeView(MVPHomeView):
    landing_template_name = "myapp/landing.html"
    dashboard_template_name = "myapp/dashboard.html"

    def get_dashboard_context(self, context):
        context["recent"] = Order.objects.filter(user=self.request.user)[:5]
        return context  # returning None blanks the context
```

### Explaining what a page is for

`page_info` is text describing the page itself — what it shows, how to use it,
what a reader is expected to do with it. Setting it puts an info icon beside the
page title; the icon opens a dialog holding the text. Leave it unset and no icon
is drawn, which is the default on every page.

```python
class ProductListView(MVPListView):
    model = Product
    page_info = _("Every product in the catalogue. Search by name, filter by price.")
```

`page_info_actions` adds buttons to the foot of that dialog. Each entry is passed
straight to the `c-button` component, so it takes any attribute that component
takes — this is how a page points at fuller documentation rather than restating
it:

```python
class ProductListView(MVPListView):
    page_info = _("Every product in the catalogue.")
    page_info_actions = [
        {
            "text": _("Read the guide"),
            "href": "https://example.com/guide/",
            "icon": "external-link",
            "target": "_blank",
        }
    ]
```

Actions on their own render nothing: the dialog exists because there is something
to say, and the buttons follow it.

For text that has to be built when the request is served, override
`get_page_info()`. Its return value goes through the template layer like any
other context value, so a plain string is escaped and a string marked safe is
written out as markup — which is what lets a view render a template or a Markdown
source into the dialog:

```python
class ProductListView(MVPListView):
    def get_page_info(self):
        return render_to_string("products/help.html", request=self.request)
```

Only mark text safe when you control it. A value marked safe is written into the
page unescaped, so passing user-supplied content through this hook without
escaping it is an injection. `get_page_info_actions()` is the matching hook for
actions built at request time.

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

    # Whitelist-only ordering (?o=) — raw query values never reach the ORM.
    # A sequence unpacks into multiple order_by() arguments, so an entry can
    # declare a tiebreak: a single column is not a total order unless it is
    # unique, and rows tying on it can move between pages without one.
    order_by = [
        ("name_asc",  "Name (A-Z)", ["name", "pk"]),
        ("name_desc", "Name (Z-A)", ["-name", "-pk"]),
        ("newest",    "Newest first", ["-created", "-pk"]),
    ]

    # Card grid + per-item template ("<app>/<model>_list_item.html" by default)
    grid = {"md": 2, "xl": 3}
    list_item_template = "shop/product_card.html"

    # Inline "create" modal on the list page
    create_form_class = ProductForm
    show_create_action = lambda self, user: user.is_staff
```

That modal is headed "Add Product", built from the model's verbose name. Set
`create_modal_title` on the view to write the heading yourself. The button that opens it
keeps its own short label either way, so a crowded action row stays readable while the
dialog still says what it creates.

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

Overriding `get_search_fields()` alone filters `?q=` without drawing the search box — the
box's visibility reads the `search_fields` attribute directly, not the hook. Set
`search_fields` to something truthy too if you need the box to show.

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
- **Success URL chain** — a validated `?next=` (open-redirect safe, via `NextURLMixin`)
  wins first. Failing that, `success_url` is tried as a CRUD shorthand (`"list"`,
  `"detail"`, ...) through the same resolver that builds the action links, gated by the
  same `show_<action>_action` flags; when it isn't a recognised shorthand, or the flag is
  off, the raw value is used verbatim as a URL path instead. Failing that,
  `self.object.get_absolute_url()` is used if the model defines it. With nothing left to
  try, the view raises `ImproperlyConfigured`.
- Model form views derive page titles and success messages from the model's
  `verbose_name`.

Three ways to change what a form looks like, cheapest first: give the form a crispy
`helper` for layouts, rows and field ordering — set `helper.form_tag = False` since the
page already renders the `<form>` element, the submit buttons and the CSRF token; drop
`c-form.*` components into a template block and compose the parts by hand; or give the
view a `template_name` extending `form_view.html` and override its `before_form`,
`formset`, `actions` or `after_form` blocks.

### Plain form pages

`MVPFormView` is a non-model form page — Django's `FormView` with the packaged chrome.
It needs no `model`, just a `form_class` and a `success_url`:

```python
class ContactView(MVPFormView):
    form_class = ContactForm
    success_url = "/contact/success/"
    page_title = "Contact Us"
```

Its redirect chain is shorter than the model views', and its `success_url` step works
differently: `?next=` first, then `success_url` used verbatim as a URL path — unlike
`MVPCreateView`/`MVPUpdateView`, it is never tried as a CRUD shorthand first — then
`ImproperlyConfigured`. Leave `page_title` unset and it's derived from the class name
instead of a model's `verbose_name`: `ContactUsView` becomes "Contact Us View".

Page chrome that would otherwise need a model — the CSS class suffix, the list-view
breadcrumb — is simply absent on a plain `MVPFormView`, rather than erroring: no
model-derived class, and a breadcrumb trail with just the page title, no link back to a
list. Give the page a model to derive that chrome from anyway by overriding
`get_model_class()`:

```python
class ContactView(MVPFormView):
    form_class = ContactForm  # a plain forms.Form
    success_url = "/thanks/"

    def get_model_class(self):
        return Enquiry  # any model — feeds the title, breadcrumb and CSS class
```

### A parent and its related rows

`MVPCreateView` and `MVPUpdateView` put a record and one or more sets of related rows on one
page, validated and saved together — set `inlines` on the view you already have. Each set is
declared as its own `InlineFormSet` class and listed on `inlines`:

```python
class OrderLineInline(InlineFormSet):
    model = OrderLine
    fields = ["quantity"]


class ProductOrderLinesView(MVPUpdateView):
    model = Product
    fields = ["name", "category"]
    inlines = [OrderLineInline]
```

No template markup, no formset construction, no save logic — the same page chrome, renderer
detection and success-URL chain as any other form view. Leaving `inlines` unset is a no-op: the
view behaves exactly like a plain `MVPCreateView`/`MVPUpdateView`. `fields = []` on an update
view edits only the declared sets, leaving the parent's own fields off the page. See
[Formsets](formsets.md) for the whole path from the models to a rendered page, more than one
set on a page, the rows-only page, and the standalone case for a formset with no parent record
at all.

## Delete flows

`MVPDeleteView` handles the hard parts of deletion:

- shows a summary of related objects that will be deleted with the target,
- blocks deletion (with an explanatory page) when `PROTECT` or `RESTRICT` relations exist,
- optional type-to-confirm for dangerous deletes (`require_confirmation = True`).

A blocked delete re-renders the same page with a 200 rather than redirecting or raising —
the POST that triggered it never reaches Django's own `ProtectedError` or `RestrictedError`.

A successful delete's redirect chain differs from the other form views' at its last step:
without an explicit `success_url`, it lands on the registered list URL rather than
`get_absolute_url()` — there's no object left to link a detail page to once it's deleted.

### Related-objects summary

Set `show_related_objects = True` and the page lists what the cascade will take with the
target, grouped by model and capped at `related_objects_max_per_group` (default 25, with
an overflow count past the cap). It renders as an info-style alert by default — right for
routine cleanup, where the cascade is expected and unremarkable.

Some cascades are not routine: deleting a record can take irreplaceable data with it.
`related_objects_attrs` is handed straight to that alert, so anything the alert component
accepts can be set from the view without touching the shell's markup:

```python
class DatasetDeleteView(MVPDeleteView):
    model = Dataset
    show_related_objects = True
    related_objects_attrs = {"variant": "warning"}
```

Setting it replaces the default rather than adding to it, so state every attribute you
want — `{"class": "mt-4"}` alone gives you an alert with no variant. Presentation only:
the collector, the cap and the overflow count are unchanged.

### Type-to-confirm

Set `require_confirmation = True` and the page asks the user to type the record's name
before the Delete button becomes active. The string they must type defaults to
`str(object)`; override `get_confirmation_value()` to ask for something else, and
`confirmation_label` to change the field's label.

```python
class ProductDeleteView(MVPDeleteView):
    model = Product
    require_confirmation = True
    confirmation_label = _("Product SKU")

    def get_confirmation_value(self):
        return self.object.sku
```

The check is enforced on the server as well as in the browser: a POST whose value does
not match — including an empty one — re-renders the page with an error and deletes
nothing. The browser only decides whether the button is clickable.

A record that is blocked by a protected relation asks for no confirmation, because it
offers no Delete button to enable.

### Reaching it from the update page

`MVPUpdateView` draws its own Delete button next to the save buttons, from a `delete_url`
context key gated by `show_delete_action` — empty, and the button absent, when that flag
is off. The link carries two query parameters the delete page reads back: `back`, this
update page's own URL (resolved directly, not gated by `show_update_action`, so leaving
that flag at its default `False` doesn't blank the link), and `next`, the list URL.
`get_back_url()` on the delete view reads `back`, validates it against the current host,
and falls back to the list URL when it's absent, then to the object's own
`get_absolute_url()` when there is no list URL either — the record still exists at the
moment the page is drawn. No Back button renders when neither is available; `next` feeds
the usual `?next=` handling for the post-delete redirect.

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

`MVPDetailView`'s own page title is `str(self.object)`, and its CSS class carries a
`<model_name>-page` suffix alongside `mvp-page`. Its `directory` defaults to
`["update", "delete"]` — list is deliberately absent, since the breadcrumb trail already
links it. `list_view_title` overrides the label on that breadcrumb link; left unset, it
falls back to `verbose_name_plural.title()`.

Each action's URL kwargs come from `get_url_kwargs(action)`, which defaults to `{}` for
`list` and `create` and `self.kwargs` for everything else. Override it for nested URL
patterns, branching on `action`; returning `None` suppresses that action's link silently,
with no error. Short of that, a shown action whose URL name isn't registered raises
`NoReverseMatch` instead of quietly dropping the link, so a misconfigured route surfaces
rather than vanishing.

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

> **Renamed in 0.16, and the old names are no longer read.** These attributes
> were `has_<action>_permission`. A view that still sets one raises
> `ImproperlyConfigured` naming the view and the attribute to rename. It raises
> rather than ignoring the old name, because ignoring it would draw a link the
> project had switched off. Renaming the attribute is the whole migration — the
> accepted values and the callable signature are unchanged.

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
origin. While a request is in flight the header shows a spinner, described in
[Loading indicator](layout.md#loading-indicator).

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
