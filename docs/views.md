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
    PageWidth,
)
```

## Page basics

Every MVP view includes `PageMixin`, which injects a `page` context dict
(`title`, `subtitle`, `class`, `width`, `breadcrumbs`, `info`, `info_actions`) consumed by
the page templates. `breadcrumbs` is drawn by the app header rather than the page
body — see [Breadcrumbs](layout.md#breadcrumbs), which also covers giving a page its
trail from a template — and the rest by the page itself:

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

### Page width

`page_width` sets how wide the page's content is. It takes a `PageWidth`:

| Value | Width | Default for |
| --- | --- | --- |
| `PageWidth.NARROW` | A 672px column (`max-w-2xl`) | Form, create, update and delete pages |
| `PageWidth.MEDIUM` | An 896px column (`max-w-4xl`) | |
| `PageWidth.WIDE` | The standard container, which steps with the screen up to 1536px | Every other page |
| `PageWidth.FULL` | The whole screen | |

Every width is centred, and every width fills a screen narrower than itself.

```python
from mvp.views import MVPUpdateView, PageWidth


class OrderLinesView(MVPUpdateView):
    model = Order
    page_width = PageWidth.MEDIUM
```

The width is always the view's choice. No packaged template widens a page because of what
it contains, so a form with fields side by side or a row of related records stays in the
narrow column until its view asks for more room. Override `get_page_width()` when the width
depends on the request or the object. A value outside the four raises `ValueError`.

`MVPTableView` fills the screen in both directions and ignores `page_width`. A page written
by hand asks for the same widths with
[`<c-mvp.container width="...">`](components.md#layout-primitives).

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

`SearchMixin`, `OrderMixin` and `SearchOrderMixin` are also usable on any plain Django
`ListView`.

### How a list page is laid out

From top to bottom, the list template draws:

1. **The title row.** The title, with the add button at the end of the same row at every
   screen width.
2. **The toolbar.** The search box, a count of what the list holds, then the sort and
   filter controls. It is one row on a wide screen. On a phone the search box takes the
   first row and the count shares the second with sort and filter.
3. **What is narrowing the list.** The search term and each applied filter, each drawn as
   a control that removes it. Two or more also get a single "Clear all".
4. **The results**, or the empty state.
5. **The pager**, only when there is more than one page. A wide screen gets the range
   being shown and numbered pages. A phone gets Previous, "Page 2 of 6" and Next.

Each control follows the thing it drives, so there is no separate list to keep in step
with the view. `search_fields` draws the search box, `order_by` the sort menu, a
`FilterSet` the filter dialog, and `show_create_action` the add button. Leave one
unconfigured and its control does not appear. A list with no records and nothing applied
draws no toolbar at all, since there is nothing to search or sort.

The count reads "32 products" from the model's verbose name. Once a search or filter is
applied it reads "3 results". On a paginated list the browser title also carries the
page, as in "Products (page 2 of 4)".

### What the view tells the template

Three context keys describe the state of the list:

| Key | Value |
| --- | --- |
| `result_count` | How many records the list holds across every page, after search and filters |
| `refinements` | What is narrowing the list: the search first, then each applied filter. Empty when nothing is applied |
| `clear_refinements_url` | The current URL with the search and every filter removed, and the ordering kept. Present only when `refinements` is not empty |

Each entry in `refinements` is a dict:

| Key | Value |
| --- | --- |
| `kind` | `"search"` or `"filter"` |
| `name` | `"q"` for the search, the filter's name otherwise |
| `label` | The words that name it: "Search", or the filter field's label |
| `value` | The value as the reader chose it. A choice shows its label and a related record its string form, never the stored key |
| `params` | The query parameters it occupies. A range filter has two |
| `remove_url` | The current URL without this one entry. Everything else is kept, and the page number is dropped |

Override `get_refinements(context)` to add an entry of your own, such as a date range
read from the URL, and the page draws it with the rest:

```python
class ProductListView(MVPListView):
    model = Product

    def get_refinements(self, context):
        refinements = super().get_refinements(context)
        if year := self.request.GET.get("year"):
            refinements.append({
                "kind": "filter",
                "name": "year",
                "label": _("Year"),
                "value": year,
                "params": ["year"],
                "remove_url": self.get_url_without("year"),
            })
        return refinements
```

`get_url_without(*params)` returns the current URL with those query parameters and the
page number removed.

### Replacing part of the page

Every part of the list template is a block, so a project template that extends
`list_view.html` can replace one part and keep the rest:

| Block | Holds |
| --- | --- |
| `page.title` | The title, subtitle and info icon |
| `page.actions` | The add button |
| `page.toolbar` | The whole toolbar row |
| `page.search` | The search box, inside the toolbar |
| `page.summary` | The count, inside the toolbar |
| `page.controls` | Sort and filter, inside the toolbar |
| `page.refinements` | The applied search and filters |
| `page.results` | The grid of records |
| `page.empty` | The empty state, inside the results |
| `page.pagination` | The pager |

```html
{% extends "list_view.html" %}
{% block page.controls %}
  {{ block.super }}
  <c-button size="sm" icon="download" text="Export" href="{% url 'product-export' %}" />
{% endblock page.controls %}
```

Replacing an outer block replaces the blocks inside it: a template that overrides
`page.toolbar` draws its own search, count and controls.

Search reads the first ten words of `?q=` and ignores the rest. The query grows by one
branch per word per field and the term arrives from the URL, so the limit keeps its size
out of a visitor's hands. Raise `max_search_words` on the view if longer terms are
genuinely useful.

There are two empty states. A list with no records shows the heading and message below,
with an "Add new" button that opens the inline create dialog when the page has one. A
list whose search or filters match nothing says so instead, and offers to clear them.

The first follows the create action. Its message is there to point at the "Add new"
button, so a user whose create action is hidden sees the heading on its own:

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

- **Form rendering** — always through django-crispy-forms with the `daisyui` template
  pack from django-mvp-forms, which is a hard runtime dependency rather than an optional
  integration (see [ADR 0029](adr/0029-forms-are-drawn-by-django-mvp-forms.md)). A form carrying a
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
`c-mvp.form.*` components into a template block and compose the parts by hand; or give the
view a `template_name` extending `form_view.html` and override its `before_form`,
`formset`, `actions` or `after_form` blocks.

Every form page is drawn in one centred column, narrower than a list or detail page. See
[Form pages sit in a narrower column](layout.md#form-pages-sit-in-a-narrower-column).

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
accepts can be set from the view without touching the shell's markup. The alert is
daisy-cotton's, and its `variant` is one of `info`, `success`, `warning` or `error`:

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
