# Forms — reference

The form views: create, update, delete, the plain form view, and the parent-plus-related-rows
inline formset views. Covers page titles, success messages, the redirect chain, `?next=`
handling and how a form is rendered.

```python
# views.py
from mvp.views import (
    InlineFormSet, MVPCreateView, MVPDeleteView, MVPFormView,
    MVPInlineCreateView, MVPInlineUpdateView, MVPUpdateView,
)
```

`MVPFormBase` and `MVPModelFormBase` are exported too, for composing a form view over a base
class the package does not ship.

## Form rendering

Forms render through django-crispy-forms with the crispy-tailwind template pack. Always — there
is no renderer setting and no fallback path. Both distributions are hard runtime dependencies,
and both apps must be in `INSTALLED_APPS` (Django resolves `{% load %}` libraries only from
installed apps, so without them `{% load crispy_forms_tags %}` raises `TemplateSyntaxError`).

```python
# settings.py
INSTALLED_APPS = [..., "crispy_forms", "crispy_tailwind", "mvp", ...]
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"
```

Three ways to change what a form looks like, cheapest first:

1. **A crispy helper on the form.** When the form has a `helper` attribute the packaged
   renderer switches to the `{% crispy %}` tag, which gives you layouts, rows, field ordering
   and appended markup. Set `helper.form_tag = False`: the page already renders the `<form>`
   element, the submit buttons and the CSRF token.
2. **The `c-form.*` components.** Drop into a template block and compose the parts by hand.
3. **A template override.** Give the view a `template_name` extending `form_view.html` and
   override its `before_form`, `formset`, `actions` or `after_form` blocks.

## `MVPFormView`

A non-model form page. Django's `FormView` with the packaged chrome.

| Attribute | Default | Meaning |
|---|---|---|
| `form_class` | — | Required, as on Django's `FormView`. |
| `page_title` | `""` | When empty, derived from the class name: `ContactUsView` → "Contact Us View". |
| `success_message` | `""` | Interpolated with `cleaned_data`. Missing keys substitute `""` rather than raising. |
| `success_url` | `None` | A literal path or a `reverse_lazy()`. **Not** a CRUD shorthand. |
| `base_template_name` | `"form_view.html"` | Fallback template. |
| `page_class` | `"mvp-form-page"` | Page container classes. |

Redirect chain, and it is shorter than the model views': validated `?next=` → `success_url` →
`ImproperlyConfigured`.

`success_url` is used verbatim here. `MVPFormView` is built on `MVPFormBase`, not on
`MVPModelFormBase`, and only the model-form base runs `success_url` through
`resolve_crud_url()` first. Write `success_url = "list"` on an `MVPFormView` and the browser is
redirected to the relative path `"list"`. The `?next=` step is the exception — that one does
resolve shorthands on both bases.

### Trap: a plain `Form` raises `ImproperlyConfigured` on render

`MVPFormView` inherits the page-class and breadcrumb machinery from the model-aware mixins, and
those dereference the model's meta while building the context. Given a plain
`django.forms.Form`, there is no model to find and rendering raises `ImproperlyConfigured`
before any HTML is produced. The package's own test for a standalone formset notes this and
works around it by passing a `ModelForm`.

Either give the view a `ModelForm`, or override `get_model_class()` to name the model the page
belongs to:

```python
# views.py
class ContactView(MVPFormView):
    form_class = ContactForm  # a plain forms.Form
    success_url = "/thanks/"

    def get_model_class(self):
        return Enquiry  # any model — feeds the title, breadcrumb and CSS class
```

## `MVPCreateView` and `MVPUpdateView`

| Attribute | `MVPCreateView` | `MVPUpdateView` |
|---|---|---|
| `page_title` | `_("Create %(verbose_name)s")` | `_("Update %(verbose_name)s")` |
| `page_class` | `"mvp-form-page mvp-create-page"` | `"mvp-form-page mvp-update-page"` |
| `success_message` | `_("%(verbose_name)s successfully created.")` | `_("%(verbose_name)s successfully updated.")` |
| `success_url` | `None` | `None` |

