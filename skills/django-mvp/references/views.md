# Views — reference

Page views that are not forms: the page-chrome mixin, the template and home views, the list
view and the detail view, plus the error handlers. Form and formset views are covered by the
forms reference.

## What `mvp.views` exports

```python
# views.py — the whole public surface of mvp.views
from mvp.views import (
    InlineFormSet,        # formset declaration class (forms reference)
    MVPCreateView,         # InlinesMixin is on this by default — set `inlines` for row sets
    MVPDeleteView,
    MVPDetailView,
    MVPFormBase,          # base class, for building your own form view
    MVPFormView,
    MVPHomeView,
    MVPListView,
    MVPModelFormBase,     # base class, for building your own model form view
    MVPTemplateView,
    MVPUpdateView,         # InlinesMixin is on this by default — set `inlines` for row sets
    bad_request, not_found, permission_denied, server_error,
)
```

Mixins are deliberately not exported. Import them from their own modules when you need to
compose one with a base class the package does not ship a view for:

```python
# views.py — mixins live in the module that defines them
from mvp.views.base import BaseTemplateNameMixin, ModelInfoMixin, PageMixin
from mvp.views.detail import CRUDDirectoryMixin, PageObjectMixin
from mvp.views.edit import NextURLMixin
from mvp.views.inline import InlinesMixin  # already on MVPCreateView/MVPUpdateView by default
from mvp.views.list import MVPListViewMixin, OrderMixin, SearchMixin, SearchOrderMixin
```

Views built on optional third-party packages are not exported either. They live in
`mvp.integrations.django_tables.views` and `mvp.integrations.django_filters.views`.

## `PageMixin` — the `page` context dict

Every packaged view mixes this in. It adds one context key, `page`, with the metadata the
shell templates read: `{{ page.title }}`, `{{ page.subtitle }}`, `{{ page.class }}`,
`{{ page.info }}` and `{% for crumb in page.breadcrumbs %}`.

| Attribute | Default | Meaning |
|---|---|---|
| `page_title` | `""` | Page heading, rendered as the `<h1>`. |
| `page_subtitle` | `""` | Secondary line under the heading. Omitted when empty. |
| `page_class` | `""` | Extra classes on the page container. The result is always prefixed `mvp-page`. |
| `breadcrumbs` | `[]` | List of breadcrumb dicts. |
| `page_info` | `""` | Text explaining the page. When set, an info icon beside the title opens a dialog holding it. Empty draws no icon. |
| `page_info_actions` | `[]` | Buttons at the foot of that dialog. Each dict is spread onto `c-button`. |

Set the class attribute for a value known at class-definition time. Override the matching hook
— `get_page_title()`, `get_page_subtitle()`, `get_page_class()`, `get_breadcrumbs()`,
`get_page_info()`, `get_page_info_actions()` — for anything that depends on the request or the
loaded object. `get_page_context()` assembles them into the dict, so override that to add a key
of your own.

A breadcrumb is a dict with a required `text` key and an optional `href`. An item with no
`href` renders as plain text, which is how the trailing current-page crumb is drawn.

```python
# views.py
class ProductDetailView(MVPDetailView):
    model = Product

    def get_breadcrumbs(self):
        return [
            {"text": "Home", "href": "/"},
            {"text": "Products", "href": "/products/"},
            {"text": self.object.name},  # no href — current page
        ]
```

There is no page icon. Two packaged templates reference `page.icon`, but nothing populates it
and no `page_icon` attribute exists, so it always renders empty.

### Page info

`page_info` is what the page is for, not what a field means. It renders into a dialog behind an
info icon, so the page layout is unchanged whether it is set or not.

```python
class ProductListView(MVPListView):
    model = Product
    page_info = _("Every product in the catalogue. Search by name, filter by price.")
    page_info_actions = [
        {"text": _("Read the guide"), "href": "/guide/", "icon": "external-link"},
    ]
```

Action dicts reach `c-button` untouched, so `variant`, `icon`, `target` and anything else that
component accepts work here. Actions without `page_info` render nothing at all.

`get_page_info()` returns whatever the dialog should hold, so a view that builds its text at
request time overrides it:

```python
def get_page_info(self):
    return render_to_string("products/help.html", request=self.request)
```

The return value goes through the template layer unchanged: a plain string is escaped, a string
marked safe is written out as markup. Mark text safe only when you control it — a value marked
safe is not escaped, so user-supplied content passed through here unescaped is an injection.

## `MVPTemplateView`

`PageMixin` over Django's `TemplateView`. Wire an informational page straight from the URLconf,
or subclass it.

| Attribute | Default | Meaning |
|---|---|---|
| `template_name` | `"mvp/placeholder_view.html"` | Overridden by any subclass that sets its own. |

The default is a real, rendering placeholder page rather than Django's `ImproperlyConfigured`.
Routing and menus are usually wired before every page has a template, and the packaged default
keeps those routes returning 200 with a "this page doesn't have a template yet" card instead of
a 500.

