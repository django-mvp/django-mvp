# Tasks: MVPListView — Item Templates and Composed List Page

**Input**: Design documents from `specs/015-mvp-list-view/`
**Prerequisites**: [plan.md](plan.md) ✅ · [spec.md](spec.md) ✅ · [research.md](research.md) ✅ · [data-model.md](data-model.md) ✅ · [contracts/view-api.md](contracts/view-api.md) ✅ · [quickstart.md](quickstart.md) ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label — only on user story phase tasks
- All tasks include exact file paths

---

## Phase 1: Setup

**Purpose**: Verify the environment and confirm existing implementation before making changes.

- [X] T001 Run `python manage.py check` to confirm no pre-existing errors in `c:\Users\samue\Documents\coding\django-mvp`
- [X] T002 Run `poetry run pytest tests/test_views/test_list_view.py -v` to confirm existing search/ordering tests pass as a baseline

**Checkpoint**: Green baseline confirmed — all pre-existing tests pass, no system errors.

---

## Phase 2: Foundational — Core MVPListViewMixin Fixes

**Purpose**: Close the three open stubs in `mvp/views/list.py`. These are the prerequisite changes that all user story tests will assert against.

**⚠️ CRITICAL**: All three code changes are in the same file. Complete them together before writing any tests.

- [X] T003 Implement `MVPListViewMixin.get_page_title()` in `mvp/views/list.py` — return `self.page_title` when truthy, fall back to `self.model._meta.verbose_name_plural.title()`
- [X] T004 Set `directory = ["create"]` on `MVPListViewMixin` in `mvp/views/list.py` to limit CRUD URL injection to the create action only
- [X] T005 Add `paginate_by = 24` to `MVPListView` in `mvp/views/list.py`
- [X] T006 [P] Write Constitution-XII compliant docstring for `MVPListViewMixin` in `mvp/views/list.py` — must include `Config:` (all 8 attributes), `Override hooks:` (all 7 methods), and a minimal usage example
- [X] T007 [P] Write Constitution-XII compliant docstring for `MVPListView` in `mvp/views/list.py` — must include `Config:` (`paginate_by`), `Override hooks:` (inherited from mixin), and a minimal usage example
- [X] T007b Run `poetry run pytest tests/test_views/test_list_view.py -v` to confirm all existing search/ordering tests pass after the stub fixes in T003–T005 *(Constitution I — required pytest gate after Django code change)*
- [X] T008 Run `python manage.py check` to confirm no errors after changes in `mvp/views/list.py`
- [X] T009 Run `poetry run ruff check mvp/views/list.py` and `poetry run ruff format mvp/views/list.py` to confirm no lint/format violations *(runs after T003–T007 are complete; not parallel with T008 since format may modify files)*

**Checkpoint**: Three stubs closed, docstrings added, linting clean, system check passes.

---

## Phase 3: User Story 1 — Zero-Config List Page (Priority: P1) 🎯 MVP

**Goal**: Verify that `MVPListView` with only `model` set produces a fully functional, paginated list page with the correct title and item template in context.