Both need `model` and `fields` (or a `form_class`). Everything else is derived.

`%(verbose_name)s` in a **page title** is substituted with the title-cased verbose name on both
views, so a model with `verbose_name = "order line"` gives "Create Order Line".

Success messages differ. `MVPCreateView` title-cases the verbose name — "Product successfully
created." Every other model form view, `MVPUpdateView` included, substitutes the verbose name
exactly as the model declares it, which is conventionally lowercase: "product successfully
updated." Any other `%(key)s` in your own `success_message` is filled from `cleaned_data`, and a
key that is not there substitutes an empty string instead of raising `KeyError`.

Breadcrumbs on update are list → detail → page title, each CRUD link gated by its
`show_<action>_action` flag. On create they are list → page title.

### The success-URL chain

For `MVPCreateView`, `MVPUpdateView` and the inline views:

1. **`get_next_url()`** — a validated same-origin `?next=` (or `next` in the POST), or a
   resolved CRUD shorthand.
2. **`success_url`** — tried first as a CRUD shorthand through `resolve_crud_url()`. If that
   resolves, its URL is used. If it does not, the raw value is used **verbatim** as a URL path.
3. **`self.object.get_absolute_url()`** — when the saved object defines it.
4. **`ImproperlyConfigured`** — nothing above produced a URL.

Step 2's fallthrough: `resolve_crud_url()` is gated by the same
`show_<action>_action` flags that draw links, so `success_url = "list"` with `show_list_action`
left `False` does not resolve, and the string `"list"` is then returned as if it were a path.
Set the flag, or use a literal path or `reverse_lazy()`.

`MVPDeleteView` replaces step 3 with the list URL from the CRUD directory and never calls
`get_absolute_url()` — the object is gone by then. `MVPFormView` has no object, so its chain
ends after `success_url` and then raises. Its step 2 is the plain non-resolving one described
above, not this one.

## `?next=` handling

The destination after a successful save can be handed to the view by whoever linked to it.

- **On GET**, the candidate is read from the `?next=` query parameter.
- **On POST**, the `next` field is read first, and `default_next` only if `next` is absent.
- **Accepted values**: a CRUD shorthand — `list`, `detail`, `create`, `update`, `delete` — which
  is resolved through the directory, or a URL starting with `/`.
- **Rejected**: anything cross-origin, an unsafe scheme, or a bare word that is not a shorthand.
  Rejection is silent, falling through to the rest of the chain, with a `logger.warning` under
  `DEBUG` to make it visible in development.

Validation uses Django's `url_has_allowed_host_and_scheme` against the current host, requiring
HTTPS when the request is secure. The validated value is also put in the context as `next_url`.

**Preservation across a failed POST.** The packaged form template renders a hidden
`<input type="hidden" name="next">` whenever `next_url` is set, so a caller's destination
survives a re-render of an invalid form. Independently, the submit buttons each post a
`default_next` value — "Save & continue" sends `list`, "Save & continue editing" sends `update`.
Both keys arrive in the same POST, and the explicit `next` wins because the view looks it up
first, not because of their order in the document. A button proposes a destination. It never
overrides one the caller asked for.

## The delete link on `MVPUpdateView`

`MVPUpdateView` adds a `delete_url` context key from `get_delete_url()`, which the packaged
template draws as a Delete button next to the save buttons.

The URL is `resolve_crud_url("delete")`, so `show_delete_action` gates it and the key is an
empty string when the action is not shown. Two query parameters are appended:

- `back` — this update page's own URL, reversed directly rather than through the directory so
  that leaving `show_update_action` at `False` does not silently blank it. An unregistered
  update route yields an empty value instead of raising.
- `next` — the list URL from the directory.

The delete view reads `back` for its Go Back button and `next` for its post-delete redirect.

