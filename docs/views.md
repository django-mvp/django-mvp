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
(`title`, `title_args`, `title_layout`, `class`, `width`, `breadcrumbs`, `info`, `info_actions`) consumed by
the page templates. `breadcrumbs` is drawn by the app header rather than the page
body — see [Breadcrumbs](layout.md#breadcrumbs), which also covers giving a page its
trail from a template — and the rest by the page itself:

```python
class AboutView(MVPTemplateView):
    template_name = "about.html"
    page_title = "About us"
    page_eyebrow = "Company"
    page_lead = "Who we are"
```

The page's title draws from six arguments. Each is a class attribute with a `get_*()` method
that returns it, so a subclass changes one argument in one line, and a method serves a value
that depends on the request or the object:

| Attribute | Method | What it is |
| --- | --- | --- |
| `page_eyebrow` | `get_page_eyebrow()` | A short line above the title, such as a category |
| `page_title` | `get_page_title()` | The heading's text |
| `page_lead` | `get_page_lead()` | A sentence or two under the title |
| `page_actions` | `get_page_actions()` | The page's own buttons, a list of dicts spread onto `c-button` |
| `page_info` | `get_page_info()` | The text of the info dialog (see below) |
| `page_info_actions` | `get_page_info_actions()` | The buttons at the foot of that dialog |

All six are empty by default, and the title draws nothing for an empty one. A page whose
view sets none of them but its title looks as it always did.

`page_actions` takes the same keys as `page_info_actions`. Every key is written into the
button's attributes, so never put user data in one.

`get_page_title_args()` gathers the six into the dict the page templates read as
`page.title_args`. Override it to set the whole title at once; what it returns is what the
title area draws. The browser tab and the share menu still read `get_page_title()`, so
override that to retitle the whole page:

```python
class OrderDetailView(MVPDetailView):
    def get_page_title_args(self):
        args = super().get_page_title_args()
        args["eyebrow"] = self.object.customer.name
        args["lead"] = f"Placed {self.object.placed_at:%d %B %Y}"
        return args
```

Each view type has a `page_type`: `page` on `MVPTemplateView` and any view that is none of
the others, `form` on the create, update and form views, `detail`, `delete`, `list` and
`table`. It is how [`MVP_CONFIG["page_title"]["layout"]`](configuration.md#page_titlelayout)
picks the layout a view's title is drawn in, so a project can give list pages one layout and
every other page another. A view of your own that matches none of them sets `page_type` to
the one it is closest to, or to a name it adds to that setting. A page type the setting does
not name draws `default`.

To choose the layout for one view, set `page_title_layout`. It wins over the setting:

```python
class WelcomeView(MVPTemplateView):
    page_title = "Welcome"
    page_title_layout = "centred"
```

A layout that depends on the request or the object comes from `get_page_title_layout()`, which
returns the attribute when it is set and the setting otherwise. A name is one of the shipped
layouts, `default`, `inline`, `centred` and `compact`, or a Cotton component of your own,
found under `cotton/` as `<name>.html` or `<name>/index.html`. A name that is neither raises
`ImproperlyConfigured` when the page is rendered, and the message names the value and the view
class.

The subtitle is now the lead: `page_lead` and `get_page_lead()` replace the old attribute and
its method. The old name is gone, not deprecated, so a view that still sets it draws no lead.

Where the actions are drawn depends on the page. A page, form or delete page draws them in
the title area. A detail page draws them there too, in front of its Edit and Delete buttons.
A list or table page draws them in the toolbar, before the Add button, whatever the title
layout, and leaves the title area without actions.

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

    # Every search, sort and filter comes from one filterset (below)
    filterset_class = ProductFilter

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

### Searching, sorting and filtering with a filterset

A list page takes every search, sort and filter it offers from one
[django-filter](https://django-filter.readthedocs.io/) filterset. The package ships two
filters for it, in `mvp.filters`:

```python
import django_filters
from django.utils.translation import gettext_lazy as _

from mvp.filters import SearchFilter, SortFilter


class ProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name", "description", "category__name"])
    o = SortFilter(
        options=[
            ("name", _("Name (A-Z)"), ["name", "pk"]),
            ("-name", _("Name (Z-A)"), ["-name", "-pk"]),
            ("-created", _("Newest first"), ["-created", "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields = ["status", "category"]


class ProductListView(MVPListView):
    model = Product
    filterset_class = ProductFilter
```

Name the search `q` and the sort `o`, as above, and the address reads the way it always
has: `?q=lamp&o=-created`.

| Filter | Arguments | What it does |
| --- | --- | --- |
| `SearchFilter` | `fields`, the ORM paths to search; `max_words`, default `10`; `label`, default "Search" | Ignoring case, keeps a record in which some word of the term appears in some named field, once, however many fields or joined rows it matched. Only the first `max_words` words are searched: the query grows by one branch per word per field and the term arrives from the URL, so the limit keeps its size out of a visitor's hands. An empty term narrows nothing |
| `SortFilter` | `options`, a list of `(key, label, columns)`; `label`, default "Sort" | Orders the list by the chosen option's `columns`, one expression or a sequence, the later ones deciding ties. Only the key ever appears in the address and the columns never come from it. The first choice is empty, labelled "Default order" (`empty_label`), and sends no sort |

A single column is not a total order unless it is unique, and rows tying on it can move
between pages, so end each option's columns with a unique one, usually `"pk"`.

`filterset_fields = ["status", "category"]` on the view, in place of `filterset_class`,
has django-filter generate a filterset from those model fields, and it works the same
way. A view with neither has no filter form and no filter context. The view builds the
filterset once per request, from `request.GET`, over the view's `get_queryset()`, as
django-filter's `FilterView` does. A view that scopes its records in `get_queryset()`
scopes the list and the context's `filter.qs` alike. Override `get_filterset_class()` or
`get_filterset()` to change either.

A filter on a related field offers every row of the related model, in the filter panel and
in the toolbar. When the related rows belong to a user, declare the filter on a
`filterset_class` with a queryset that reads the request, so each visitor sees their own:

```python
class ProductFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        queryset=lambda request: Category.objects.filter(owner=request.user)
    )
```

A value the address carries that a filter cannot accept, such as a sort option that no
longer exists or a choice that was removed, is ignored for that filter alone. The other
filters still apply and the list is never emptied because of it.

The sort is never an applied filter: it is not counted, not drawn among the refinements,
and neither clear action removes it. The page names the chosen sort beside the count
instead (`sort_label` in the context). The search is an applied filter like any other,
labelled by its own label.

Every field of the filterset is drawn in the filter panel, unless the view names it in
`toolbar_filters`. See [The filter panel](#the-filter-panel).

How each control applies:

- A choice, the sort and a toggle in the toolbar apply the moment they are picked.
- The search applies on Enter or its Search button.
- The filter panel's fields apply with its Apply button, which sends the toolbar's values
  with them. A toolbar change likewise sends what the panel's fields hold, applied or not.
- The Filters button's badge counts the panel's applied filters only. The panel's Clear
  link removes those and keeps the toolbar's filters, the search and the sort, wherever
  the sort is drawn. The count row's "Clear all" removes the search and every filter and
  keeps the sort.

Every change returns to the first page. The address carries only the fields that are
set: an empty field is left out, and so is the empty choice of a yes/no select (Django's
`NullBooleanSelect` sends `unknown`). A search for the word "unknown" is kept. The page's
`js/list_view.js` static file does this, and finds the form by its id, `filterForm`. It
also applies a toolbar list of several values, and a
widget of your own, when focus leaves it with a different value than it found, so a list
that opens applies once, on closing, and not at all when nothing changed.

### Choosing which filters go in the toolbar

`toolbar_filters` names the filterset fields drawn in the toolbar itself, where they can be
reached without opening anything:

```python
class ProductListView(MVPListView):
    model = Product
    filterset_class = ProductFilter
    toolbar_filters = ["q", "status", "o"]
```

The named fields are drawn in the toolbar in that order, each once. The sort is the
exception: wherever it is named, it is drawn at the end of the row, before the Filters and
add buttons. Every field not named is drawn in the filter panel. Name every field and the
page draws no Filters button and no panel. The default, `[]`, leaves every field in the
panel.

Each kind of filter has a compact form in the toolbar:

| Filter | Drawn as |
| --- | --- |
| `SearchFilter` | A search box with its button, taking the room the row has left |
| `SortFilter` | A button opening its options; picking one applies it |
| `ChoiceFilter`, `ModelChoiceFilter` | A button opening the choices, with the empty choice first; picking one applies it. The empty choice is named by the filter's `empty_label`, or "Any" when that is left at its default dashes. `empty_label=None` leaves it out |
| `MultipleChoiceFilter`, `ModelMultipleChoiceFilter` | A button opening a list of checkboxes; the list applies when it closes with a changed choice |
| `BooleanFilter` | A switch that applies when flipped |
| `CharFilter` | A text box |
| Any filter given a widget other than its field's default | That widget, drawn as it is |

Each control is named by its filter's label for a screen reader. None shows the value
chosen in it, so the row keeps its width: a chosen value is shown on its chip below the
toolbar, and the chosen sort beside the count.

A filter with a widget of your own, such as a Tom Select control, is drawn by that widget
and nothing more. It gains daisyUI's `select w-full` class (`input w-full` for anything
that is not a select) and an `aria-label` of the filter's label, unless it declares its
own, and it applies when focus leaves it with a different value than it found. The package
loads no asset such a widget needs: the page still writes `{{ filter.form.media }}`, and
the project loads anything else the widget relies on itself.

Any other filter, such as a `RangeFilter` or a `DateFilter` with its default widget, has
no compact form. Naming it in `toolbar_filters` raises `ImproperlyConfigured` on the first
request, naming the view, the field and the filter's class; leave it in the panel. So does
a name the filterset has no field for, naming the view, the name and the filterset.

To draw a filter the toolbar does not cover, override `get_toolbar_field(filterset, name)`
and return a dict with a `kind` of your own, then draw it in an override of the
`page.toolbar` block:

```python
class ProductListView(MVPListView):
    model = Product
    filterset_class = ProductFilter
    toolbar_filters = ["q", "price"]

    def get_toolbar_field(self, filterset, name):
        if name == "price":
            return {"kind": "range", "name": name, "label": filterset.form[name].label}
        return super().get_toolbar_field(filterset, name)
```

Every dict carries `name`, `label` and `kind`. The package's kinds add:

| `kind` | Extra keys |
| --- | --- |
| `search`, `text` | `value`, the value the request sent |
| `sort`, `choice` | `value`, and `choices` as `(key, label, selected)` without the empty choice |
| `choice` | also `empty_label`, the words for the empty choice, or `None` for no empty choice |
| `multichoice` | `choices` as `(key, label, selected)` |
| `toggle` | `checked` |
| `widget` | `bound`, the field's bound field |

### The filter panel

The filterset fields the toolbar does not draw are drawn in a filter panel, a
[side panel](layout.md#side-panel) beside the results. From its breakpoint (`xl` by
default) it is a column at the end of the page, level with the results, that sticks under
the header. Below the breakpoint it is a drawer, opened by the Filters button in the
toolbar. The button's badge counts the panel's applied filters. A list whose fields are
all in the toolbar draws neither the panel nor the button.

The panel draws no form of its own. The view sets `form="filterForm"` on each panel
field's widget, so the field belongs to the toolbar's form from outside it. That reaches a
range, whose widget draws two inputs, a multiple choice, and a widget of your own, a Tom
Select control among them. Apply names the same form.

Every update to the list, whether from the toolbar, a chip, the pager or the panel's own
Apply and Clear, asks htmx for the panel along with the list region (`hx-select-oob`), so
the panel's fields and its Clear link show the state of the response. An open drawer is
replaced with the rest of the panel and comes back closed. A form or link of your own that
swaps the region carries `hx-select-oob="#{{ filter_panel_id }}"` as well to keep the panel
in step.

Two attributes on the view set the panel up:

```python
class ProductListView(MVPListView):
    model = Product
    filterset_class = ProductFilter
    toolbar_filters = ["q", "status", "o"]
    filter_panel_attrs = {"position": "start", "width": "lg"}
    filter_panel_id = "refine"
```

| Attribute | What it does |
| --- | --- |
| `filter_panel_attrs` | A dict handed to the panel's `<c-mvp.page.side>`: `width`, `position`, `align`, `breakpoint` (`False` keeps the filters behind the button at every width), `collapse` and `class`. Default: `{"position": "end"}`. The panel sticks under the header, and one taller than the screen moves with the page rather than scrolling on its own, so its Apply and Clear are never out of reach. Unless `align` is set, the panel is level with the results at the end and with the title at the start. A dict you set replaces the default whole |
| `filter_panel_id` | The id of the panel's root element, which the Filters button opens and every update refreshes. Default: `"filters"` |

To draw the panel yourself, call
[`<c-mvp.page.list.filters.panel>`](components.md#list-components-driven-by-view-context)
in the `page.side` block.

A drawer closed without applying keeps what was typed in its fields until the next update
to the list, which redraws the panel from the response.

### Moving search_fields and order_by into a filterset

`search_fields`, `max_search_words`, `order_by`, `get_search_fields()` and
`get_order_by_choices()` are gone, along with `SearchMixin`, `OrderMixin`,
`SearchOrderMixin` and `mvp.integrations.django_filters.views.MVPFilteredListView`. A view
that still declares one is refused when Django imports it, with an error that names the
view, the setting and the filter that replaces it. So is a view that composes
django-filter's `FilterView`: the list view builds its own filterset.

Before:

```python
class ProductListView(MVPListView):
    model = Product
    search_fields = ["name", "description"]
    max_search_words = 20
    order_by = [
        ("name_asc", "Name (A-Z)", ["name", "pk"]),
        ("newest", "Newest first", ["-created", "-pk"]),
    ]
```

After:

```python
class ProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name", "description"], max_words=20)
    o = SortFilter(
        options=[
            ("name_asc", "Name (A-Z)", ["name", "pk"]),
            ("newest", "Newest first", ["-created", "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields: list[str] = []


class ProductListView(MVPListView):
    model = Product
    filterset_class = ProductFilter
```

Keep the option keys and the addresses people have bookmarked keep working. A view that
had a filterset already adds the two filters to it, and one that composed
`MVPListViewMixin` with `FilterView` drops `FilterView`. A table view's ordering belongs on
its table class, through the table's own `order_by` or `Meta.order_by`; a table view
ignores a `SortFilter`.

### How a list page is laid out

From top to bottom, the list template draws:

1. **The title row.** The eyebrow, the title, the lead and the info button.
2. **The toolbar.** The filter form with the fields named in `toolbar_filters`, then the
   sort when it is named, the Filters button that opens the filter panel, and the add
   button last. The filter panel itself is a [side panel](layout.md#side-panel) beside the
   results.
3. **The count row.** A count of what the list holds, the chosen sort, then what is
   narrowing the list: the search and each applied filter, each drawn as a control that
   removes it. Two or more also get a single "Clear all".
4. **The results**, or the empty state.
5. **The pager**, only when there is more than one page. A wide screen gets the range
   being shown and numbered pages. A phone gets Previous, "Page 2 of 6" and Next.

Each control follows the thing it drives, so there is no separate list to keep in step
with the view. A filterset draws the filter form, the filter panel and the Filters button, and
`show_create_action` the add button. Leave one unconfigured and its control does not
appear. A list with no records and nothing applied draws no toolbar at all, since there
is nothing to search or sort. Its empty state carries the add button, and the create
dialog with it, instead.

The count reads "32 products" from the model's verbose name. Once a search or filter is
applied it reads "3 results". On a paginated list the browser title also carries the
page, as in "Products (page 2 of 4)".

### Updating in place

Applying a filter, removing a chip, Clear all, sorting and moving to another page all
update the list without reloading the page. Each fetches the list with htmx and swaps one
region, `#mvp-list`, which holds the toolbar, the count row, the results and the pager. The
address bar follows each change, so the back button and a copied link work as they did. A
browser without JavaScript submits the form as an ordinary GET.

On a table page the column headings sort the same way. A table drawn anywhere else sorts
with a page load.

The view answers a request whose `HX-Target` header is the region with the page's content
alone, without the app shell around it. It renders the same template, so a block you
override is drawn in the swap too. Every response varies on `HX-Target`, so a cache keeps
the two apart. django-htmx and its middleware are not needed for any of this.

| Attribute or hook | What it does |
| --- | --- |
| `list_region_id` | The id of the swapped region. Default: `"mvp-list"`. Passed to the template under the same name |
| `partial_base_template` | What `page_view.html` extends in place of `base.html` for the region alone. Default: `"mvp/partial.html"`, which draws the title and the `content` block |
| `is_region_request()` | Whether this request asked for the region alone |

The swap sits on each control rather than on the region, so htmx you add to a result card
or a table cell keeps its own target. A form or link of your own, drawn in an overridden
block, swaps the region when it carries the same four attributes:

```html
<a href="?status=draft"
   hx-boost="true"
   hx-target="#{{ list_region_id }}"
   hx-select="#{{ list_region_id }}"
   hx-swap="outerHTML">Drafts</a>
```

### What the view tells the template

These context keys describe the state of the list:

| Key | Value |
| --- | --- |
| `result_count` | How many records the list holds across every page, after search and filters. Override `get_result_count(context)` to count another way |
| `refinements` | What is narrowing the list: each applied filter of the filterset, the search among them, in the filterset's order. The sort is never one. Empty when nothing is applied |
| `clear_refinements_url` | The current URL with the search and every filter removed, and the sort kept. Present only when `refinements` is not empty |
| `sort_label` | The label of the chosen sort option, or `""`. Present only when the view has a filterset |
| `filter`, `filterset` | The request's filterset, under both names. Present only when the view has one |
| `toolbar_fields` | The fields `toolbar_filters` names, as `get_toolbar_field()` describes them, in that order and without the sort. Present only when the view has a filterset |
| `toolbar_sort` | The sort, described the same way, when `toolbar_filters` names it; otherwise `None` |
| `panel_fields` | The bound fields of every other field of the filterset, for the filter panel. Each widget carries `form="filterForm"`, so the field joins the toolbar's form from outside it |
| `panel_applied_count` | How many of the panel's fields are applied filters: the Filters button's badge. Present only when the view has a filterset |
| `clear_panel_url` | The current URL without the panel's fields and the page number. The toolbar's fields and the sort are kept. Present only when a panel field is applied |
| `filter_panel_attrs` | The attributes the filter panel's `<c-mvp.page.side>` is drawn with |
| `filter_panel_id` | The id of the filter panel's root element |
| `list_region_id` | The id of the region a filter, the pager or a column heading swaps in place |
| `page_base_template` | `partial_base_template`, present only when the request asked for the region alone |

Each entry in `refinements` is a dict:

| Key | Value |
| --- | --- |
| `kind` | `"filter"` |
| `name` | The filter's name on the filterset, `"q"` for a search named that way |
| `label` | The words that name it: the filter's label |
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
| `page.title` | The title area: the eyebrow, title, lead and info icon |
| `page.eyebrow`, `page.heading`, `page.lead`, `page.info` | One argument of the title each, inside `page.title`. Filled with nothing, one removes its argument alone. See [Replacing one part of a page's title](layout.md#replacing-one-part-of-a-pages-title) |
| `page.side` | The filter panel, beside the results. Empty when every field is in the toolbar |
| `page.toolbar` | The whole toolbar row: the filter form, then `page.controls` |
| `page.filters` | The filter form with the toolbar's fields, inside `page.toolbar` |
| `page.controls` | The end of the toolbar row: sort, the Filters button, then `page.actions` |
| `page.actions` | The view's `page_actions`, then the add button, inside `page.controls`. Write `{{ block.super }}` to keep both |
| `page.refinements` | The count row: the count, the chosen sort and the applied search and filters |
| `page.summary` | The count, inside `page.refinements` |
| `page.results` | The grid of records |
| `page.empty` | The empty state, inside the results |
| `page.pagination` | The pager |

```html
{% extends "list_view.html" %}
{% block page.actions %}
  <c-button icon="download" text="Export" href="{% url 'product-export' %}" />
  {{ block.super }}
{% endblock page.actions %}
```

`{{ block.super }}` is the view's actions and the add button, so where you write it decides
where they go: before your own actions, after them, or nowhere if you leave it out. A table page has the same
three toolbar blocks, so an override written for one serves the other.

The toolbar is drawn only when the list has records or something is applied, and
`page.actions` is drawn with it. A list with no records shows the empty state instead,
which has its own add button; a page that wants more there overrides `page.empty`.

Replacing an outer block replaces the blocks inside it: a template that overrides
`page.toolbar` draws its own filter form and controls, and its own add button if it wants
one. The filter panel's fields join the filter form, `#filterForm`, through the HTML `form`
attribute; the Filters button only opens the panel and may sit anywhere. Give your form the swap attributes from
[Updating in place](#updating-in-place) to keep it updating without a page load.

The toolbar's controls are drawn at DaisyUI's default size. For a denser page, override
`page.filters` and `page.controls` and pass `size="sm"` to the controls you draw:
`<c-mvp.page.list.filters.field>`, `<c-mvp.page.side.toggle>` and
`<c-mvp.page.list.actions.create>` all take it.

```django
{% block page.filters %}
  <form id="filterForm" method="get" action="." class="contents">
    {% for field in toolbar_fields %}
      <c-mvp.page.list.filters.field :field="field" size="sm" />
    {% endfor %}
  </form>
{% endblock page.filters %}
```

On a phone the sort, Filters and add buttons are drawn as their icons alone, below `sm`,
and the controls sit closer together. The Filters button keeps its count of applied
filters. A screen reader still names each by its label.

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

For how the filter state reaches the template, and table rendering with django-tables2,
see [Integrations](integrations.md).

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

List and table pages update in place with no setup and without django-htmx: see
[Updating in place](#updating-in-place).

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
