# API Contract: MVPDeleteView

**Feature**: `013-mvp-delete-view` | **Type**: Class-Based View (Python)

---

## Class: `MVPDeleteView`

**Module**: `mvp.views.edit` (re-exported from `mvp.views`)
**Base classes**: `MVPModelFormBase`, `django.views.generic.DeleteView`

A configurable Django class-based view that handles all four deletion scenarios — simple confirmation, related-objects summary, protected-record detection, and type-to-confirm — from a single class.

---

### Minimum viable subclass

```python
from mvp.views import MVPDeleteView
from myapp.models import Product

class ProductDeleteView(MVPDeleteView):
    model = Product
    success_url = "list"          # CRUD shorthand or literal URL path
```

No template override, no extra methods, no form wiring required.

---

### Configuration attributes

#### Required (inherited from Django)

| Attribute | Type | Notes |
|---|---|---|
| `model` | `type[Model]` | The Django model class to delete |

#### Optional — defaults cover all four scenarios

| Attribute | Type | Default | Description |
|---|---|---|---|
| `success_url` | `str \| None` | `None` | Post-delete redirect. Accepts CRUD shorthand (`"list"`) or a literal path. When `None`, falls back to the list URL from the CRUD directory. |
| `show_related_objects` | `bool` | `False` | Set to `True` to display a grouped list of cascade-deleted records before the user confirms. |
| `require_confirmation` | `bool` | `False` | Set to `True` to require the user to type the record's name (or custom string) before deletion proceeds. |
| `confirmation_label` | `str \| lazy str` | `_("Type the name to confirm")` | Placeholder / label text for the type-to-confirm input. |
| `related_objects_max_per_group` | `int` | `25` | Maximum number of related records to show per group. Groups exceeding this limit display a "… and N more" note. |
| `page_title` | `str \| lazy str` | `_("Delete %(verbose_name)s")` | Page heading. `%(verbose_name)s` is replaced with the model's title-cased `verbose_name` at runtime. |
| `page_icon` | `str` | `"delete"` | Material icon name for the page header. |
| `page_class` | `str` | `"mvp-delete-page"` | CSS class(es) on the page wrapper (in addition to `"mvp-page"`). |
| `success_message` | `str \| lazy str` | `_("%(verbose_name)s successfully deleted.")` | Flash message template. `%(verbose_name)s` is the model's `verbose_name`. |

#### CRUD directory permissions (inherited from `CRUDDirectoryMixin`)

| Attribute | Type | Default | Effect |
|---|---|---|---|
| `has_list_permission` | `bool \| callable` | `False` | When truthy, the List breadcrumb and Go Back fallback render as links |
| `has_detail_permission` | `bool \| callable` | `False` | When truthy, the Detail breadcrumb renders as a link |

---

### Override hooks

| Method | Signature | Default | When to override |
|---|---|---|---|
| `get_confirmation_value()` | `() → str` | `str(self.object)` | Return a different string the user must type |
| `get_back_url()` | `() → str` | Validated `?back=` or list URL | Customise the Go Back button destination |
| `get_breadcrumbs()` | `() → list[dict]` | `[list, detail, delete]` | Replace the three-level breadcrumb trail |
| `get_page_title()` | `() → str` | Interpolated `page_title` | Dynamic page title |
| `get_success_message(cleaned_data)` | `(dict) → str` | Interpolated `success_message` | Custom flash message |
| `get_success_url()` | `() → str` | `?next=` → `success_url` → list | Custom post-delete redirect |

---

### HTTP protocol

#### `GET /path/to/<pk>/delete/`

Returns `200 OK` with the confirmation page. Context populated with all scenario-specific variables.

**Response**: `200 OK`, renders `delete_view.html` (or app-specific override).

#### `POST /path/to/<pk>/delete/`

**Success path (delete executed)**:

- Object is not protected AND (confirmation not required OR submitted value matches).
- Object is deleted, success message is added, redirect issued.
- **Response**: `302 Found` → `success_url` / list.

**Failure paths (object not deleted)**:

- Object is **protected**: re-renders page with `is_protected=True` and `protected_objects` list.
  - **Response**: `200 OK`.
- Type-to-confirm submitted with **wrong value**: `form_invalid()` re-renders with form errors.
  - **Response**: `200 OK`.

---

### Template context contract

All keys below are available in `delete_view.html`:

| Key | Type | Present when | Description |
|---|---|---|---|
| `object` | `Model` | always | Target record |
| `is_protected` | `bool` | always | `True` when PROTECT FK blocks deletion |
| `protected_objects` | `list` | always | Blocking records (empty when not protected) |
| `related_objects` | `list[tuple]` | always | `(label, display_list, overflow_count)` triples |
| `require_confirmation` | `bool` | always | Mirrors `self.require_confirmation` |
| `confirmation_value` | `str` | always | Expected string; `""` when `require_confirmation=False` |
| `confirmation_label` | `str` | always | Input placeholder text |
| `back_url` | `str` | always | Go Back button href |
| `next_url` | `str` | always | Hidden next-redirect field value |
| `form` | `Form` | always | Django form (provides CSRF; contains `confirmation` field when active) |
| `page` | `dict` | always | `{title, subtitle, icon, class, breadcrumbs}` |

---

### Scenario quick reference

| Scenario | Config | Key context flags |
|---|---|---|
| 1 — Simple confirmation | (none) | `is_protected=False`, `related_objects=[]`, `require_confirmation=False` |
| 2 — Related-objects summary | `show_related_objects = True` | `is_protected=False`, `related_objects` non-empty |
| 3 — Protected-record detection | (none, auto) | `is_protected=True`, `protected_objects` non-empty, Delete button absent |
| 4 — Type-to-confirm | `require_confirmation = True` | `require_confirmation=True`, `confirmation_value` set |

---

### `DeleteConfirmForm`

**Module**: `mvp.forms`

Single-field form used as the `form_class` when `require_confirmation = True`.

| Init kwarg | Type | Description |
|---|---|---|
| `confirmation_value` | `str \| None` | The expected string; injected by the view via `get_form_kwargs()` |

**Validation**: `clean_confirmation()` strips whitespace from the submitted value and raises `ValidationError` if the result does not match `confirmation_value`. Empty submissions are caught by `required=True` on the field.

Developers do not instantiate this form directly; the view wires it automatically.