## `MVPDeleteView`

| Attribute | Default | Meaning |
|---|---|---|
| `show_related_objects` | `False` | Show what will be cascade-deleted alongside the object. |
| `require_confirmation` | `False` | Require the user to type a value before the Delete button activates. |
| `confirmation_label` | `_("Type the name to confirm")` | Label and placeholder on the confirmation input. |
| `related_objects_max_per_group` | `25` | Per-model cap on the listed related records. The rest become an "… and N more" note. |
| `base_template_name` | `"delete_view.html"` | Extends `form_view.html`. |
| `page_title` | `_("Delete %(verbose_name)s")` | |
| `success_message` | `_("%(verbose_name)s successfully deleted.")` | |

Four scenarios, all rendered by the one template:

| Scenario | Trigger | What renders |
|---|---|---|
| Basic | default | Warning alert, Back button, Confirm delete button. |
| Related-objects summary | `show_related_objects = True` | The warning plus a grouped list of records that will be deleted with it. |
| Protected | detected automatically | An error alert naming the blocking records; **no** Delete button. |
| Type-to-confirm | `require_confirmation = True` | A text input. The Delete button stays disabled until the typed value matches. |

Hooks: `get_confirmation_value()` returns the string the user must type, defaulting to
`str(self.object)`. `get_back_url()` returns the Go Back target, reading `?back` from the query
string, validating it against the current host and falling back to the list URL.

Context added: `is_protected`, `protected_objects`, `require_confirmation`,
`confirmation_value` (empty unless confirmation is required), `confirmation_label`,
`related_objects` (a list of `(label, instances, overflow_count)` tuples, empty when protected)
and `back_url`.

Detection uses Django's own deletion `Collector`, so it sees exactly what a real delete would.
A POST on a PROTECT-blocked object **re-renders the page with status 200** — it does not
redirect and does not raise `ProtectedError`. Confirmation is enforced server-side through a
form, not only by the JavaScript that disables the button.

```python
# views.py
class ArticleDeleteView(MVPDeleteView):
    model = Article
    show_related_objects = True   # preview the cascade
    require_confirmation = True   # user types the article title
    success_url = "list"
    show_list_action = True       # needed for the "list" shorthand to resolve
```

## Inline formsets

A parent record and one or more sets of related rows on one page. Declare each set as an
`InlineFormSet` subclass, list them on the view's `inlines`, and the page renders, validates and
saves them with no template markup and no save code.

### `InlineFormSet`

Shapes the generated formset **class** (folded into `inlineformset_factory`):

| Attribute | Meaning |
|---|---|
| `model` | The related model. Required; never rebound to the parent. |
| `fields` / `exclude` | Field selection on the row form. |
| `form` / `formset` | Custom `ModelForm` / `BaseInlineFormSet` classes. |
| `extra` | Blank rows rendered beyond the existing ones. |
| `min_num` / `max_num` | Row bounds. Setting either also sets its `validate_*` flag, since Django defaults both to `False` and a bound alone rejects nothing. |
| `can_delete` | Whether rows carry a remove control. |
| `fk_name` | Required when the related model reaches the parent by more than one foreign key. |

Shapes the formset **instance**:

| Attribute | Meaning |
|---|---|
| `prefix` | Form-name prefix. Left unset, Django derives one per relation. |
| `initial` | Initial data for the extra rows. |

Escape hatches and presentation:

| Attribute | Meaning |
|---|---|
| `factory_kwargs` | Anything the factory accepts that has no shorthand (`can_order`, …). Applied last, so it wins over a shorthand setting the same key. |
| `formset_kwargs` | Instance-level kwargs. The opposite way round: it is the base dict, and `prefix`, `initial`, `form_kwargs`, `instance`, `data` and `files` are laid on top of it. Use it for keys no shorthand covers. |
| `form_kwargs` | Extra kwargs passed to every row form. |
| `title` | Heading above the set. Defaults to the related model's `verbose_name_plural`. |
| `description` | Help text under the heading. No default; omitted when unset. |

