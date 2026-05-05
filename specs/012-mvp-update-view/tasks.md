# Tasks: MVPUpdateView — Zero-Config Model Update View

**Input**: Design documents from `specs/012-mvp-update-view/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Branch**: `012-mvp-update-view`
**Implementation scope**: 4 targeted changes across 2 files; tests appended to 2 existing test files.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or classes, no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US6)
- All file paths are relative to the repository root

---

## Phase 1: Setup

**Purpose**: Confirm the baseline is clean before any changes.

- [ ] T001 Run `pytest tests/test_views/` and confirm zero failures on branch `012-mvp-update-view` before any code changes

**Checkpoint**: Green baseline confirmed — implementation can begin.

---

## Phase 2: Foundational

**Purpose**: No new infrastructure is needed for this feature — all shared infrastructure (CRUD directory, base classes, test fixtures, template components) is pre-existing.

> ⚠️ Phase 2 has no tasks. Proceed directly to Phase 3.

---

## Phase 3: User Story 1 — Zero-Config Update Page (Priority: P1) 🎯 MVP

**Goal**: A minimal `MVPUpdateView` subclass (only `model` + `fields`) produces a model-aware page title and a correct three-level breadcrumb with no additional configuration.

**Independent Test**: Create `class ProductUpdateView(MVPUpdateView): model = Product; fields = ["name"]`. Navigate to the update URL for an existing `Product`. Verify title is "Update Product", breadcrumb has three items with the middle item linking via `resolve_crud_url("detail")`, and page icon and CSS classes are correct.

### Tests for User Story 1 ⚠️ Write FIRST — ensure they FAIL before implementation

- [ ] T002 [US1] Write failing unit tests `TestMVPUpdateViewDefaults` (`test_page_icon_is_edit`, `test_page_class_contains_update`, `test_page_title_class_attr_is_template`) in `tests/test_views/test_edit_view.py` — mirror structure of `TestMVPCreateViewDefaults`
- [ ] T003 [P] [US1] Write failing unit tests `TestMVPUpdateViewPageTitle` (`test_default_title_single_word_verbose_name` → "Update Product", `test_default_title_multi_word_verbose_name` → "Update Order Line", `test_explicit_page_title_returned`, `test_empty_string_page_title_returns_empty`) in `tests/test_views/test_edit_view.py` — mirror structure of `TestMVPCreateViewPageTitle`; use `make_update_view()`
- [ ] T004 [P] [US1] Write failing unit tests `TestMVPUpdateViewBreadcrumb` (`test_breadcrumb_has_three_items`, `test_second_item_text_is_str_object`, `test_second_item_href_uses_resolve_crud_url_detail`, `test_third_item_has_no_href`, `test_third_item_text_matches_page_title`) in `tests/test_views/test_edit_view.py`; confirm T004 `test_second_item_href_uses_resolve_crud_url_detail` FAILs (current code calls `self.object.get_absolute_url()`)

### Implementation for User Story 1

- [ ] T005 [US1] Change `page_title = _("Update Entry")` to `page_title = _("Update %(verbose_name)s")` in `MVPUpdateView` class in `mvp/views/edit.py`; run T002 and T003 tests — all must now pass
- [ ] T006 [US1] Change `get_breadcrumbs()` to use `self.resolve_crud_url("detail")` instead of `self.object.get_absolute_url()` for the middle breadcrumb item in `mvp/views/edit.py`; run T004 tests — all must now pass

**Checkpoint**: US1 is fully functional. `pytest tests/test_views/test_edit_view.py -k TestMVPUpdateView` is green.

---

## Phase 4: User Story 6 — Contextual Update Page Title and Confirmation (Priority: P1)

**Goal**: An end user visiting an update page built on `MVPUpdateView` sees a model-named heading ("Update Product") and a grammatically correct flash on save ("Product successfully updated.").

**Independent Test**: Using `live_server`, navigate to `/demo/products/<pk>/update/`. Verify the `<h1>` or page-title element contains "Update Product". Submit valid form data; verify the flash message text on the next page.

### Tests for User Story 6

- [ ] T007 [P] [US6] Write E2E test `test_US6_update_page_title_is_model_aware` in `tests/test_views/test_edit_view_e2e.py`; use `product` fixture; verify page title element contains "Update Product"
- [ ] T008 [P] [US6] Write E2E test `test_US6_update_success_message_is_title_cased` in `tests/test_views/test_edit_view_e2e.py`; submit valid product update form; verify flash contains "Product successfully updated."
- [ ] T009 [P] [US6] Write E2E test `test_US6_update_breadcrumb_has_three_items` in `tests/test_views/test_edit_view_e2e.py`; verify breadcrumb container contains exactly three items with correct text and link presence

**Checkpoint**: US6 E2E tests pass. US1 + US6 complete — the P1 MVP is deliverable.

---

## Phase 5: User Story 2 — Customised Title and Message (Priority: P2)

**Goal**: A developer can override `page_title`, `success_message`, `page_icon`, and `page_class` with a single class attribute and the view uses the explicit value instead of the default.

**Independent Test**: Set `page_title = "Edit product details"` and `success_message = "%(name)s was saved."` on the view class. Verify `get_page_title()` returns "Edit product details" and `get_success_message({"name": "Widget"})` returns "Widget was saved."

### Tests for User Story 2

- [ ] T010 [US2] Write unit tests `TestMVPUpdateViewOverrides` (`test_page_icon_overridable`, `test_page_class_overridable`, `test_page_title_overridable`, `test_success_message_overridable_with_field_interpolation`) in `tests/test_views/test_edit_view.py`; use `make_update_view(extra_attrs=...)` for each; all tests should pass with existing code (no new implementation needed)

**Checkpoint**: US2 passes — customisation works without code changes (tested against already-correct infrastructure from Phase 3).

---

## Phase 6: User Story 3 — Delete Link Within the Edit Page (Priority: P2)

**Goal**: When a delete view is registered, the update page shows a Delete button with `?back=<update_url>&next=<list_url>` query parameters.

**Independent Test**: Register `MVPDeleteView` for the same model. Load the update page and verify the Delete button is visible and its `href` contains `?back=` and `?next=`.

### Tests for User Story 3

- [ ] T011 [US3] Confirm `TestMVPUpdateViewDeleteUrl` (3 existing tests) in `tests/test_views/test_delete_view.py` already covers `?back` and `?next` params on `get_delete_url()` — no new unit tests needed (see research finding 5)
- [ ] T012 [US3] Write E2E test `test_US3_update_delete_link_visible_when_configured` in `tests/test_views/test_edit_view_e2e.py`; use `product` fixture; verify Delete button is visible and `href` contains both `?back=` and `?next=` substrings

**Checkpoint**: US3 verified end-to-end.

---

## Phase 7: User Story 4 — Delete Link Hidden When Not Configured (Priority: P3)

**Goal**: When no delete view is registered (or `has_delete_permission` is falsy), the update page renders with no Delete button — no broken link, no 404, no error.

**Independent Test**: Configure `MVPUpdateView` with `has_delete_permission = False` (or omit `MVPDeleteView` from the CRUD directory). Load the update page and verify no delete control is visible anywhere on the page.

### Tests for User Story 4 ⚠️ Write FIRST — ensure they FAIL before implementation

- [ ] T013 [US4] Write failing unit test `TestMVPUpdateViewDeleteLinkVisibility.test_delete_button_absent_when_delete_url_empty` in `tests/test_views/test_edit_view.py`; create a `make_update_view(extra_attrs={"has_delete_permission": False})` instance; verify `get_context_data()["delete_url"]` is falsy (this should already pass); additionally render the template snippet and verify the delete button element is absent — this test FAILS with current `{% if object %}` guard
- [ ] T014 [P] [US4] Write E2E test `test_US4_update_delete_link_absent_when_not_configured` in `tests/test_views/test_edit_view_e2e.py`; navigate to a product update URL where no delete view is configured (use the `demo` app's category update route which has no delete view); verify no delete button is rendered

### Implementation for User Story 4

- [ ] T015 [US4] Change `{% if object %}` to `{% if delete_url %}` on the Delete button guard in `mvp/templates/form_view.html`; run T013 and T014 — all must now pass

**Checkpoint**: US4 complete — `pytest tests/test_views/test_edit_view.py -k TestMVPUpdateViewDeleteLink` is green; E2E test T014 passes.

---

## Phase 8: User Story 5 — Breadcrumb Degrades When Detail or List Is Missing (Priority: P3)

**Goal**: When no detail URL or no list URL is registered (or permissions are falsy), the affected breadcrumb item renders as plain text with no `href` — no `AttributeError`, no broken link.

**Independent Test**: Configure `MVPUpdateView` with `has_detail_permission = False`. Verify the second breadcrumb item has no `href`. Separately configure with `has_list_permission = False` and verify the first breadcrumb item has no `href`.

### Tests for User Story 5

- [ ] T016 [P] [US5] Write unit tests extending `TestMVPUpdateViewBreadcrumb` (from T004) with: `test_first_item_has_no_href_when_list_permission_false` and `test_first_item_has_href_when_list_permission_true` in `tests/test_views/test_edit_view.py`; use `make_update_view(extra_attrs={"has_list_permission": False/True})` — these should pass after T006 (no new implementation needed)
- [ ] T017 [P] [US5] Write unit tests `test_second_item_has_no_href_when_detail_permission_false` and `test_second_item_has_href_when_detail_permission_true` in `tests/test_views/test_edit_view.py`; use `make_update_view(extra_attrs={"has_detail_permission": False/True})` — these should pass after T006 (the change to `resolve_crud_url("detail")` already handles this)

**Checkpoint**: US5 complete — all `TestMVPUpdateViewBreadcrumb` tests green.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Principle XII docstring compliance, skill currency, and final validation.

- [ ] T018 Replace the single-line `MVPUpdateView` class docstring with a Principle XII-compliant docstring in `mvp/views/edit.py`: (a) 1–2 sentence intended-use summary; (b) `Config:` block listing `page_title`, `page_icon`, `page_class`, `success_message`, `success_url`, `fields`, `model` with types, defaults, and one-line descriptions; (c) `Override hooks:` subsection listing `get_breadcrumbs()`, `get_delete_url()`, `get_page_title()` (inherited), `get_success_message()` (inherited), `get_success_url()` (inherited); (d) minimal usage example (match the pattern in `quickstart.md`)
- [ ] T019 [P] Update `MVPUpdateView` entry in `skills/django-mvp/SKILL.md`: document model-aware default title (`_("Update %(verbose_name)s")`), three-level breadcrumb depth, `resolve_crud_url("detail")` middle link, and delete-button visibility gate (`{% if delete_url %}`)
- [ ] T020 Run `python manage.py check` and confirm zero errors or warnings with a minimal `MVPUpdateView` subclass registered in `INSTALLED_APPS`
- [ ] T021 Run quickstart.md validation: create `class ProductUpdateView(MVPUpdateView): model = Product; fields = ["name", "slug"]` wired to `product-update` URL; navigate to `/demo/products/<pk>/update/`; verify page renders with correct title, breadcrumb, and icon (Playwright MCP)
- [ ] T022 Run full test suite `pytest tests/test_views/` and confirm zero regressions across all `MVPCreateView`, `MVPDeleteView`, `MVPFormView`, and `MVPUpdateView` tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: N/A — no foundational tasks
- **Phase 3 (US1)**: Depends on Phase 1. Blocks Phase 4 (US6), Phase 5 (US2), Phase 8 (US5) because implementation changes in T005/T006 are prerequisites
- **Phase 4 (US6)**: Depends on Phase 3 implementation (T005, T006)
- **Phase 5 (US2)**: Depends on Phase 3 implementation (T005) for title tests
- **Phase 6 (US3)**: Can start after Phase 3 — delete URL logic pre-exists; E2E test independent
- **Phase 7 (US4)**: Depends on Phase 6 (US3) completion; T015 template fix serves both
- **Phase 8 (US5)**: Depends on Phase 3 T006 (get_breadcrumbs fix) being complete
- **Polish (Final Phase)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Independent — blocks US6, US2, US5
- **US6 (P1)**: Depends on US1 implementation (same code change)
- **US2 (P2)**: Depends on US1 `page_title` change (T005)
- **US3 (P2)**: Independent of other stories — delete URL logic pre-exists
- **US4 (P3)**: Depends on US3 (shares template fix); T015 enables both stories
- **US5 (P3)**: Depends on US1 T006 (`get_breadcrumbs` fix)

### Within Each Phase

- Failing tests MUST be written and observed to FAIL before implementation
- T005 (page_title) before T006 (get_breadcrumbs) — both in same file; do sequentially
- T015 (template fix) after T013 (failing test observed)

### Parallel Opportunities

- T003 and T004 (test writing for US1) can run in parallel — different test classes
- T007, T008, T009 (US6 E2E tests) can be written in parallel — different test functions
- T016 and T017 (US5 breadcrumb tests) can run in parallel — different test methods
- T018 (docstring) and T019 (skill update) can run in parallel — different files

---

## Parallel Example: User Story 1

```bash
# After T005 and T006 (implementation complete):
pytest tests/test_views/test_edit_view.py -k "TestMVPUpdateViewDefaults or TestMVPUpdateViewPageTitle or TestMVPUpdateViewBreadcrumb" -v
# Expect: All green
```

---

## Implementation Strategy

**MVP scope**: Phase 3 + Phase 4 (US1 + US6, both P1) — delivers the core value in the fewest changes.

**Full scope order**: Phase 3 → 4 → 7 → 5 → 6 → 8 → Polish

- The template fix (Phase 7, T015) is a one-line change that unblocks US4 and makes US3 correctness verifiable end-to-end.
- US2 (Phase 5) and US5 (Phase 8) have no additional implementation — tests only.
- Total implementation lines changed: ~4 Python + 1 HTML.

---

## Task Count Summary

| Phase | Story | Tasks | Parallel |
|-------|-------|-------|---------|
| Phase 1 (Setup) | — | 1 | 0 |
| Phase 3 | US1 [P1] | 5 | 2 |
| Phase 4 | US6 [P1] | 3 | 3 |
| Phase 5 | US2 [P2] | 1 | 0 |
| Phase 6 | US3 [P2] | 2 | 0 |
| Phase 7 | US4 [P3] | 3 | 1 |
| Phase 8 | US5 [P3] | 2 | 2 |
| Polish | — | 5 | 1 |
| **Total** | | **22** | **9** |