Under `settings.DEBUG` the view also adds a `placeholder_source` context key reading
`"<ViewClassName> at <request path>"`, which the placeholder prints so you can tell which route
is unfinished. Outside DEBUG the key is absent, so internal class names never reach production
HTML.

```python
# urls.py
path(
    "about/",
    MVPTemplateView.as_view(
        template_name="myapp/about.html",
        page_title="About",
        breadcrumbs=[{"text": "Home", "href": "/"}, {"text": "About"}],
    ),
    name="about",
),
```

## `MVPHomeView`

Subclass of `MVPTemplateView`. Serves two different templates from one URL with no redirect:
the landing page to anonymous visitors, the dashboard to authenticated ones.

| Attribute | Default | Meaning |
|---|---|---|
| `landing_template_name` | `"mvp/landing.html"` | Rendered when `request.user` is not authenticated. |
| `dashboard_template_name` | `"mvp/dashboard.html"` | Rendered when the user is authenticated. |
| `page_title` | `_("Home")` | Inherited chrome. |

`get_template_names()` raises `ImproperlyConfigured` when `landing_template_name` is `None` —
checked on every request, authenticated or not — and separately when the visitor is
authenticated and `dashboard_template_name` is `None`. Setting one to `None` to "turn it off"
is therefore an error, not a fallback.

Both context hooks take the already-built context and must return it:

```python
# views.py
class HomeView(MVPHomeView):
    landing_template_name = "myapp/landing.html"
    dashboard_template_name = "myapp/dashboard.html"

    def get_dashboard_context(self, context):
        context["recent"] = Order.objects.filter(user=self.request.user)[:5]
        return context  # returning None blanks the context

    def get_landing_context(self, context):
        context["testimonials"] = Testimonial.objects.published()
        return context
```

## `MVPListView`

A paginated, searchable, orderable list page. A subclass that sets only `model` is a working
page.

| Attribute | Default | Meaning |
|---|---|---|
| `paginate_by` | `24` | Page size. Divisible by 1–4, so it fills 1-, 2-, 3- and 4-column grids evenly. |
| `base_template_name` | `"list_view.html"` | Fallback template, tried after Django's own `<app>/<model>_list.html`. |
| `directory` | `["create"]` | CRUD links offered in the header. Detail, update and delete belong on object pages. |
| `list_item_template` | `None` | Partial rendered per object. When `None`, derived as `<app_label>/<model_name>_list_item.html`. |
| `grid` | `{}` | Passed through to the context unchanged as `grid_config`, and on to the grid component. |
| `empty_state_heading` | `_("There's nothing here yet")` | Heading shown when the page has no objects. |
| `empty_state_message` | translated default | Body text under it. The paragraph element renders either way — `None` leaves it empty rather than dropping it. |
| `create_form_class` | `None` | A form class enables the inline "Add" modal on the list page. |
| `create_modal_title` | `None` | Injected into context but read by no packaged template — currently has no effect. |
| `search_fields` | `None` | ORM field paths for `?q=`. `None` or empty disables search entirely. |
| `max_search_words` | `10` | How many words of `?q=` are searched. Words past the limit are ignored. |
| `order_by` | `None` | Whitelist of orderings for `?o=`. `None` or empty disables ordering. |
| `page_title` | `""` | When empty, falls back to `verbose_name_plural.title()`. |

Hooks: `get_list_item_template()`, `get_empty_state_heading()`, `get_empty_state_message()`,
`get_grid_config()`, `get_create_form()`, `get_search_fields()`, `get_order_by_choices()`, plus
the `PageMixin` hooks. The default `get_breadcrumbs()` is Home → page title.

`get_search_fields()` is the odd one out. The queryset filter calls it, but the
`is_searchable` context key that decides whether the search box is drawn reads the
`search_fields` attribute directly. Override the hook alone and `?q=` still filters while the
box never renders — set `search_fields` to something truthy as well.

`get_list_item_template()` raises `AttributeError` when the view has no `model` and no explicit
`list_item_template` — the derived name has nothing to derive from.

Context added: `list_item_template`, `empty_state` (`{"heading", "message"}`), `grid_config`,
`directory`, `model_info`, `search_query`, `is_searchable`, and Django's own `object_list` /
`page_obj` / `paginator`. `order_by_choices` and `current_ordering` are added only when
`order_by` is configured. `create_form` is added only when `create_form_class` is set *and*
`show_create_action` allows the create link.

### Search and ordering

`?q=` runs a case-insensitive `icontains` match across every `search_fields` path, splitting on
whitespace and OR-ing every word against every field, then calling `.distinct()`. Relationship
traversal works (`"category__name"`).

Only the first `max_search_words` words are searched — ten by default. One branch is added to
the query per word per field, and the term comes from the URL, so an unbounded one lets the
requester choose how deep the expression tree gets. Raise the limit on the view if a project
genuinely needs longer terms.

`?o=` is whitelist-only. Each `order_by` entry is a three-tuple:

```python
# views.py
class ProductListView(MVPListView):
    model = Product
    search_fields = ["name", "description", "category__name"]
    order_by = [
        # (public_key, label, orm_expression)
        ("name_asc", "Name (A–Z)", "name"),
        ("newest", "Newest first", "-created_at"),
    ]
```

