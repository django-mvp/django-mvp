# Research: Model Resolution Mixin

**Branch**: `005-model-resolution-mixin` | **Date**: 2026-05-03
**Purpose**: Audit the current `ModelInfoMixin` implementation against the spec's requirements; identify gaps; determine what work is required.

---

## Research Question 1: Does the current implementation satisfy FR-001 through FR-011?

**Task**: Verify that `ModelInfoMixin` in `mvp/views/detail.py` satisfies each functional requirement in the spec, excluding FR-013 (module location), which is a known gap addressed separately.

**Findings**:

Reviewing `mvp/views/detail.py` line-by-line:

| Requirement | Status | Notes |
|---|---|---|
| FR-001: Resolve via `model` attribute | ✅ | `if getattr(self, "model", None) is not None: return self.model` |
| FR-002: Resolve via queryset | ✅ | `get_queryset()` called; `queryset.model` extracted |
| FR-003: Resolve via `form_class` / `get_form_class()` | ✅ | Both static attribute and `get_form_class()` tried; `form._meta.model` extracted |
| FR-004: Resolve via `self.object` instance | ✅ | `self.object.__class__` used when object is non-None |
| FR-005: Priority order — model → queryset → form → object | ✅ | Strategies executed in this exact sequence |
| FR-006: `ImproperlyConfigured` with class name + options | ✅ | Error message: `f"{self.__class__.__name__} inherits from \`ModelInfoMixin\` but could not determine a model class. Set \`model\`, \`queryset\`, use a ModelForm \`form_class\` or override the \`get_model_class()\` method."` — names the class and lists all options |
| FR-007: Single override point `get_model_class()` | ✅ | Public method; subclasses can override without touching `model_meta` or `get_context_data` |
| FR-008: `model_info` context key, four fields, no model class | ✅ | `get_context_data` injects `model_info`; `get_model_info()` returns `verbose_name`, `verbose_name_plural`, `app_label`, `model_name` only |
| FR-009: Exception silencing for queryset/form strategies | ✅ | Both `get_queryset()` and `get_form_class()` calls are wrapped in `try/except Exception` |
| FR-010: `None`-valued `object` skipped | ✅ | `getattr(self, "object", None) is not None` guards the object strategy |
| FR-011: All downstream consumers use `get_model_class()` | ✅ | `CRUDDirectoryMixin` and `PageObjectMixin` both inherit `ModelInfoMixin`; all model-derived values flow through `model_meta` → `get_model_class()` |

**Decision**: The current implementation satisfies FR-001 through FR-011. No logic changes are required.

**Alternatives considered**: None — the current code is already correct.

---

## Research Question 2: What does the module move (FR-013) require?

**Task**: Determine the concrete file edits needed to move `ModelInfoMixin` from `mvp.views.detail` to `mvp.views.base` without breaking existing consumers.

**Findings**:

Current callers of `ModelInfoMixin` (confirmed by codebase search):

1. `mvp/views/detail.py` — defines it; also uses it as the base for `CRUDDirectoryMixin` and `PageObjectMixin`
2. `mvp/views/__init__.py` — imports it from `.detail`
3. `mvp/views/edit.py` — imports `PageObjectMixin` from `.detail` (inherits `ModelInfoMixin` transitively; does not reference the name directly)
4. `mvp/views/list.py` — imports `CRUDDirectoryMixin` from `.detail` (transitively; does not reference the name directly)

Required edits:

- **`mvp/views/base.py`**: Add `ModelInfoMixin` class definition (move from `detail.py`). Place after `PageMixin` and before any class that depends on it.
- **`mvp/views/detail.py`**: Remove the `ModelInfoMixin` class body. Add `from .base import ModelInfoMixin` at the top so that existing `from mvp.views.detail import ModelInfoMixin` calls continue to work without modification — backward compatible re-export.
- **`mvp/views/__init__.py`**: Change `from .detail import CRUDDirectoryMixin, ModelInfoMixin, MVPDetailView, PageObjectMixin` to import `ModelInfoMixin` from `.base` instead (or keep it via the re-export from `.detail` — either approach works; importing from canonical source is cleaner).

