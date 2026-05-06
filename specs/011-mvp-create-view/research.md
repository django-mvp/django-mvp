# Research: MVPCreateView — Zero-Config Model Create View

**Feature**: `specs/011-mvp-create-view/spec.md`
**Date**: 2026-05-05
**Status**: Complete — all unknowns resolved

---

## RQ-001: How does `model_meta.verbose_name` behave and where is it available?

**Decision**: Use `self.model_meta.verbose_name` directly.

**Rationale**: `model_meta` is a `cached_property` defined on `ModelInfoMixin`
(`mvp/views/base.py`, line 297). `MVPCreateView` inherits from
`MVPModelFormBase → MVPFormBase → PageObjectMixin → CRUDDirectoryMixin → ModelInfoMixin`,
so `self.model_meta` is available in every instance method on `MVPCreateView` at
request time (i.e. after `model` or `form_class` is set). Django convention keeps
`verbose_name` lowercase (e.g. `"product"`, `"order line"`). To produce the display
string `"Create Product"` or `"Create Order Line"`, callers must apply `.title()`.

**Alternatives considered**: Accessing `self.model._meta.verbose_name` directly —
rejected because `model_meta` already handles the three-step fallback (model attribute,
queryset, form_class) and raises a clear `ImproperlyConfigured` when none is found.

---

## RQ-002: How does the breadcrumbs component handle a missing or empty list URL?

**Decision**: FR-006 ("plain text when no list URL") is **already satisfied** by the
existing `PageObjectMixin.get_breadcrumbs()` implementation. No override in
`MVPCreateView` is required for this requirement.

**Rationale**: `PageObjectMixin.get_breadcrumbs()` returns
`{"href": self.resolve_crud_url("list") or ""}`. When `resolve_crud_url("list")`
returns `None` (permission denied or no URL registered), the `or ""` substitutes an
empty string. The `django-cotton-bs5` breadcrumbs item component (`breadcrumbs/item.html`)
uses `{% with element=href|yesno:"a,span" %}` — Django's `|yesno` filter returns the
second option (`"span"`) for any falsy value, including `""`. The item therefore renders
as a `<span class="breadcrumb-item active">` with no anchor — correct plain-text
behaviour. No template changes are needed.

**Alternatives considered**: Returning `None` instead of `""` for missing list URLs —
behaviorally equivalent for `|yesno` (both are falsy), but an empty string is explicit
and consistent with the existing `MVPUpdateView.get_breadcrumbs()` pattern.

---

## RQ-003: Should `MVPCreateView` have its own `get_breadcrumbs()` override?

**Decision**: **No.** `PageObjectMixin.get_breadcrumbs()` already produces the
correct two-item breadcrumb for a create view:

```python
[
    {"text": self.get_list_title(), "href": self.resolve_crud_url("list") or ""},
    {"text": self.get_page_title()},
]
```

Once `get_page_title()` is overridden on `MVPCreateView` (RQ-001 above), the second
breadcrumb item will automatically reflect the model-aware title ("Create Product").
No override needed.

**Alternatives considered**: Overriding `get_breadcrumbs()` to omit the `href` key
entirely when the list URL is None — unnecessary; the breadcrumbs component handles
falsy `href` correctly (RQ-002).

---

## RQ-004: How should the success message verbose_name be capitalised?

**Decision**: Override `get_success_message()` on `MVPCreateView` to inject
`self.model_meta.verbose_name.title()` instead of the raw lowercase `verbose_name`.

**Rationale**: `MVPModelFormBase.get_success_message()` injects the raw
`self.model_meta.verbose_name` (lowercase, per Django convention — e.g. `"product"`).
With the existing `success_message = _("%(verbose_name)s successfully created.")`,
this produces `"product successfully created."` — sentence-start without a capital
letter. The spec (FR-004) requires `"Product successfully created."`. The fix is a
targeted override on `MVPCreateView` only, leaving `MVPModelFormBase`,
`MVPUpdateView`, and `MVPDeleteView` unaffected (preserving FR-010).

**Alternatives considered**:

1. Change `MVPModelFormBase.get_success_message()` to always title-case — rejected;
   violates FR-010 (would affect UpdateView and DeleteView tests).
2. Use a capitalised `verbose_name` in the `success_message` template string via
   a custom template filter — overly complex; no existing filter for in-string title-casing.
3. Change the `success_message` default to use `%(verbose_name)s` — requires
   injecting a new key; more invasive than a local override.

