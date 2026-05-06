# Research: MVP Delete View

**Phase**: 0 | **Feature**: `013-mvp-delete-view`

---

## 1. Django 5.x `DeleteView` form machinery

**Decision**: Use Django 5.x `BaseDeleteView` form machinery (`FormMixin` + `DeletionMixin`) as the inheritance foundation rather than overriding `post()` monolithically.

**Rationale**:  
In Django 5.x `BaseDeleteView` inherits from `DeletionMixin`, `FormMixin`, and `BaseDetailView`. `FormMixin` provides a well-defined `get_form()` / `get_form_class()` / `get_form_kwargs()` / `form_valid()` / `form_invalid()` pipeline that maps naturally onto all four delete scenarios:

| Scenario | Form Class | Path |
|---|---|---|
| Simple confirmation | `Form` (default, always valid) | `form_valid()` → delete |
| Related objects | `Form` (default, always valid) | `form_valid()` → delete |
| Protected object | N/A (handled in `post()` before form processing) | early re-render |
| Type-to-confirm | `DeleteConfirmForm` with `confirmation_value` kwarg | `form_valid()` → delete; `form_invalid()` → re-render with error |

`form_valid()` and `form_invalid()` provide natural hooks that avoid the current monolithic `post()` override.

**Key API surface used**:

- `get_form_class()` — overridden to return `DeleteConfirmForm` when `require_confirmation = True`.
- `get_form_kwargs()` — overridden to inject `confirmation_value` into the form.
- `form_valid(form)` — overridden to perform the delete and emit the success message.
- `form_invalid(form)` — standard Django; re-renders the template with `form.errors` in context.
- `post(request, *args, **kwargs)` — overridden to set `self.object` and run the protection check before invoking form machinery.

**Alternatives considered**:  

- Keep the monolithic `post()` override from the existing sketch. Rejected: forces all branching into one method, breaks separation of concerns, and cannot re-use Django's `form_valid`/`form_invalid` pipeline.
- Use `delete()` override. Rejected: Django 5.x `BaseDeleteView` no longer calls `delete()`; it routes through `FormMixin.post()` → `form_valid()` instead.

---

## 2. `DeleteConfirmForm` validation design

**Decision**: Move the confirmation-value match into the form itself rather than validating it manually in the view.

**Rationale**:  
Injecting `confirmation_value` via `__init__` and validating it in `clean_confirmation()` means the form's `is_valid()` call handles both presence and match validation in one step. The view's `form_valid()` path is then unconditionally safe to delete — no second-layer check needed. This is idiomatic Django form design.

**Implementation**:

```python
class DeleteConfirmForm(forms.Form):
    confirmation = forms.CharField(...)

    def __init__(self, *args, confirmation_value=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._confirmation_value = confirmation_value

    def clean_confirmation(self):
        value = self.cleaned_data["confirmation"].strip()
        if self._confirmation_value and value != self._confirmation_value:
            raise forms.ValidationError(
                _("The value you entered does not match. Please try again.")
            )
        return value
```

**View wiring**:

```python
def get_form_class(self):
    if self.require_confirmation:
        return DeleteConfirmForm
    return super().get_form_class()  # returns django.forms.Form

def get_form_kwargs(self):
    kwargs = super().get_form_kwargs()
    if self.require_confirmation:
        kwargs["confirmation_value"] = self.get_confirmation_value()
    return kwargs
```

**Alternatives considered**:

- Validate the match in `form_valid()` (existing approach). Rejected: `form_valid()` should be the "all-OK" path; adding a conditional re-render inside it blurs the `valid/invalid` contract.
- Subclass `DeleteConfirmForm` per view to hardcode the value. Rejected: unnecessary coupling; `get_form_kwargs()` is the idiomatic injection point.

---

## 3. Cascade/protection inspection via Django's `Collector`

**Decision**: Use `django.db.models.deletion.Collector` to gather cascade and protection data synchronously on page load.

**Rationale**:  
`Collector.collect()` raises `ProtectedError` if any `PROTECT` FK references the object. Otherwise `collector.data` yields `{model: set-of-instances}` for all cascade relations. This is the same code path Django's own delete machinery uses, so the displayed data exactly matches what `object.delete()` would do — no possibility of divergence.

**Caching strategy**: `_collect_deletion_data()` is called at most once per request path:

- GET: called from `get_context_data()`.
- POST (protection check): called from `post()` override before form processing.
- POST (form_invalid re-render): called again from `get_context_data()`.

