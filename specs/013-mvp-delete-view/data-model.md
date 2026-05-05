# Data Model: MVP Delete View

**Phase**: 1 | **Feature**: `013-mvp-delete-view`

---

## Overview

This feature adds no new Django models or database migrations. The data model describes the **public class interface** of `MVPDeleteView`, the **updated `DeleteConfirmForm`**, and the **template context contract** — the three surfaces that must stay in sync for the four deletion scenarios to work correctly.

---

## 1. `MVPDeleteView` — class attribute model

### Inheritance chain (MRO order)

```
MVPDeleteView
  → MVPModelFormBase
      → MVPFormBase
          → SuccessMessageMixin        (django.contrib.messages.views)
          → BaseTemplateNameMixin      (mvp.views.base)
          → NextURLMixin               (mvp.views.edit)
          → PageObjectMixin            (mvp.views.detail)
              → CRUDDirectoryMixin     (mvp.views.detail)
              → PageMixin              (mvp.views.base)
  → generic.DeleteView
      → BaseDeleteView
          → DeletionMixin             (django.views.generic.edit)
          → FormMixin                 (django.views.generic.edit)
          → BaseDetailView            (django.views.generic.detail)
```

### Class-level attributes

| Attribute | Type | Default | Settable by developer | Description |
|---|---|---|---|---|
| `base_template_name` | `str` | `"delete_view.html"` | No | Fallback template name (from `BaseTemplateNameMixin`) |
| `page_title` | `str \| lazy str` | `_("Delete %(verbose_name)s")` | Yes | Page heading interpolation template |
| `page_icon` | `str` | `"delete"` | Yes | Material icon identifier |
| `page_class` | `str` | `"mvp-delete-page"` | Yes | Extra CSS classes on the page wrapper |
| `success_message` | `str \| lazy str` | `_("%(verbose_name)s successfully deleted.")` | Yes | Flash message template after deletion |
| `show_related_objects` | `bool` | `False` | Yes | Opt-in: show cascade-deleted related records |
| `require_confirmation` | `bool` | `False` | Yes | Opt-in: require user to type confirmation string |
| `confirmation_label` | `str \| lazy str` | `_("Type the name to confirm")` | Yes | Label text for the type-to-confirm input |
| `related_objects_max_per_group` | `int` | `25` | Yes | Display cap per related-object group |

### Override hooks

| Method | Return type | When to override |
|---|---|---|
| `get_confirmation_value()` | `str` | Change what the user must type (default: `str(self.object)`) |
| `get_back_url()` | `str` | Customise the Go Back button destination |
| `get_breadcrumbs()` | `list[dict]` | Replace the List → Detail → Delete breadcrumb trail |
| `get_page_title()` | `str` | Dynamic page titles (inherited from `MVPModelFormBase`) |
| `get_success_message(cleaned_data)` | `str` | Custom flash message text (inherited from `MVPModelFormBase`) |
| `get_success_url()` | `str` | Custom post-delete redirect destination |

### Method implementations (new or changed)

#### `get_form_class(self)` *(override)*

Returns `DeleteConfirmForm` when `self.require_confirmation is True`; otherwise returns the default `django.forms.Form` (always valid, no fields).

#### `get_form_kwargs(self)` *(override)*

Injects `confirmation_value=self.get_confirmation_value()` into the form kwargs when `require_confirmation is True`.

#### `post(self, request, *args, **kwargs)` *(override)*

1. Sets `self.object = self.get_object()`.
2. Calls `_collect_deletion_data()`.
3. If `protected_objects` is non-empty → returns early with `render_to_response(get_context_data())`.
4. Otherwise calls `get_form()` → `form_valid()` or `form_invalid()`.

#### `form_valid(self, form)` *(override)*

1. Computes `success_url = self.get_success_url()`.
2. Calls `self.object.delete()`.
3. Calls `messages.success(request, self.get_success_message({}))`.
4. Returns `HttpResponseRedirect(success_url)`.

#### `get_breadcrumbs(self)` *(new)*

Returns `[{"text": list_title, "href": list_url}, {"text": str(object), "href": detail_url}, {"text": page_title}]`.

