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
rows than the cap is accepted and saved. When `inline_max_num` is set,
`get_formset_factory_kwargs()` therefore also sets `validate_max=True`.

**`absolute_max` is left at Django's default and must not be derived from the cap.** Django's
`absolute_max` check reads the *raw* submitted `TOTAL_FORMS` and, unlike the `validate_max` check,
does not subtract the rows marked for deletion — and `total_form_count()` clamps to it, so every
row past the bound is dropped before validation and never re-rendered. Binding it to the cap would
therefore reject submissions that are legitimately within the cap the moment a user adds and
removes rows in the same sitting, and would silently discard what they typed, against FR-013. It
would also make a record with pre-existing rows above the cap permanently uneditable through this
view, because the very submission that removes the surplus is the one rejected. `absolute_max`
stays the memory-exhaustion backstop Django intends, at the same ceiling every other Django inline
formset already has.

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

The success message and the redirect are produced **after** the block exits, and **not** by calling
`super().form_valid()`. Two reasons, and both matter:

- Django's message storage is not transactional, so a flash queued inside the block survives a
  rollback — a request that persisted nothing would still tell the user the record was saved.
- `super().form_valid()` reaches `SuccessMessageMixin`, whose first statement delegates to
  `ModelFormMixin.form_valid`, whose first statement is `self.object = form.save()`. Neither
  `MVPCreateView` nor `MVPUpdateView` overrides it, so calling it after the block would save the
  parent a **second** time, outside the transaction and after the rows were written — an extra
  `UPDATE` of every field, a second `_save_m2m`, and a consuming project's `post_save` receivers
  firing twice for one user action.

So `form_valid` queues the message and returns the redirect itself:

```python
with transaction.atomic():
    self.object = form.save()
    formset.instance = self.object
    formset.save()
success_url = self.get_success_url()
messages.success(self.request, self.get_success_message(form.cleaned_data))
return HttpResponseRedirect(success_url)
```

**The success URL is resolved after the saves, not before them.** On the create path Django sets
`self.object = None` before `form_valid` runs, and `get_success_url()` needs the saved object: with
no `success_url` set it falls through to `object.get_absolute_url()` and raises
`ImproperlyConfigured` when there is no object, and with `success_url = "detail"` it fails to
resolve the shorthand — `get_url_kwargs` has no pk — and silently returns the literal string
`"detail"` as a relative path. Either way the rows are already committed. This is the same order
`ModelFormMixin.form_valid` uses: save, then resolve.

`MVPDeleteView.form_valid` is the precedent for producing the message and redirect directly, but
**not** for the ordering — it resolves the URL first because its object is about to be deleted,
and its success-URL chain has no `get_absolute_url()` step. That reason does not transfer here.

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