For a delete view, a maximum of two Collector traversals per request is acceptable. No explicit caching is added to keep the code simple (the view is not performance-critical and the dataset is bounded by the model's FK graph).

**Alternatives considered**:

- Cache via `functools.cached_property`. Would save one traversal on the POST→invalid path but adds complexity. Deferred: not worth the added surface area for this feature.
- Use `QuerySet.delete(keep_parents=True)` to get related counts. Rejected: `delete()` on a queryset does not raise `ProtectedError` for a single object lookup pre-deletion; the Collector is the right tool.

---

## 4. Related-objects display cap

**Decision**: Truncate each group at `related_objects_max_per_group` (default 25) in the view layer; pass a `(label, display_list, overflow_count)` triple to the template.

**Rationale**:  
Keeping truncation in the view keeps the template dumb — it just iterates `display_list` and conditionally renders "… and N more" when `overflow_count > 0`. The cap is a class attribute so developers can raise or lower it without subclassing beyond changing the value.

**Context structure**:

```python
# In get_context_data():
related_objects = []
for model, instances in related_map.items():
    label = model._meta.verbose_name_plural.title()
    cap = self.related_objects_max_per_group
    display = instances[:cap]
    overflow = max(0, len(instances) - cap)
    related_objects.append((label, display, overflow))
context["related_objects"] = related_objects
```

**Alternatives considered**:

- Do truncation in the template with `|slice`. Rejected: pushes business logic into templates; the overflow count cannot be computed in a template filter without custom tags.
- Always load all instances (no cap). Rejected: a model with thousands of cascade children would fill memory and produce an unusable page.

---

## 5. `SuccessMessageMixin` interaction

**Decision**: Emit the success message directly in `MVPDeleteView.form_valid()` via `messages.success()` rather than relying on `SuccessMessageMixin`.

**Rationale**:  
`MVPDeleteView` inherits `SuccessMessageMixin` through `MVPModelFormBase → MVPFormBase`. `SuccessMessageMixin.form_valid()` calls `super().form_valid()` first, then adds the message. Since `MVPDeleteView.form_valid()` overrides the entire method and does not call `super().form_valid()`, `SuccessMessageMixin` never fires. Calling `messages.success()` directly is the correct and explicit approach.

`get_success_message({})` (from `MVPModelFormBase`) is still used for message formatting — it injects `verbose_name` into the template — so the message text machinery is inherited correctly.

**Alternatives considered**:

- Call `super().form_valid(form)` to trigger `SuccessMessageMixin`. Rejected: Django's `DeletionMixin.form_valid()` calls `self.object.delete()` which would double-delete.

---

## 6. `get_success_url()` and post-delete redirect

**Decision**: Minimal override — call `super().get_success_url()` (inheriting steps 1–3 from `MVPModelFormBase`) and catch `ImproperlyConfigured` to replace step 4 (`object.get_absolute_url()`) with `resolve_crud_url("list")`.

**Rationale**:  
After deletion the object no longer exists; `object.get_absolute_url()` would return a 404. `MVPModelFormBase.get_success_url()` already implements the full priority chain (next URL → success_url shorthand → success_url literal → object URL → raise). The delete view's only special requirement is suppressing step 4. Duplicating the full chain in `MVPDeleteView` would be redundant.

**Full priority chain** (inherited + patched):

```
1. get_next_url()          → validated ?next= / CRUD shorthand (from MVPModelFormBase)
2. success_url as shorthand → resolved via resolve_crud_url() (from MVPModelFormBase)
3. success_url literal      → used verbatim (from MVPModelFormBase)
4. resolve_crud_url("list") → list URL fallback (DELETE override — replaces object.get_absolute_url())
5. ImproperlyConfigured     → raised if list URL is also unresolvable
```

---

## 7. Breadcrumb structure

**Decision**: List → Detail → Delete (three-level, mirrors `MVPUpdateView`).

**Rationale**:  
The breadcrumb links are gated by `has_list_permission` and `has_detail_permission` respectively (via `resolve_crud_url()`). When a permission is absent, the link renders as plain text — consistent with `MVPUpdateView.get_breadcrumbs()`.

```python
def get_breadcrumbs(self):
    return [
        {"text": self.get_list_title(), "href": self.resolve_crud_url("list")},
        {"text": str(self.object), "href": self.resolve_crud_url("detail")},
        {"text": self.get_page_title()},
    ]
```
