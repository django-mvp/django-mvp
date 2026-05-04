# Data Model: MVPFormView — Non-Model Form View

**Phase**: 1 — Design
**Branch**: `010-mvp-form-view`
**Date**: 2026-05-04

## Entities

This feature introduces no new data models, database tables, or Django models.

## Class Design

### `MVPFormView` (extension of existing stub)

**Location**: `mvp/views/edit.py`
**Inheritance**: `MVPFormBase`, `generic.FormView`

```
MVPFormView
├── Inherited from MVPFormBase:
│   ├── base_template_name = "form_view.html"      # FR-001
│   ├── get_success_url()                           # FR-003, FR-004, FR-006, FR-010
│   └── get_next_url() / get_next_candidate()       # FR-004
├── Inherited from SuccessMessageMixin (via MVPFormBase):
│   └── (get_success_message overridden below)
├── Inherited from PageMixin (via MVPFormBase → PageObjectMixin → PageMixin):
│   ├── page_title = ""
│   ├── page_subtitle = ""
│   ├── page_class (already set to "mvp-form-page")
│   └── get_page_title() (overridden below)         # FR-008
├── Inherited from generic.FormView:
│   └── form validation lifecycle                   # FR-002
│
├── NEW: get_success_message(cleaned_data)           # FR-005
│   └── defaultdict(str, cleaned_data) — no verbose_name injection
│
└── NEW: get_page_title()                            # FR-008
    └── camel_case_to_spaces(cls.__name__).title()
        when self.page_title is falsy
```

### Attribute Contract

| Attribute | Type | Default | Source | Notes |
|-----------|------|---------|--------|-------|
| `form_class` | `type[Form]` | — | Developer sets | Required; Django raises if absent |
| `success_url` | `str \| Promise \| None` | `None` | Developer sets | Coerced to `str` before use |
| `success_message` | `str` | `""` | Developer sets | `%(field)s` tokens resolved from `cleaned_data` |
| `page_title` | `str \| Promise` | `""` | Developer sets | Falls back to class-name split when falsy |
| `page_subtitle` | `str \| Promise` | `""` | Developer sets | Passed through to layout |
| `page_icon` | `str \| None` | `None` | Developer sets | Passed through to layout |
| `page_class` | `str` | `"mvp-form-page"` | Class attribute | Applied to page wrapper |
| `breadcrumbs` | `list` | `[]` | Developer sets | Passed through to layout |

## Validation Rules

- `form_class` absent → Django's `FormMixin.get_form_class()` raises `ImproperlyConfigured`
  (no additional validation added by this feature)
- `success_url` absent AND no valid `?next=` → `MVPFormBase.get_success_url()` raises
  `ImproperlyConfigured` with a named, actionable error message

## State Transitions

None. `MVPFormView` is stateless between requests.
