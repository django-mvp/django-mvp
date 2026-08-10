# Formsets

django-mvp renders a Django formset with the same packaged look as a single form —
management form, one row per form, per-row and set-level errors, and add/remove controls
that work in the browser without a page reload or a build step. This guide walks the whole
path from a model and its related model to a rendered page, then covers the standalone case:
a formset with no parent record at all.

## A parent and its rows

The common case is a parent record edited alongside a set of rows that belong to it — an
order and its line items, a survey and its questions. Start from two related models:

```python
# models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)


class OrderLine(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_lines")
    quantity = models.PositiveIntegerField(default=1)
```

Configure one view with `MVPInlineUpdateView`:

```python
# views.py
from django.utils.translation import gettext_lazy as _

from mvp.views import MVPInlineUpdateView

from .models import OrderLine, Product


class ProductOrderLinesView(MVPInlineUpdateView):
    model = Product
    fields = ["name", "category"]
    inline_model = OrderLine
    inline_fields = ["quantity"]
    inline_extra = 1
    inline_title = _("Order lines")
    inline_description = _("Add a row per order, or remove one to drop it when you save.")
    success_url = "list"
```

Wire it to a URL, the same as any other model view:

```python
# urls.py
path("products/<int:pk>/order-lines/", ProductOrderLinesView.as_view(), name="product-order-lines"),
```

That's the whole configuration. No template markup for the rows, and no code to build,
validate or save the formset:

- **Rendering.** `GET` renders the parent's form and one row per existing `OrderLine`, plus
  `inline_extra` blank rows. The view's default template (`form_view.html`) already renders
  `{{ formset }}` through `<c-form.formset>` when one is in context — see
  [Components](components.md#actions-user-misc) for what that component renders.
- **Telling the two parts of the page apart.** The set opens with a divider and a heading, so
  the rows do not read as more fields on the parent's form. `inline_title` sets that heading
  and defaults to the related model in plural; `inline_description` puts help text under it and
  is omitted when unset. Each row is boxed and labelled with the object it edits — the object's
  own string once it is saved, and its model name before that.
- **Removing a row.** The control is a trash icon in the row's top right, kept transparent
  until the row is hovered or something in it takes focus. Its label is the accessible name
  rather than visible text, and it is overridable with the `remove-label` attribute.
- **Adding and removing rows.** The add control clones the row markup in the browser; removing
  a row hides it and marks it for deletion (a saved row) or drops it (an unsaved one). Neither
  needs a page reload.
- **Validation and saving.** A submission is only valid when the parent form and every row are
  valid. On success the parent is saved, the rows are attached to it, and both save in one
  transaction — nothing is half-persisted.

See [Views](views.md#forms-create--update--generic) for the rest of `MVPInlineUpdateView`'s
configuration surface — `inline_form_class`, `inline_can_delete`, `inline_max_num`, and the
`get_formset_factory_kwargs()` override point for anything beyond it.

## The standalone case

A formset does not need a parent record at all. Rendering is generic: any packaged form view
that puts a formset in its context renders it in the right place, with no further
configuration. Build the formset yourself and add it in `get_context_data`:

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
  belongs to the set as a whole — too few rows, a cross-row constraint — renders once, above
  every row, never collapsed into the row-level messages.
- **A cap that's actually enforced.** `inline_max_num` (or `max_num` plus `validate_max=True`
  on a formset you build yourself) rejects a submission over the limit on the server, and
  disables the add control in the browser once the limit is reached.

## Reference

- [`<c-form.formset>` and `<c-form.formset.row>`](components.md#actions-user-misc) — the components this
  guide's examples render through.
- [`MVPInlineCreateView` and `MVPInlineUpdateView`](views.md#forms-create--update--generic) —
  the configured view for the parent-and-rows case.