---

## RQ-005: Will overriding `get_success_message()` on `MVPCreateView` break existing tests?

**Decision**: **Yes — three existing tests in `TestGetSuccessMessage` must be relocated.**

**Rationale**: The three tests in `TestGetSuccessMessage` (lines ~515–540 of
`tests/test_views/test_edit_view.py`) use `make_create_view()` (which creates a
`MVPCreateView` subclass) as the test vehicle for `MVPModelFormBase.get_success_message()`
behaviour. They assert lowercase `verbose_name` output. After the override, those tests
will fail because `MVPCreateView.get_success_message()` now title-cases the name.

**Resolution**: Move the three `TestGetSuccessMessage` tests to a new `TestMVPUpdateView`
class (or relocate them to use a `MVPUpdateView`-based helper) to test
`MVPModelFormBase.get_success_message()` behaviour independently. Add a new
`TestMVPCreateViewSuccessMessage` class testing the title-cased output.

**Affected tests**:

- `TestGetSuccessMessage.test_verbose_name_only_resolves` — asserts `"product created."`
- `TestGetSuccessMessage.test_missing_field_placeholder_substitutes_empty_string` — asserts lowercase verbose_name
- `TestGetSuccessMessage.test_field_value_and_verbose_name_both_resolve` — asserts lowercase verbose_name

---

## RQ-006: Gating logic for `get_page_title()` — when to derive, when to use override?

**Decision**: Declare `page_title = _("Create %(verbose_name)s")` as a class-level
attribute (a translatable interpolation template). `get_page_title()` interpolates
`self.page_title` with `{"verbose_name": self.model_meta.verbose_name.title()}` when
truthy; when falsy, returns `self.page_title` as-is.

**Rationale**: Defining the template on the class makes the default visible in
`MVPCreateView.__dict__`, introspectable, and translatable without requiring a
runtime `gettext` call that assembles an unknown string. Subclasses that want
the default need not touch `page_title` at all. Subclasses that override `page_title`
with any truthy string (with or without a `%(verbose_name)s` placeholder) get that
string interpolated. Subclasses that explicitly set `page_title = None / False / ""`
have that value returned as-is — a deliberate override, not a fallback trigger.

This differs from the `MVPFormView.get_page_title()` pattern (`if self.page_title:
return str(self.page_title)` → class-name derivation) because `MVPCreateView` has
no meaningful class-name fallback; the template IS the default, living on the class.

**Alternatives considered**: `if self.page_title: return str(self.page_title)` — the
`MVPFormView` pattern. Rejected: it makes an empty-string override silently fall
through to a derived value, which violates the principle that an explicit `page_title`
assignment is the caller's intent.

---

## RQ-007: How to produce the default title — f-string vs `_()` interpolation?

**Decision**: Use `_("Create %(verbose_name)s")` as the class-level `page_title`
attribute. `get_page_title()` interpolates it with `self.model_meta.verbose_name.title()`
at request time.

**Rationale**: Storing the pattern in `page_title` as a translatable lazy string
means the "Create" prefix is properly extracted by `makemessages` and translatable
per locale. The `%(verbose_name)s` placeholder is filled at request time with the
model's verbose name, so the full string is both i18n-correct and model-aware.
Using a plain f-string (the earlier approach) left "Create " hardcoded in English
and invisible to `makemessages`.

**Alternatives considered**: Plain `f"Create {self.model_meta.verbose_name.title()}"`
— rejected; the "Create" prefix is untranslatable. Wrapping the entire assembled
string in `gettext_lazy` — not possible, because lazy strings must be fixed at
import time.

---

## Summary of Resolved Unknowns

| RQ | Question | Resolution |
|----|----------|------------|
| RQ-001 | `model_meta` availability and `verbose_name` casing | Available via inheritance; must `.title()` |
| RQ-002 | Breadcrumb `href` for missing list URL | Already handled; `"" | yesno` → `<span>` |
| RQ-003 | Need for `get_breadcrumbs()` override | No — base class sufficient |
| RQ-004 | Success message capitalisation | Override `get_success_message()` on `MVPCreateView` |
| RQ-005 | Impact on existing tests | 3 tests must be relocated to `MVPUpdateView` vehicle |
| RQ-006 | `get_page_title()` gating logic | Class-level template `_("Create %(verbose_name)s")`; falsy overrides returned as-is |
| RQ-007 | Default title format | `_("Create %(verbose_name)s")` on class; interpolated at request time |
