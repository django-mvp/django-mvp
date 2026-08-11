# Formsets

django-mvp renders a Django formset with the same packaged look as a single form —
management form, one row per form, per-row and set-level errors, and add/remove controls
that work in the browser without a page reload or a build step. This guide walks the whole
path from a model and its related model to a page carrying one set, then more than one, then
the rows-only case. It ends with the standalone case: a formset with no parent record at all.

## Declaring a set

A set of related rows is declared as its own class, one per related model: subclass
`InlineFormSet` (`mvp.views`), set `model` to the related model, and configure the rest as
class attributes. List the declaration on a view's `inlines` and it renders, validates and
saves alongside the parent record.

```python
# models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)


class OrderLine(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_lines")
    quantity = models.PositiveIntegerField(default=1)
```

```python
# views.py
from django.utils.translation import gettext_lazy as _

from mvp.views import InlineFormSet, MVPInlineUpdateView

from .models import OrderLine, Product


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
```

Wire it to a URL, the same as any other model view:

```python
# urls.py
path("products/<int:pk>/order-lines/", ProductOrderLinesView.as_view(), name="product-order-lines"),
```

That's the whole configuration. No template markup for the rows, and no code to build,
validate or save the set:

- **Rendering.** `GET` renders the parent's form and one row per existing `OrderLine`, plus
  `extra` blank rows. The view's default template (`form_view.html`) already renders each
  declared set through `<c-form.formset>` when it is in context — see
  [Components](components.md#actions-user-misc) for what that component renders.
- **Telling the set apart from the parent's fields.** The set opens with a divider and a
  heading, so the rows do not read as more fields on the parent's form. `title` sets that
  heading and `description` puts help text under it. See
  [the heading below](#more-than-one-set-on-a-page) for what `title` defaults to when it is
  left unset.
- **Removing a row.** The control is a trash icon in the row's top right, kept transparent
  until the row is hovered or something in it takes focus. Its label is the accessible name
  rather than visible text, and it is overridable with the `remove-label` attribute.
- **Adding and removing rows.** The add control clones the row markup in the browser. Removing
  a row hides it and marks it for deletion (a saved row) or drops it (an unsaved one). Neither
  needs a page reload.
- **Validation and saving.** A submission is only valid when the parent form and every set are
  valid. On success the parent is saved, every set's rows are attached to it, and everything
  saves in one transaction — nothing is half-persisted.

## More than one set on a page

`inlines` takes any number of declarations, each against its own related model:

```python
# views.py
from django.utils.translation import gettext_lazy as _

from mvp.views import InlineFormSet, MVPInlineCreateView

from .models import Project, ProjectNote, ProjectTask


class ProjectTaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    extra = 1


class ProjectNoteInline(InlineFormSet):
    model = ProjectNote
    fields = ["text"]
    fk_name = "project"
    extra = 1


class ProjectCreateView(MVPInlineCreateView):
    model = Project
    fields = ["name"]
    inlines = [ProjectTaskInline, ProjectNoteInline]
    success_url = "/"
```

Both sets render, each under its own heading, in the order `inlines` lists them. Neither
declaration above sets `title`, so each falls back to its related model's `verbose_name_plural`
— the same heading `django.contrib.admin` would give it. Set `title` to override it, the way
`OrderLineInline` does above.

Each set gets its own prefix, derived from the relation it uses rather than from the model, so
two sets over different relations never collide by accident. When two declarations do resolve
to the same prefix — two sets over the same relation — building the page raises
`ImproperlyConfigured` naming both declaration classes. Set `prefix` on one of them to fix it.

### When a related model reaches the parent by more than one relation

`ProjectNote` above has two foreign keys to `Project`: `project` and `related_project`. Two
things follow from that:

- **Name `fk_name`.** With more than one foreign key to the parent, Django cannot pick one on
  its own, so the declaration must say which relation it edits — `fk_name = "project"` above,
  not `related_project`.
- **Name `fields` explicitly, never `exclude`.** A set built with `exclude` still admits every
  other field on the model, including its other foreign keys. `BaseInlineFormSet.add_fields`
  replaces only *this set's own* foreign key with the parent-bound field — `related_project`
  would render as a plain chooser over every `Project` in the database, not just the one this
  page edits. Naming `fields` explicitly, as both declarations above do, keeps the field
  selection to what the set is meant to show.

This applies whenever a related model reaches the parent by more than one relation, not only
when a set is built against the less common one.

## Reaching past the shorthand attributes

Every shorthand attribute is a name Django already uses — `inlineformset_factory`'s parameters
and `django.contrib.admin`'s `InlineModelAdmin` attributes at once — split across the two
things a set is built from:

- **Shape the generated formset class:** `fields`, `exclude`, `form`, `formset`, `extra`,
  `min_num`, `max_num`, `can_delete` and `fk_name`.
- **Shape the formset instance:** `prefix` and `initial`.

Anything Django's factory accepts that the shorthands don't expose —
`can_order`, for instance — is reached through `factory_kwargs` (class-level) or
`formset_kwargs` (instance-level), both dictionaries folded in after the shorthands, so an
explicit key in either one wins over its shorthand on the same name:

```python
class TaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    factory_kwargs = {"can_order": True}
```

For anything `factory_kwargs`/`formset_kwargs` can't express as a static value, override
`get_factory_kwargs()` or `get_formset_kwargs()`, call `super()` and mutate the result — the
same super-and-extend pattern Django's own `get_form_kwargs` uses.

## Per-form arguments — `get_form_kwargs(index)`

Override `get_form_kwargs(index)` to give individual forms different arguments by position.
This is Django's own per-form hook (`BaseFormSet.get_form_kwargs`), not a new one: `index` is
the position of the form being built, and `None` for the blank template form the browser
clones to add a row.

```python
class TaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["label_suffix"] = f"row-{index}" if index is not None else "blank"
        return kwargs
```

Without an override, every form gets the shared `form_kwargs` attribute, the same default
`BaseFormSet.get_form_kwargs` falls back to.

## Display order — `sort_forms()`

Override `sort_forms(forms)` to change the order a set's forms render in, independently of the
order Django built them in:

```python
class TaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    extra = 0

    def sort_forms(self, forms):
        return list(reversed(forms))
```

This is display only. The rows a submission validates and saves are unaffected by
`sort_forms` — reordering that too would change which submitted row maps to which record, so
it never does. `sort_forms` is also a different feature from Django's own `can_order`.
`can_order` lets the *user* reorder rows through the form (reached through `factory_kwargs`,
above), and `sort_forms` lets the *developer* fix the sequence a set always renders in.

## The rows-only page

An update view configured with `fields = []` edits only its declared sets — the parent's own
fields are left off the page entirely:

```python
class OrderLineInline(InlineFormSet):
    model = OrderLine
    fields = ["quantity"]
    extra = 1


class ProductOrderLinesRowsOnlyView(MVPInlineUpdateView):
    model = Product
    fields = []
    inlines = [OrderLineInline]
    success_url = "list"
```

- **What renders.** No field input for any of the parent's own fields — the generated parent
  form has none. Every declared set still renders and binds to the record the URL identifies,
  the same as on any other update page.
- **`fields = []` is not `fields = None`.** Leaving `fields` unset (`None`) is Django's own
  "you configured nothing" state and still raises its usual error. Only an explicit empty
  `fields` selects the rows-only page.
- **The parent form is never saved.** An empty `ModelForm` is always valid, and calling
  `save()` on one issues a full `UPDATE` of every column from whatever was in memory when the
  page was loaded — silently discarding any change another request made to a different column
  in between. The rows-only page never calls it.
- **Create still requires parent fields.** There's no loaded record to hang rows off on a
  create page, so `fields = []` on `MVPInlineCreateView` raises `ImproperlyConfigured` rather
  than creating the one record nobody asked to create. The rows-only page is an update-page
  concept.

### `touch_parent`

`touch_parent` (default `True`) decides whether a valid submission also records the change on
the parent's own `auto_now` field or fields — `Product.updated_at` above — without saving the
parent form:

- **On** (the default), a valid submission writes only the `auto_now` field(s), through
  `save(update_fields=[...])`, in the same transaction the rows save in. It fires the model's
  usual save signals, the same as any other save.
- **Off** (`touch_parent = False`), a valid submission never calls `save()` on the parent at
  all.
- **Where the parent model has no `auto_now` field**, the two settings behave identically:
  there is nothing to touch, so this is a genuine no-op either way — nothing about the parent
  record is written.

## The standalone case

A formset does not need a parent record, an `InlineFormSet` declaration, or `inlines` at all.
Rendering is generic: any packaged form view that puts a formset in its context renders it in
the right place, with no further configuration. Build the formset yourself and add it in
`get_context_data`:

```python
# views.py
from django.forms import modelformset_factory

from mvp.views import MVPFormView

from .forms import ProductForm
from .models import OrderLine


class BulkOrderLinesView(MVPFormView):
    form_class = ProductForm  # any ModelForm satisfies the view — unrelated to the formset
    template_name = "form_view.html"
    success_url = "/done/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        OrderLineFormSet = modelformset_factory(OrderLine, fields=["product", "quantity"])
        context["formset"] = OrderLineFormSet(queryset=OrderLine.objects.none())
        return context
```

The component itself doesn't know or care whether its formset came from
`inlineformset_factory` or `modelformset_factory` — it renders `formset.forms`,
`formset.management_form` and `formset.non_form_errors` the same way either time. The demo
app's Formset component page renders exactly this: a bound `OrderLine` formset with no
parent view around it at all.

## What you get either way

- **The packaged look.** Every row's fields render through the same crispy field template a
  single form's fields use — same control, same label, same help text, same error placement.
- **Errors in the right place.** A row's own errors render inside that row. An error that
  belongs to a set as a whole — too few rows, a cross-row constraint — renders once, above
  every row in that set, never collapsed into the row-level messages.
- **A cap that's actually enforced.** `max_num` (with `validate_min`/`validate_max` set
  automatically alongside `min_num`/`max_num`) rejects a submission over the limit on the
  server, and disables the add control in the browser once the limit is reached.

## Reference

- [`<c-form.formset>` and `<c-form.formset.row>`](components.md#actions-user-misc) — the components this
  guide's examples render through.
- [`InlineFormSet`, `MVPInlineCreateView` and `MVPInlineUpdateView`](views.md#a-parent-and-its-related-rows) —
  the declaration class and the configured views for the parent-and-rows case.