**Decision**: Move class body to `mvp/views/base.py`. Add re-export in `mvp/views/detail.py` for backward compatibility. Update `mvp/views/__init__.py` to import `ModelInfoMixin` from `.base` as the canonical source.

**Alternatives considered**:

- Skip the backward-compatible re-export — rejected; any downstream project importing `from mvp.views.detail import ModelInfoMixin` directly would break silently.
- Move to a new `mvp/views/mixins.py` — rejected; spec clarification session chose `mvp.views.base` explicitly.

---

## Research Question 3: What test coverage is needed?

**Task**: Inventory what test coverage exists for `ModelInfoMixin` and define the full test scope needed.

**Findings**:

No tests for `ModelInfoMixin` exist anywhere in the test suite. A search across `tests/` found zero references to the class name.

The constitution (Principle I) requires tests for all new or changed Python behavior. Since this is a move (plus adding coverage for previously untested logic), full coverage must be written.

Test cases needed, organized by spec acceptance criteria:

**Resolution strategies (FR-001 – FR-005, US1):**

- `test_resolves_from_model_attribute` — view with only `model` set
- `test_resolves_from_queryset` — view with only `queryset` set, no `model`
- `test_resolves_from_form_class` — view with only a ModelForm `form_class`, no `model` or `queryset`
- `test_resolves_from_object_instance` — view with `object` set at runtime, no static config
- `test_model_priority_over_queryset` — view with both `model` and `queryset` set to different models; `model` wins
- `test_queryset_priority_over_form_class` — view with `queryset` (with model) and `form_class`; queryset wins
- `test_form_class_priority_over_object` — view with form_class and object; form_class wins

**Exception silencing (FR-009):**

- `test_get_queryset_exception_falls_through_to_next_strategy` — `get_queryset()` raises; resolution continues to form_class strategy
- `test_get_form_class_exception_falls_through_to_next_strategy` — `get_form_class()` raises; resolution continues to object strategy

**Edge cases (spec edge cases section):**

- `test_plain_form_class_is_skipped` — form_class is a plain `Form` (not ModelForm); skipped, resolution continues
- `test_none_object_is_skipped` — `self.object = None`; skipped, resolution continues
- `test_proxy_model_returned_not_concrete_parent` — view configured with proxy model; proxy class returned

**Error message (FR-006, US3):**

- `test_raises_improperly_configured_with_no_config` — no model config at all; `ImproperlyConfigured` raised
- `test_error_message_contains_view_class_name` — error message includes `self.__class__.__name__`

**Custom override (FR-007, US2):**

- `test_custom_get_model_class_override` — subclass overrides `get_model_class()` to return a model not reachable via standard strategies; that model is used
- `test_custom_override_exception_propagates` — subclass override raises; exception propagates without being swallowed

**Context shape (FR-008, US4):**

- `test_model_info_context_key_present` — `model_info` key exists in `get_context_data()` result
- `test_model_info_contains_expected_fields` — all four fields present: `verbose_name`, `verbose_name_plural`, `app_label`, `model_name`
- `test_model_info_does_not_contain_model_class` — `model_info` dict does not contain the model class or any non-string value
- `test_custom_verbose_name_in_model_info` — model with `verbose_name = "custom name"` → appears in `model_info`

**Decision**: All cases above must be covered in a `TestModelInfoMixin` class in `tests/test_views/test_base.py`.

**Alternatives considered**: Separate `test_detail.py` file — rejected; constitution mandates test structure mirrors source tree. Since `ModelInfoMixin` moves to `mvp/views/base.py`, its tests belong in `tests/test_views/test_base.py`.

---

## Summary of Gaps

| Gap | Requirement | Work Required |
|---|---|---|
| `ModelInfoMixin` lives in `mvp.views.detail` | FR-013 | Move to `mvp.views.base`; add backward-compat re-export |
| Zero test coverage | Constitution I | Add `TestModelInfoMixin` in `tests/test_views/test_base.py` (~20 test cases) |
| `skills/django-mvp/SKILL.md` canonical path reference | Principle X | Update any reference to `ModelInfoMixin` import path |

No logic changes to the mixin itself are required. The existing implementation is correct and complete.
