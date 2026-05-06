# Research: MVPListView — Item Templates and Composed List Page

**Feature**: `015-mvp-list-view` | **Date**: 2026-05-06 | **Phase**: 0

## Decision Log

### R1: Are any upstream dependencies still partially implemented?

**Decision**: Yes — `MVPListViewMixin.get_page_title()` is a stub (`pass`), and
`directory` is not set on `MVPListViewMixin` (inherits `[]` from `CRUDDirectoryMixin`).
`MVPListView` lacks `paginate_by`. Everything else (`SearchOrderMixin`, `CRUDDirectoryMixin`,
`PageMixin`, `get_list_item_template()`, `get_context_data()`) is already implemented and
tested.

**Rationale**: Reading `mvp/views/list.py` directly. These are the only three code gaps.

**Alternatives considered**: None — this is a factual audit.

---

### R2: What does `get_list_item_template()` currently do?

**Decision**: Already complete. Returns `self.list_item_template` if set; otherwise derives
`"{app_label}/{model_name}_list_item.html"` from `self.model._meta`. Raises `AttributeError`
with an informative message when `model` is not set and `list_item_template` is falsy.

**Rationale**: Reading `mvp/views/list.py` lines 303–330. Matches FR-001, FR-002, FR-003,
FR-004, FR-014, FR-015 exactly. No changes needed.

**Alternatives considered**: None — implementation already satisfies spec.

---

### R3: How should `get_page_title()` access the model's verbose name plural?

**Decision**: `self.model._meta.verbose_name_plural.title()`. This is the same pattern used
elsewhere in the codebase (e.g., `PageObjectMixin.get_list_title()`). The `model_meta`
cached property (from `ModelInfoMixin`) is also available but is not needed here since
`MVPListViewMixin` already has `model` via `ListView`.

**Rationale**: Consistent with existing codebase; `_meta` is the canonical Django API for
model metadata.

**Alternatives considered**: Using `self.model_meta.verbose_name_plural` — equivalent but
adds an indirect hop through `ModelInfoMixin.model_meta` when `self.model` is directly
available from `ListView`.

---

### R4: Does `get_list_item_template()` handling of empty string match FR-002?

**Decision**: Yes. The current implementation uses `if self.list_item_template:` (truthiness
check), so an empty string `""` falls through to auto-discovery. This satisfies the edge
case in the spec.

**Rationale**: Python truthiness: `bool("") == False`.

---

### R5: Is `paginate_by = 24` safe as a class-level default on `MVPListView`?

**Decision**: Yes. Django's `ListView` honours any value of `paginate_by`; `None` means no
pagination. Setting `24` on `MVPListView` does not affect `MVPListViewMixin` itself (which
sets no default), so developers using `MVPListViewMixin` directly with a different base
class retain full control.

**Rationale**: Standard Django ListView design; no special handling required.

---

### R6: Are there E2E tests needed for this feature?

**Decision**: No new E2E test file is required. This feature changes only Python view
behaviour (context injection, `get_page_title()`, `directory` scoping, `paginate_by`).
The rendered HTML output of `list_view.html` is unchanged. Existing `test_list_view.py`
unit tests cover all acceptance criteria. If a future spec adds UI elements that exercise
these new context keys, E2E tests should be added then.

**Rationale**: Constitution Principle VIII: E2E tests required when user-visible behaviour
changes. No template HTML changes in this PR.

---

## All NEEDS CLARIFICATION Resolved

None present. All dependencies confirmed implemented. Implementation can proceed directly
to Phase 1.