#### `get_back_url(self)` *(new)*

Reads `?back` from `request.GET`, validates it with `url_has_allowed_host_and_scheme`, falls back to `resolve_crud_url("list")`.

#### `get_next_url(self)` *(override)*

Returns the validated `?next=` parameter value (via `super()`) or `resolve_crud_url("list")` when absent.

#### `get_success_url(self)` *(override)*

Priority: validated `?next=` POST value → `self.success_url` (if set) → list URL from CRUD directory. Never falls back to `object.get_absolute_url()`.

#### `get_context_data(self, **kwargs)` *(override)*

Adds delete-specific context keys to the base context (see Template Context Contract below).

#### `_collect_deletion_data(self)` *(private)*

Uses `django.db.models.deletion.Collector` to determine cascade relations and protection state. Returns `(related_map: dict[Model, list], protected_objects: list)`. Called from both `get_context_data()` and `post()`.

---

## 2. `DeleteConfirmForm` — updated form

**File**: `mvp/forms.py`

```
DeleteConfirmForm(forms.Form)
  Fields:
    - confirmation (CharField, required, autocomplete=off)
  Init kwargs:
    - confirmation_value (str | None = None)  — injected by view
  Validation:
    - clean_confirmation(): strips whitespace, raises ValidationError
      when value != confirmation_value (when confirmation_value is not None)
  Error message:
    - _("The value you entered does not match. Please try again.")
```

**Change from current**: adds `confirmation_value` `__init__` kwarg and `clean_confirmation()` field validator. The single-field `CharField` presence check is retained (empty submission is caught by `required=True`).

---

## 3. Template context contract

Context variables available to `delete_view.html` on both GET and the POST→invalid re-render:

| Variable | Type | Scenario | Description |
|---|---|---|---|
| `object` | model instance | all | The record targeted for deletion |
| `is_protected` | `bool` | all | True when a PROTECT FK blocks deletion |
| `protected_objects` | `list` | 3 | Objects blocking deletion (empty otherwise) |
| `related_objects` | `list[tuple]` | 2 | Triples `(label: str, display_list: list, overflow_count: int)` |
| `require_confirmation` | `bool` | 4 | True when type-to-confirm mode is active |
| `confirmation_value` | `str` | 4 | String user must type; `""` when not required |
| `confirmation_label` | `str` | 4 | Input placeholder/label text |
| `back_url` | `str` | all | Go Back button destination |
| `next_url` | `str` | all | Hidden `next` field value for post-delete redirect |
| `form` | `Form` | all | Django form (for CSRF and confirmation field when active) |

### `related_objects` tuple structure change

The current shape `(label, objs_list)` becomes `(label, display_list, overflow_count)`:
- `label` — `model._meta.verbose_name_plural.title()`
- `display_list` — at most `related_objects_max_per_group` instances
- `overflow_count` — `max(0, total - cap)` — zero means no truncation

The `delete_view.html` template must be updated to unpack all three elements and render the "… and N more" note when `overflow_count > 0`.

---

## 4. `delete_view.html` — template changes

**File**: `mvp/templates/delete_view.html`

Changes required:
1. Update the related-objects loop from `{% for label, objs in related_objects %}` to `{% for label, objs, overflow in related_objects %}`.
2. Add conditional overflow note inside the loop: `{% if overflow %}<p class="text-muted mb-0">… and {{ overflow }} more</p>{% endif %}`.
3. No other structural changes — the four-scenario branching (`is_protected` / `related_objects` / `require_confirmation`) remains in place.

---

## 5. File change summary

| File | Change type | Reason |
|---|---|---|
| `mvp/views/edit.py` | Rewrite `MVPDeleteView` | Inheritance-first design, Django 5.x form machinery |
| `mvp/forms.py` | Update `DeleteConfirmForm` | Add `confirmation_value` injection and field-level validation |
| `mvp/templates/delete_view.html` | Update related-objects loop | Unpack overflow count, render "N more" note |
| `tests/test_views/test_delete_view.py` | Update + extend tests | Cover new form contract, overflow truncation, breadcrumbs |
| `skills/django-mvp/SKILL.md` | Update | Document public API changes |
