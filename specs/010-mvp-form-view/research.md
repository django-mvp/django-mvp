# Research: MVPFormView — Non-Model Form View

**Phase**: 0 — Outline & Research
**Branch**: `010-mvp-form-view`
**Date**: 2026-05-04

## Research Findings

### Finding 1 — `MVPFormView` stub already exists

**Decision**: Extend the existing stub rather than creating a new class.

**Rationale**: `mvp/views/edit.py` line 238 defines:
```python
class MVPFormView(MVPFormBase, generic.FormView):
    page_class = "mvp-form-page"
```
This stub already satisfies FR-001 through FR-004, FR-006, FR-007, FR-009, and FR-010
through inheritance. Only FR-005 and FR-008 require new code on the class body.

**Alternatives considered**: Creating a new class or moving `MVPFormView` to its own
file — rejected because the stub is already in the right place and consistent with the
existing layout of `edit.py`.

---

### Finding 2 — `SuccessMessageMixin.get_success_message()` API

**Decision**: Override `get_success_message()` on `MVPFormView` using `defaultdict(str, cleaned_data)`.

**Rationale**: Django's base `SuccessMessageMixin.get_success_message()` does
`self.success_message % cleaned_data`. When `cleaned_data` is a plain `dict`,
any `%(key)s` token whose key is absent raises `KeyError`. Wrapping in
`defaultdict(str, cleaned_data)` silently substitutes `""` for unknown tokens —
identical to the pattern already used by `MVPModelFormBase.get_success_message()`.

The difference from `MVPModelFormBase`:
- `MVPModelFormBase` injects `verbose_name` → `data["verbose_name"] = self.model_meta.verbose_name`
- `MVPFormView` MUST NOT inject `verbose_name` (no model available); the key is simply absent
  from the dict, so `%(verbose_name)s` → `""` if accidentally present.

**Alternatives considered**: Not overriding (keep vanilla `SuccessMessageMixin` behaviour) —
rejected because it would raise `KeyError` when a developer accidentally uses an unknown
`%(token)s` in a message, violating the spec's robustness requirement (FR-005 clarification).

---

### Finding 3 — `django.utils.text.camel_case_to_spaces()` API

**Decision**: Use `camel_case_to_spaces(self.__class__.__name__).title()` for the default title.

**Rationale**: `django.utils.text.camel_case_to_spaces("ContactFormView")` returns
`"contact form view"`. Applying `.title()` gives `"Contact Form View"`. This is a stable,
well-documented Django utility used internally by Django's own ORM (for `verbose_name`
generation from model class names). No third-party dependency needed.

**API signature** (confirmed from Django source):
```python
from django.utils.text import camel_case_to_spaces
camel_case_to_spaces("ContactFormView")  # → "contact form view"
```

**Override location**: `MVPFormView.get_page_title()` — NOT `MVPFormBase.get_page_title()`.
Placing it on `MVPFormView` only ensures model form views (`MVPCreateView`, `MVPUpdateView`,
`MVPDeleteView`) are unaffected; they supply their own `page_title` defaults via class
attributes set on those concrete classes.

**Alternatives considered**: Class-name as-is (no split) — rejected (unreadable:
`"ContactFormView"`). Empty string fallback — rejected per spec clarification Q2 answer.
A generic `"Form"` literal — rejected per spec clarification Q2 answer.

---

### Finding 4 — Existing test coverage

**Decision**: Append a new `TestMVPFormView` class to `tests/test_views/test_edit_view.py`.

**Rationale**: The file already imports `MVPFormView` and contains related helpers
(`make_next_url_view`, `RequestFactory` setup). Adding a focused class is consistent with
the existing structure and avoids creating a new test module for a two-method change.

**Tests required** (5 total):

| ID | Method under test | Scenario |
|----|------------------|---------|
| T001 | `get_success_message()` | Message with `%(email)s` and `email` in `cleaned_data` → substituted |
| T002 | `get_success_message()` | Message with unknown `%(foo)s` → `""` substituted, no `KeyError` |
| T003 | `get_success_message()` | `%(verbose_name)s` present → `""` substituted, no error, no model dependency |
| T004 | `get_page_title()` | No `page_title` set, class `ContactFormView` → `"Contact Form View"` |
| T005 | `get_page_title()` | Explicit `page_title = "My Form"` set → `"My Form"` (existing behaviour preserved) |

**Existing tests that already cover `MVPFormView`** (no changes needed):
- `test_form_view_no_next_with_success_url` (line 478) — FR-003
- `test_get_success_url_raises_improperly_configured` (line 526) — FR-006
- `test_base_template_name` (line 508) — FR-001
- `test_page_class` (line 514) — class-level attribute
- US3 next=list fallthrough test (line 355) — FR-004

## Resolved Unknowns

| Unknown | Resolved As |
|---------|------------|
| Is `MVPFormView` a new class or an extension? | Extension of existing stub |
| Does `get_success_message()` need a `defaultdict`? | Yes — same pattern as `MVPModelFormBase`, minus `verbose_name` injection |
| Where does `%(verbose_name)s` go when present? | Silently → `""` (not injected; not an error) |
| Default title source? | `camel_case_to_spaces(cls.__name__).title()` |
| Override location for `get_page_title()`? | `MVPFormView` only, not `MVPFormBase` |
| Contracts needed? | None — pure Python method additions, no external interface |