**Independent Test**: Create a `MVPListView` stub with `model = Product` and no other configuration. Assert: page renders, `page.title` = `"Products"` (or model's verbose name plural in title case), `list_item_template` = `"demo/product_list_item.html"`, `paginate_by` = `24`.

- [X] T010 [US1] Add `_make_list_view()` helper to `tests/test_views/test_list_view.py` — produces a `MVPListViewMixin + ListView` stub with `request`, `kwargs`, `args`, and `object_list` set, skipping template rendering
- [X] T011 [US1] Write test `test_zero_config_page_renders` in `tests/test_views/test_list_view.py` — assert view with only `model = Product` produces a valid context (no errors, no `AttributeError`)
- [X] T012 [US1] Write test `test_default_page_title_from_model` in `tests/test_views/test_list_view.py` — assert `page["title"]` equals `Product._meta.verbose_name_plural.title()` when `page_title` is not set
- [X] T013 [US1] Write test `test_default_list_item_template_convention` in `tests/test_views/test_list_view.py` — assert `list_item_template` context key equals `"demo/product_list_item.html"` for `model = Product` (app label `demo`)
- [X] T014 [US1] Write test `test_default_paginate_by` in `tests/test_views/test_list_view.py` — assert `MVPListView.paginate_by == 24`
- [X] T015 [US1] Run `poetry run pytest tests/test_views/test_list_view.py -v -k "zero_config or default_page_title or default_list_item or default_paginate"` to confirm US1 tests pass

**Checkpoint**: US1 independently verified — zero-config list page works end-to-end via unit tests.

---

## Phase 4: User Story 2 — Item Template Convention and Override (Priority: P1)

**Goal**: Verify that `list_item_template` takes precedence over auto-discovery, and that auto-discovery produces the correct path for any model/app combination. Verify that missing `model` + missing `list_item_template` raises an informative error.

**Independent Test**: (a) Stub with `model = Category` (app `demo`) → context contains `demo/category_list_item.html`. (b) Stub with `list_item_template = "shared/item.html"` → context contains `"shared/item.html"`. (c) Stub with no `model` and no `list_item_template` → `AttributeError` raised.

- [X] T016 [P] [US2] Write test `test_explicit_list_item_template_overrides_convention` in `tests/test_views/test_list_view.py` — set `list_item_template = "shared/item.html"`, assert context key equals that value
- [X] T017 [P] [US2] Write test `test_list_item_template_convention_uses_app_label_and_model_name` in `tests/test_views/test_list_view.py` — test with `model = Category` (app label `demo`) → `"demo/category_list_item.html"`
- [X] T017b [P] [US2] Write test `test_list_item_template_convention_different_app_label` in `tests/test_views/test_list_view.py` — create a stub model with `_meta.app_label = "sales"` and `_meta.model_name = "order"` using `type()`, assert convention produces `"sales/order_list_item.html"` *(SC-002: multiple app/model combinations required)*
- [X] T018 [US2] Write test `test_empty_string_list_item_template_falls_back_to_convention` in `tests/test_views/test_list_view.py` — set `list_item_template = ""`, assert convention path is used
- [X] T018b [US2] Write test `test_get_list_item_template_override_takes_full_precedence` in `tests/test_views/test_list_view.py` — subclass overrides `get_list_item_template()` to return `"custom/override.html"` while `list_item_template` is also set; assert context `list_item_template == "custom/override.html"` *(FR-014: override hook bypasses both attribute and convention)*
- [X] T019 [US2] Write test `test_missing_model_and_template_raises_error` in `tests/test_views/test_list_view.py` — assert `AttributeError` is raised when neither `model` nor `list_item_template` is set
- [X] T020 [US2] Run `poetry run pytest tests/test_views/test_list_view.py -v -k "list_item_template or missing_model"` to confirm US2 tests pass

**Checkpoint**: US2 independently verified — template convention and override both confirmed.

---

## Phase 5: User Story 3 — Empty State Messaging (Priority: P2)

**Goal**: Verify that `empty_state` context dict is always present, default translated strings are non-empty, and both heading and message can be overridden or set to `None`.

**Independent Test**: Render a list view with an empty queryset. Confirm `empty_state` is present in context with `heading` and `message` populated with defaults. Then override each individually.

- [X] T021 [P] [US3] Write test `test_empty_state_present_in_context_with_defaults` in `tests/test_views/test_list_view.py` — assert `"empty_state"` in context, `context["empty_state"]["heading"]` is non-empty string, `context["empty_state"]["message"]` is non-empty string
- [X] T022 [P] [US3] Write test `test_empty_state_heading_override` in `tests/test_views/test_list_view.py` — set `empty_state_heading = "No products found"`, assert `context["empty_state"]["heading"] == "No products found"`
- [X] T023 [US3] Write test `test_empty_state_message_none_suppresses_message` in `tests/test_views/test_list_view.py` — set `empty_state_message = None`, assert `context["empty_state"]["message"] is None`
- [X] T024 [US3] Write test `test_empty_state_heading_none_suppresses_heading` in `tests/test_views/test_list_view.py` — set `empty_state_heading = None`, assert `context["empty_state"]["heading"] is None`
- [X] T025 [US3] Run `poetry run pytest tests/test_views/test_list_view.py -v -k "empty_state"` to confirm US3 tests pass

**Checkpoint**: US3 independently verified — empty state context is always present and configurable.

---

## Phase 6: User Story 4 — "Create" Action Link from the List Page (Priority: P2)

**Goal**: Verify that `directory` on `MVPListViewMixin` is limited to `["create"]`, that `create_url` is resolved when `has_create_permission = True`, and that it is absent when `has_create_permission = False`.

**Independent Test**: Configure `has_create_permission = True` with a URL named via the project's convention. Confirm `directory.create_url` is present. Set `has_create_permission = False` and confirm `directory` is an empty dict.

- [X] T026 [P] [US4] Write test `test_directory_attribute_is_create_only` in `tests/test_views/test_list_view.py` — assert `MVPListViewMixin.directory == ["create"]`
- [X] T027 [US4] Write test `test_create_url_absent_when_permission_false` in `tests/test_views/test_list_view.py` — set `has_create_permission = False` (default), assert `context["directory"]` does not contain `"create_url"`
- [X] T028 [US4] Write test `test_no_detail_update_delete_urls_in_directory` in `tests/test_views/test_list_view.py` — with `has_create_permission = False` (avoids URL resolution), assert context directory does not contain `"detail_url"`, `"update_url"`, or `"delete_url"` keys *(L3: permission=False avoids URL-resolution failures that would make the assertion pass for the wrong reason)*
- [X] T029 [US4] Run `poetry run pytest tests/test_views/test_list_view.py -v -k "directory or create_url"` to confirm US4 tests pass

**Checkpoint**: US4 independently verified — list page correctly scopes directory to create-only.

---

## Phase 7: User Story 5 — Grid Configuration (Priority: P3)

**Goal**: Verify that `grid` attribute is passed unchanged to context as `grid_config`, and that a view with no `grid` attribute still injects `grid_config` as an empty dict.

**Independent Test**: Set `grid = {"sm": 1, "md": 2, "lg": 3}`. Assert `context["grid_config"] == {"sm": 1, "md": 2, "lg": 3}`. Then omit `grid`. Assert `context["grid_config"] == {}`.

- [X] T030 [P] [US5] Write test `test_grid_config_passthrough` in `tests/test_views/test_list_view.py` — set `grid = {"sm": 1, "md": 2, "lg": 3}`, assert `context["grid_config"] == {"sm": 1, "md": 2, "lg": 3}`
- [X] T031 [P] [US5] Write test `test_grid_config_empty_dict_when_not_configured` in `tests/test_views/test_list_view.py` — no `grid` attribute, assert `context["grid_config"] == {}`
- [X] T032 [US5] Run `poetry run pytest tests/test_views/test_list_view.py -v -k "grid_config"` to confirm US5 tests pass

**Checkpoint**: US5 independently verified — grid config is correctly passed through.

---

## Phase 8: User Story 6 — Search, Ordering, and Pagination Compose Cleanly (Priority: P2)

**Goal**: Verify that `search_query` and `current_ordering` are always in context regardless of configuration, confirming the view injects the values templates need to build parameter-preserving pagination links.

**Independent Test**: Configure a view with `search_fields` and `order_by`. Submit `?q=foo&o=name_asc`. Assert `context["search_query"] == "foo"` and `context["current_ordering"] == "name_asc"`. Also confirm both keys are present on a view with neither configured.

- [X] T033 [P] [US6] Write test `test_search_query_in_context_when_search_active` in `tests/test_views/test_list_view.py` — assert `context["search_query"] == "foo"` when `?q=foo` submitted
- [X] T034 [P] [US6] Write test `test_search_query_empty_when_not_configured` in `tests/test_views/test_list_view.py` — no `search_fields`, assert `context["search_query"] == ""`
- [X] T035 [US6] Write test `test_current_ordering_in_context_when_ordering_active` in `tests/test_views/test_list_view.py` — assert `context["current_ordering"] == "name_asc"` when `?o=name_asc` submitted with matching whitelist
- [X] T036 [US6] Write test `test_mvp_list_view_all_context_keys_present_with_defaults` in `tests/test_views/test_list_view.py` — assert all mandatory keys present: `list_item_template`, `empty_state`, `grid_config`, `directory`, `search_query`, `is_searchable`; and `context["page"]["title"]` (the `PageMixin` metadata dict — not Django's `page_obj` pagination object); with a zero-extra-attribute view *(H2: `page` is PageMixin metadata injected as a nested dict with keys title/subtitle/breadcrumbs/icon/class)*
- [X] T037 [US6] Run `poetry run pytest tests/test_views/test_list_view.py -v -k "search_query or current_ordering or all_context_keys"` to confirm US6 tests pass

**Checkpoint**: US6 independently verified — context values for parameter preservation are always injected.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Full test suite validation, skill documentation, and breadcrumb integration test.

- [X] T038 [P] Write test `test_default_breadcrumbs_include_home_and_page_title` in `tests/test_views/test_list_view.py` — assert `context["page"]["breadcrumbs"]` is `[{"text": "Home", "href": "/"}, {"text": <model verbose name plural title case>}]` for zero-config view
- [X] T039 [P] Write test `test_page_title_attribute_overrides_model_derived_title` in `tests/test_views/test_list_view.py` — set `page_title = "Our Catalogue"`, assert `context["page"]["title"] == "Our Catalogue"`
- [X] T040 Add `MVPListView` section to `skills/django-mvp/SKILL.md` — document all class attributes, override hooks, context variables, and the item template naming convention; include the quickstart example
- [X] T041 Run `poetry run pytest tests/test_views/test_list_view.py -v` to confirm entire test module passes (including new + existing search/ordering tests)
- [X] T042 Run `python manage.py check` to confirm no configuration errors after all changes
- [X] T043 [P] Run `poetry run ruff check mvp/ tests/test_views/test_list_view.py skills/django-mvp/SKILL.md` and `poetry run ruff format --check mvp/ tests/test_views/test_list_view.py` to confirm clean linting
- [X] T044 [H1] Playwright MCP — open the demo list page with `MVPListView` wired to a model with 30 records. Confirm: (a) page title renders the model's verbose name plural (not empty/`None`), (b) pagination controls appear (24 records on page 1, controls for page 2), (c) no "New" button appears by default (`has_create_permission = False`). *(Constitution VI + VIII: user-visible behavior changes from stub fixes require Playwright verification)*

**Checkpoint**: All tests pass, system check clean, skill updated, linting green. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 confirmation — MUST complete before any test phase
- **Phases 3–8 (User Stories)**: All depend on Phase 2 completion. Can proceed in priority order (P1 first: Phase 3 + 4, then P2: Phase 5 + 6 + 8, then P3: Phase 7) or in parallel where staffed
- **Phase 9 (Polish)**: Depends on all story phases complete

### User Story Dependencies

| Story | Phase | Priority | Depends on | Independent test? |
|---|---|---|---|---|
| US1 — Zero-Config List Page | 3 | P1 | Phase 2 | ✅ Yes |
| US2 — Item Template Convention | 4 | P1 | Phase 2 | ✅ Yes |
| US3 — Empty State Messaging | 5 | P2 | Phase 2 | ✅ Yes |
| US4 — Create Action Link | 6 | P2 | Phase 2 | ✅ Yes |
| US5 — Grid Configuration | 7 | P3 | Phase 2 | ✅ Yes |
| US6 — Search/Ordering/Pagination | 8 | P2 | Phase 2 | ✅ Yes |

### Parallel Opportunities Within Each Phase

- **Phase 2**: T006 and T007 (docstrings) are [P] and can run in parallel with T003–T005 if on separate branches; T008 and T009 run together after all complete
- **Phase 3**: T010–T014 can run in parallel (all new test methods in the same file, no ordering dependency)
- **Phase 4**: T016 and T017 are [P] (independent test methods)
- **Phase 5**: T021 and T022 are [P] (independent test methods)
- **Phase 6**: T026 is [P] (class attribute assertion, no setup needed)
- **Phase 7**: T030 and T031 are [P] (independent test methods)
- **Phase 8**: T033 and T034 are [P]; T033 and T035 are independent
- **Phase 9**: T038, T039, T040, T043 are all [P]

---

## Parallel Example: Phases 3 + 4 (P1 Stories Together)

```
# Team of two working Phase 3 + 4 in parallel after Phase 2 completes:

Dev A: T010 → T011 → T012 → T013 → T014 → T015  (US1 tests)
Dev B: T016 + T017 (parallel) → T018 → T019 → T020  (US2 tests)

# Both run T041 (full test suite) at end of Phase 9
```

---

## Implementation Strategy

**MVP scope**: Phase 1 + Phase 2 + Phase 3 (US1) — delivers a fully working zero-config list page with `paginate_by = 24`, correct page title, and item template auto-discovery. The three-line code change in Phase 2 is the entire runtime delta.

**Incremental delivery**:

1. Phase 2 closes all three stubs and adds docstrings — this is the entire feature change at the Python level
2. Phases 3–8 are test-only additions that verify the already-implemented behaviour
3. Phase 9 adds the skill doc and full suite confirmation

**Total task count**: 43 tasks across 9 phases
**Tasks per user story**: US1 = 6, US2 = 5, US3 = 5, US4 = 4, US5 = 3, US6 = 5
**Parallel opportunities**: 16 tasks marked [P]
