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
| `inline_max_num` | `None` | Cap on rows. Passed to Django and read by the add control. |

Anything else — `min_num`, `validate_min`, `validate_max`, a custom base formset class — is
supplied by overriding `get_formset_factory_kwargs()`, which returns the full keyword dictionary
handed to `inlineformset_factory`. One override point rather than an attribute per Django
parameter.

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

**Saving.** In one `transaction.atomic()` block: the parent is saved, assigned to
`formset.instance`, and the formset is saved. A failure at any point leaves nothing persisted
(FR-011). `BaseInlineFormSet.save_new` reads `formset.instance` at save time, so assigning the
parent after creating it is what attaches rows to a brand-new record (FR-014).

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
| Neither `inline_form_class` nor `inline_fields` set | `ImproperlyConfigured`, naming both. |

Configuration mistakes fail at request time with an actionable message rather than as a
`TypeError` out of `inlineformset_factory`.

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
