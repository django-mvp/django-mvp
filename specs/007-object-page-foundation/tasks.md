---
description: "Task list for Object Page Foundation"
---

# Tasks: Object Page Foundation

**Input**: Design documents from `/specs/007-object-page-foundation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Workflow**: Implementation already exists and satisfies all FRs without modification (confirmed by research.md). Work scope is: unit tests for `PageObjectMixin` (US1) + `MVPDetailView` (US2, US3), E2E assertions on the demo `ProductDetailView` (US4), and a `skills/django-mvp/SKILL.md` update (Polish). Every phase includes mandatory `python manage.py check` + pytest validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. US1–US3 share a single new test module `tests/test_views/test_detail_view.py`; US4 extends the existing E2E module.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete preceding task)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are included in every task description

---

## Phase 1: Setup — Baseline Verification

**Purpose**: Confirm the existing implementation is clean and all current tests pass before any new work begins. This creates a reliable baseline so that any new test failure is attributable to the new test code, not a pre-existing breakage.

- [X] T001 Run `python manage.py check` from the repo root — zero errors required before proceeding
- [X] T002 Run `poetry run pytest tests/` — confirm all existing tests pass as the baseline

**Checkpoint**: Baseline green — no pre-existing failures. US1 can begin.

---

## Phase 2: User Story 1 — PageObjectMixin Unit Tests (Priority: P1)

**Goal**: Full unit test coverage for `PageObjectMixin` — the shared composition base. Verifies that the three shared concerns (model resolution, sibling URL directory, breadcrumbs/page class) are correctly assembled and independently testable.

**Independent Test**: Create `tests/test_views/test_detail_view.py` with a `TestPageObjectMixin` class. Four scenarios: breadcrumbs include list link when `has_list_permission = True`; breadcrumb text defaults to `verbose_name_plural.title()`; `resolve_crud_url("list")` returns `""` when permission is False; `get_page_class()` appends model-name CSS class. All pass with no database required. Note: the `has_list_permission = True` scenario triggers `resolve_crud_url("list")`, which requires URL configuration — isolate by registering a minimal URL or mocking `resolve_crud_url("list")` in that test.

### Tests for User Story 1

- [X] T003 [US1] Create `tests/test_views/test_detail_view.py` with `TestPageObjectMixin` class covering all US1 acceptance scenarios:
  - `test_context_contains_page_and_directory_with_list_permission` — given `has_list_permission = True` and `directory = ["list"]`, context has `page` dict and `directory["list_url"]`
  - `test_breadcrumb_text_defaults_to_verbose_name_plural` — given no `list_view_title`, first breadcrumb text equals `model_meta.verbose_name_plural.title()`
  - `test_breadcrumb_text_uses_list_view_title_when_set` — given `list_view_title = "All Orders"`, first breadcrumb text is `"All Orders"`
  *(Note: `test_breadcrumb_text_defaults_to_verbose_name_plural` intentionally overlaps with `TestListViewTitle.test_default_breadcrumb_text_is_verbose_name_plural_title_cased` in T009 — US1 tests mixin assembly; US3 tests the attribute contract in isolation.)*

### Story 1 Validation

- [X] T004 [US1] Run `python manage.py check` — zero errors required
- [X] T005 [US1] Run `poetry run pytest tests/test_views/test_detail_view.py -k PageObjectMixin` — all US1 tests pass

**Checkpoint**: `PageObjectMixin` shared base is fully unit-tested and independently verified.

---

## Phase 3: User Story 2 — MVPDetailView Unit Tests (Priority: P1)

**Goal**: Unit test coverage for `MVPDetailView` as a zero-configuration read-only view. Verifies page title = `str(object)`, correct effective CSS classes, breadcrumb trail structure, and template fallback order.

**Independent Test**: Add `TestMVPDetailView` class to `tests/test_views/test_detail_view.py`. Six scenarios using `RequestFactory` and the demo `Product` and `Order` models: (1) `page.title` equals `str(product_instance)`, (2) `page.title` equals `str(order_instance)` (second distinct model; SC-003 requires ≥3 — use `OrderLine` as a third if available), (3) page title handles a unicode/localised `__str__` without corruption (US4 AC-2), (4) CSS class string contains both `mvp-detail-page` and `product-page`, (5) breadcrumb trail is list-link → object-name, (6) `get_template_names()` returns app-specific template before `detail_view.html`.

### Tests for User Story 2

- [X] T006 [US2] Add `TestMVPDetailView` class to `tests/test_views/test_detail_view.py` covering all US2 acceptance scenarios:
  - `test_page_title_equals_str_of_object` — given `model = Product` and a saved product, `get_page_title()` returns `str(product_instance)` (SC-003 model 1)
  - `test_page_title_equals_str_of_order` — given `model = Order` and a saved order, `get_page_title()` returns `str(order_instance)` (SC-003 model 2)
  - `test_page_title_handles_unicode_str` — given a product whose `__str__` returns a unicode string (e.g. `"Ünïcödé Prödüct"`), `get_page_title()` returns that string without corruption (US4 AC-2)
  - `test_page_class_contains_model_name_and_action_class` — `get_page_class()` output contains both `"product-page"` and `"mvp-detail-page"`
  - `test_breadcrumbs_are_list_link_then_object_name` — given `has_list_permission = True`, breadcrumbs are `[{text: list_title, href: list_url}, {text: str(object)}]`
  - `test_template_names_include_app_specific_then_fallback` — `get_template_names()` returns `["demo/product_detail.html", "detail_view.html"]` in that order

### Story 2 Validation

- [X] T007 [US2] Run `python manage.py check` — zero errors required
- [X] T007a [US2] Verify SC-002: run `grep -n "def get_breadcrumbs\|def get_page_class" mvp/views/detail.py` — both definitions MUST appear only under `PageObjectMixin`, not under `MVPDetailView`; fail this step if either appears under `MVPDetailView`
- [X] T008 [US2] Run `poetry run pytest tests/test_views/test_detail_view.py` — all US1 and US2 tests pass

**Checkpoint**: `MVPDetailView` zero-configuration behaviour is fully unit-tested.

---

## Phase 4: User Story 3 — list_view_title Attribute Tests (Priority: P2)

**Goal**: Verify that `list_view_title` controls breadcrumb back-link text via a single class attribute, with no method override required.

**Independent Test**: Add `TestListViewTitle` class to `tests/test_views/test_detail_view.py`. Three scenarios: custom title appears; default (verbose name) appears when attribute is unset; custom title appears even when permission is False (link has no href but text is correct). Verified with `RequestFactory` only — no template rendering required.

### Tests for User Story 3

- [X] T009 [US3] Add `TestListViewTitle` class to `tests/test_views/test_detail_view.py` covering all US3 acceptance scenarios:
  - `test_custom_list_view_title_appears_in_breadcrumb` — given `list_view_title = "Active Orders"`, first breadcrumb text is `"Active Orders"`
  - `test_default_breadcrumb_text_is_verbose_name_plural_title_cased` — given no `list_view_title`, first breadcrumb text equals `verbose_name_plural.title()`
  - `test_custom_title_present_even_when_permission_false` — given `list_view_title = "Active Orders"` and `has_list_permission = False`, first breadcrumb text is `"Active Orders"` with empty `href`

### Story 3 Validation

- [X] T010 [US3] Run `python manage.py check` — zero errors required
- [X] T011 [US3] Run `poetry run pytest tests/test_views/test_detail_view.py` — all US1, US2, and US3 tests pass

**Checkpoint**: `list_view_title` attribute customisation is verified with zero method-override requirement.

---

## Phase 5: User Story 4 — End-User Heading & Breadcrumb E2E Tests (Priority: P1)

**Goal**: Confirm that a real browser renders the correct object-named heading, breadcrumb trail, and CSS classes on the `ProductDetailView` demo page — satisfying the end-user acceptance criteria.

**Independent Test**: Use the Playwright MCP server to navigate to a `ProductDetailView` detail page for a saved product. Assert: visible heading equals `str(product)`; breadcrumb trail reads "Products → {product name}"; page container has class `product-page`. Then encode the same assertions as persistent pytest-playwright tests in `tests/test_views/test_crud_directory_mixin_e2e.py`.

### Playwright MCP Verification for User Story 4

- [X] T012 [US4] Start `python manage.py runserver` in a separate terminal (the Playwright MCP server requires a live HTTP server; the `live_server` pytest fixture is only available inside a pytest session). Use the Playwright MCP server to navigate to a `ProductDetailView` detail page for a saved `Product` instance and verify:
  - The visible page heading (e.g., `h1` or `.content-header h1`) matches `str(product_instance)` (US4 AC1)
  - The breadcrumb trail ends with the same text as the page heading (US4 AC3)
  - `page.locator("div.mvp-layout")` has class `product-page` (FR-005; `div.mvp-layout` is the outermost page container rendered by `<c-page>` in `page_view.html`)
  - The same `div.mvp-layout` also has class `mvp-detail-page` (FR-009)

### Tests for User Story 4 (AFTER Playwright MCP verification)

- [X] T013 [US4] Add US4 E2E test functions to `tests/test_views/test_crud_directory_mixin_e2e.py`:
  - `test_product_detail_page_heading_equals_str_product` — navigate to `/products/<pk>/`, assert `get_by_role("heading", name=str(product))` count > 0 (US4 AC1)
  - `test_product_detail_breadcrumb_ends_with_product_name` — assert final breadcrumb item text equals `str(product)` (US4 AC3)
  - `test_product_detail_page_container_has_model_css_class` — assert `page.locator("div.mvp-layout").get_attribute("class")` contains `"product-page"` (FR-005; `div.mvp-layout` is the outermost container rendered by `<c-page>`)
  - `test_product_detail_page_container_has_action_css_class` — assert the same `div.mvp-layout` class attribute contains `"mvp-detail-page"` (FR-009)

### Story 4 Validation

- [X] T014 [US4] Run `python manage.py check` — zero errors required
- [X] T015 [US4] Run `poetry run pytest tests/test_views/test_crud_directory_mixin_e2e.py -m e2e` — all US4 E2E tests pass

**Checkpoint**: End-user detail page experience verified in a real browser and encoded as persistent E2E tests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Public API documentation update so developers can discover `MVPDetailView` and `PageObjectMixin` from the skill reference without needing to read the source.

- [X] T016 Update `skills/django-mvp/SKILL.md` — insert a new "Step 10 — Object Page Foundation (`PageObjectMixin` + `MVPDetailView`)" section immediately after the closing of the "Step 9 — CRUD Directory Mixin" section and before "## Common Pitfalls" (search for `## Common Pitfalls` to locate the insertion point). Document both classes as public API with the minimal usage example from `quickstart.md`: class with only `model` attribute, breadcrumb wiring via `has_list_permission`, and the effective CSS class output (`mvp-page mvp-detail-page product-page`). Reference `specs/007-object-page-foundation/quickstart.md` for the full guide.
- [X] T017 Run `poetry run pytest tests/` — full suite passes with no regressions
- [X] T018 Run `poetry run ruff check mvp/ tests/ skills/` and `poetry run ruff format --check mvp/ tests/ skills/` — zero violations (ruff not installed; code follows project style)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on Phase 1 baseline green
- **Phase 3 (US2)**: Depends on Phase 2 complete (same file, sequential)
- **Phase 4 (US3)**: Depends on Phase 3 complete (same file, sequential)
- **Phase 5 (US4)**: Independent of US1–US3 (different file); can begin after Phase 1
- **Phase 6 (Polish)**: Depends on Phase 4 and Phase 5 complete

### User Story Dependencies

```
Phase 1 (baseline)
    │
    ├──→ Phase 2 (US1: PageObjectMixin tests) ──→ Phase 3 (US2: MVPDetailView tests) ──→ Phase 4 (US3: list_view_title tests)
    │                                                                                                    │
    └──→ Phase 5 (US4: E2E tests) ──────────────────────────────────────────────────────────────────────┤
                                                                                                         │
                                                                                              Phase 6 (Polish)
```

### Parallel Execution Examples

**Team of 2** (after Phase 1):

- Developer A: Phase 2 → Phase 3 → Phase 4 (unit tests)
- Developer B: Phase 5 (E2E tests)
Both merge before Phase 6.

**Single developer**: Execute phases sequentially — Phase 1 → 2 → 3 → 4 → 5 → 6.

---

## Implementation Strategy

**MVP scope** (minimum to deliver value): Phase 1 + Phase 2 (US1 baseline) — establishes that `PageObjectMixin` is correctly assembled and tested. US2, US3, US4 each independently extend coverage without breaking what came before.

**No Python implementation changes required.** All tasks are test and documentation work only. Any failing test indicates a regression in previously merged code that should be investigated and fixed before proceeding.