Hooks: `get_factory_kwargs()`, `get_formset_kwargs()`, `get_formset_class()`, `get_title()`,
`get_description()`, `get_form_kwargs(index)` (Django's own per-form hook — `index` is `None`
for the blank template row the browser clones) and `sort_forms(forms)`.

`sort_forms()` is **display only**. The order rows are validated and saved in never changes,
because reordering that would change which submitted row maps to which record.

With `exclude` rather than an explicit `fields`, only *this set's own* foreign key is replaced
with the parent-bound field. Any other foreign key still renders as a chooser over every parent
record. Name `fields` explicitly on a model with more than one relation to the parent.

### `MVPInlineCreateView` and `MVPInlineUpdateView`

| Attribute | Default | Meaning |
|---|---|---|
| `inlines` | `[]` | Declaration classes, rendered in the order listed. |
| `touch_parent` | `True` | On a rows-only page, whether a valid submission writes the parent's `auto_now` field(s). |

Everything else is inherited from `MVPCreateView` / `MVPUpdateView`, including the redirect
chain and the success message. The formsets are added to the context as `inlines`, and each
carries its own `title` and `description`.

- **Atomic save.** Every set is validated with `all_valid()`, which does not short-circuit, so
  every set accumulates its own errors. The parent and all sets then save inside one
  `transaction.atomic()` — the page is never half-persisted.
- **Rows-only page.** `fields = []` on an update view drops the parent's own fields and edits
  only the sets. The parent form is never saved, because saving an empty `ModelForm` issues a
  full `UPDATE` of every column from whatever was loaded and would discard a concurrent write.
  `fields = []` is not `fields = None`: leaving it unset is still Django's own error.
- **`ImproperlyConfigured` guards.** `fields = []` on a *create* view raises (nothing to create
  the parent from), and `fields = []` with no `inlines` raises (the page could edit nothing).
- **Prefix collision.** Two declarations resolving to the same prefix raise
  `ImproperlyConfigured` naming both classes. Otherwise both would read the same POST keys and
  share one management form. Set `prefix` on one of them.

```python
# views.py
class OrderLineInline(InlineFormSet):
    model = OrderLine
    fields = ["quantity"]
    extra = 1
    title = _("Order lines")
    description = _("Add a row per order, or remove one to drop it when you save.")


class ProductOrderLinesView(MVPInlineUpdateView):
    model = Product
    fields = ["name", "category"]
    inlines = [OrderLineInline]
    success_url = "list"
    show_list_action = True
```

## A formset without a parent

A formset needs no declaration class and no `inlines`. Any packaged form view that puts one in
its context under the key `formset` renders it in the same place, with the same markup:

```python
# views.py
from django.forms import modelformset_factory


class BulkOrderLinesView(MVPFormView):
    form_class = ProductForm  # a ModelForm — see the MVPFormView trap above
    success_url = "/done/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        FormSet = modelformset_factory(OrderLine, fields=["product", "quantity"])
        context["formset"] = FormSet(queryset=OrderLine.objects.none())
        return context
```

The component does not care whether the formset came from `inlineformset_factory` or
`modelformset_factory`.

## The form components

| Component | Purpose |
|---|---|
| `c-form` | The `<form>` element: CSRF token, `enctype` when any form or set is multipart, and the slot for buttons. |
| `c-form.render` | Renders a whole Django form through crispy, using `{% crispy %}` when the form has a helper. |
| `c-form.field` | One standalone control with its label, help text and errors, built from explicit attributes rather than a bound field. |
| `c-form.formset` | A whole formset: heading, description, management form, rows, the cloneable blank row and the add control. |
| `c-form.formset.row` | One row: its label, its fields through crispy, and the remove control. |

Attributes for each are in the components reference.

---

Back to [SKILL.md](../SKILL.md).