`public_key` is what appears in the URL, `label` is what the sort control displays, and
`orm_expression` is the only value that ever reaches `queryset.order_by()`. The raw `?o=` value
is never passed to the ORM, and an unrecognised one is ignored silently.

### Composing with another base

`MVPListView` is `MVPListViewMixin` plus Django's `ListView` and `paginate_by = 24`. Subclass
the mixin instead when you need a different base — a `FilterView`, say — and it brings the
template resolution, page chrome, CRUD directory, search and ordering with it.

| Mixin | Brings |
|---|---|
| `SearchMixin` | `?q=` filtering, `search_fields`, the `search_query` / `is_searchable` context. |
| `OrderMixin` | `?o=` whitelist ordering, `order_by`, the ordering context. |
| `SearchOrderMixin` | Both, in the fixed order that applies ordering before `.distinct()`. |
| `MVPListViewMixin` | All of the above plus `BaseTemplateNameMixin`, `CRUDDirectoryMixin` and `PageMixin`. |

Keep the mixin left of the base class so its `get_queryset()` runs outermost.

## `MVPDetailView`

The read page for one object. Its header carries links to the sibling CRUD views.

| Attribute | Default | Meaning |
|---|---|---|
| `base_template_name` | `"detail_view.html"` | Fallback after `<app>/<model>_detail.html`. |
| `page_class` | `"mvp-detail-page"` | Plus `mvp-page` and `<model_name>-page`, both added automatically. |
| `directory` | `["update", "delete"]` | Which action links the page may draw. List is absent because the breadcrumb already links it. |
| `list_view_title` | `""` | Label for the list link in the breadcrumb. Falls back to `verbose_name_plural.title()`. |
| `show_list_action` | `False` | Whether a list link may be drawn. |
| `show_detail_action` | `False` | Whether a detail link may be drawn. |
| `show_create_action` | `False` | Whether a create link may be drawn. |
| `show_update_action` | `False` | Whether an update link may be drawn. |
| `show_delete_action` | `False` | Whether a delete link may be drawn. |

`get_page_title()` returns `str(self.object)`. Context added: `directory`, `model_info`, `page`,
plus Django's `object`.

Each `show_<action>_action` takes a bool or a callable receiving the request user:

```python
# views.py
class ProductDetailView(MVPDetailView):
    model = Product
    show_update_action = True

    def show_delete_action(self, user):
        return user.is_staff
```

### These flags only draw links

A `show_<action>_action` decides whether *this* page offers a link. The view it points at is a
different class that never sees the attribute. Hiding a button is not authorisation — anyone
who types the URL still reaches the target view. Put the real check on the target:
`LoginRequiredMixin`, `PermissionRequiredMixin` or `UserPassesTestMixin` from
`django.contrib.auth.mixins`, or an object-level permission library such as django-guardian.

### How the URLs are built

`get_directory()` walks `self.directory` and puts each resolved URL in the context as
`<action>_url` (`directory.update_url`, `directory.delete_url`). The URL *name* comes from
`MVP_CONFIG["view_names"]`, whose defaults are `"{model_name}-list"`, `"{model_name}-detail"`,
`"{model_name}-create"`, `"{model_name}-update"` and `"{model_name}-delete"`. The pattern is
formatted with `model_name` and `app_name` from the model's meta, so a `Product` in the `shop`
app reverses `product-update` by default. Reconfigure the pattern globally through `MVP_CONFIG`.

`get_url_kwargs(action)` supplies the reverse kwargs: `{}` for `list` and `create`, and this
view's own `self.kwargs` for everything else. Override it for nested URL patterns, and return
`None` from it to suppress an action silently. The default returns `dict(self.kwargs) or None`,
so a view with no URL kwargs at all suppresses every non-collection action rather than
reversing it without arguments.

A shown action whose route is not registered raises `NoReverseMatch` rather than dropping the
link, so the misconfiguration surfaces. Suppress an action on purpose with the flag or a
`None` from `get_url_kwargs()`.

### The `has_<action>_permission` names

The flags were called `has_<action>_permission` before 0.16 and were renamed to
`show_<action>_action` to say what they actually do. The deprecation names 0.18 as the removal
release: that is what the `MVPDeprecationWarning` tells the developer, and what the class
docstring says.

As of 0.18.0 the old names are still read, and when both are set on a view the **old name
wins** — ignoring it would reveal a link a project had deliberately hidden. Treat removal as
imminent rather than as a date you can plan around. Write the new names on new code and rename
on sight.

## Error handlers

Four plain view functions, wired in the root URLconf. `bad_request`, `permission_denied` and
`not_found` take `(request, exception)`. `server_error` takes `(request)` alone. Each renders
the correspondingly-named template — `400.html`, `403.html`, `404.html`, `500.html` — with the
matching status code.

`server_error` runs no database query, by design: it is the handler for the case where the
database may be what failed. It passes one context value, `support_email`, read from
`settings.DEFAULT_FROM_EMAIL`. Keep any override of `500.html` free of queries too.

---

Back to [SKILL.md](../SKILL.md).
