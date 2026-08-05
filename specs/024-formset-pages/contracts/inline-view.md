# Contract: `MVPInlineCreateView` and `MVPInlineUpdateView`

**Module**: `mvp/views/inline.py` — exported from `mvp/views/__init__.py`.

A page carrying one record and one set of rows belonging to it. The developer configures the
two models and writes no code to build the formset, to validate the two parts together, or to
save them in the right order.

`InlineFormsetMixin` holds the configuration and the hooks. It is deliberately **not** exported,
matching the rule already stated in `mvp/views/__init__.py`: the package exports views, not
mixins.

---

## Configuration

| Attribute | Default | Meaning |
|---|---|---|
| `inline_model` | `None` | The related model. Required. |
| `inline_form_class` | `None` | Form class for a row. Defaults to a generated `ModelForm`. |
| `inline_fields` | `None` | Fields on a row, when no form class is given. |
| `inline_extra` | `1` | Blank rows rendered beyond the existing ones. |
| `inline_can_delete` | `True` | Whether rows may be removed. `False` suppresses every remove control (FR-026). |
| `inline_max_num` | `None` | Cap on rows. Enforced on the server **and** read by the add control. |

`inline_max_num` is a real cap, not a presentational one. Django's `inlineformset_factory`
defaults `validate_max=False`, so `max_num` alone rejects nothing: a submission carrying more
rows than the cap is accepted and saved, up to `max_num + 1000`. When `inline_max_num` is set,
`get_formset_factory_kwargs()` therefore also sets `validate_max=True` and an `absolute_max`
proportionate to the cap rather than Django's `max_num + 1000` default. The second half matters
independently of the first: `full_clean` constructs and validates every submitted form before it
reaches the too-many-forms check, so `absolute_max` is what bounds the work a single request can
demand.

Anything else — `min_num`, `validate_min`, a custom base formset class, `fk_name` where two
relations exist between the models — is supplied by overriding `get_formset_factory_kwargs()`.
It is **super-and-extend**, like Django's own `get_form_kwargs`: the base implementation derives
the dictionary from the six attributes above, and an override calls
`super().get_formset_factory_kwargs()` and mutates the result. One override point rather than an
attribute per Django parameter.

## Hooks

| Method | Contract |
|---|---|
| `get_formset_class()` | Builds the formset class from `get_formset_factory_kwargs()`. |
| `get_formset_kwargs()` | Instance-level kwargs: `instance`, and `data`/`files` on a POST. |
| `get_formset()` | Returns the formset, built once per request and reused. |
| `get_context_data()` | Adds `formset` to the context. |
| `form_valid(form)` | Validates the formset, then saves both atomically. |

`get_formset()` memoises deliberately. `form_invalid` re-renders through `get_context_data`, and
a second construction there would throw away the bound formset carrying the user's values and
its errors — the page would come back blank, breaking FR-013.

## Behaviour

**Rendering.** On `GET`, the parent's form and one row per existing related record are rendered
on one page, plus `inline_extra` blank rows (FR-009). Page title, breadcrumbs, page class,
actions and permission behaviour are inherited unchanged from the packaged single-form pages —
this feature adds no surface of its own (FR-015).

**Validation.** A submission is valid only when both the parent form and the formset are valid
(FR-010). If either fails, nothing is persisted and the page re-renders with every submitted
value still present in both parts (FR-013).

**Saving.** In one `transaction.atomic()` block, and in this order: the parent is saved, assigned
to `formset.instance`, and the formset is saved. A failure at any point leaves nothing persisted
(FR-011). `BaseInlineFormSet.save_new` reads `formset.instance` at save time, so assigning the
parent after creating it is what attaches rows to a brand-new record (FR-014).

The success message and the redirect are produced **after** the block exits. `super().form_valid()`
reaches `SuccessMessageMixin`, and Django's message storage is not transactional — a flash queued
inside the block survives the rollback, so a request that persisted nothing would still tell the
user the record was saved.

**Redirect.** Handled by the inherited `get_success_url()` — the `next` parameter, then a CRUD
shorthand, then `success_url`, then `get_absolute_url()`. Identical to the single-form pages
(FR-012).

**Create versus update.** `MVPInlineCreateView` extends `MVPCreateView`, `MVPInlineUpdateView`
extends `MVPUpdateView`. On create the formset is built against an unsaved parent instance,
which is what `BaseInlineFormSet` does when given no instance.

## Errors the view raises

| Condition | Result |
|---|---|
| `inline_model` unset | `ImproperlyConfigured`, naming the attribute. |

One guard, not two. Django's own `modelform_factory` already raises a clear `ImproperlyConfigured`
when neither fields nor a form class is given, so a second check would restate it; an unset
`inline_model` would otherwise surface as a `TypeError` from inside `inlineformset_factory`, which
names nothing the developer wrote.

## Worked configuration

```python
from mvp.views import MVPInlineUpdateView

from .models import OrderLine, Product


class ProductOrderLinesView(MVPInlineUpdateView):
    model = Product
    fields = ["name", "category"]
    inline_model = OrderLine
    inline_fields = ["quantity"]
    inline_extra = 1
    success_url = "list"
```

No template, no formset construction, no save logic.
