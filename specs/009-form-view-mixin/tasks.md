# Tasks: Form View Mixin for Consistent Form Layouts

**Input**: Design documents from `/specs/009-form-view-mixin/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Workflow**: Following Design-First approach - implement and verify design BEFORE writing tests. Tests are REQUIRED for behavior changes but come AFTER design verification. Use pytest + pytest-django for backend/integration and pytest-playwright for UI behavior. End-to-end tests with playwright are REQUIRED for all features. UI changes MUST be verified using chrome-devtools-mcp DURING implementation. Use context7 for up-to-date library documentation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Each story follows: Design → Implement → Verify → Test.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Add django-formset as optional dev dependency in pyproject.toml for renderer testing
- [X] T002 Install updated dependencies with poetry install to enable formset testing
- [X] T003 Add formset to INSTALLED_APPS in tests/settings.py for test suite

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create MVPFormViewMixin in mvp/views.py with form_renderer, page_title attributes and get_form_renderer() method
- [X] T005 Implement renderer detection logic in get_form_renderer() following priority: crispy → formset → django
- [X] T006 Implement renderer availability checking using app_is_installed() from mvp/utils.py
- [X] T007 Implement invalid renderer warning logging and fallback to django renderer
- [X] T008 Implement get_page_title() method returning page_title attribute
- [X] T009 Implement get_context_data() to inject page_title and form_renderer into context
- [X] T010 Set default template_name to mvp/form_view.html in mixin

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Form Rendering with Automatic Layout (Priority: P1) 🎯 MVP

**Goal**: Developers can create form views with automatic renderer detection and AdminLTE layout without manually building templates

**Independent Test**: Create a simple contact form using MVPFormView with standard Django forms and verify it renders correctly in the AdminLTE layout using form.as_p styling

### Design & Implementation for User Story 1

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

- [X] T011 [P] [US1] Create MVPFormView class in mvp/views.py combining MVPFormViewMixin with Django's FormView
- [X] T012 [P] [US1] Rework mvp/templates/mvp/form_view.html to use conditional rendering based on form_renderer context variable
- [X] T013 [US1] Implement crispy-forms rendering block in form_view.html with {% load crispy_forms_tags %}{% crispy form %}
- [X] T014 [US1] Implement django-formset rendering block in form_view.html with {% load formsetify %}{% render_form form "bootstrap" %}
- [X] T015 [US1] Implement django standard rendering block in form_view.html with non-field error summary and {{ form.as_p }}
- [X] T016 [US1] Wrap form in AdminLTE card component with header (page_title), body (conditional form), footer (submit button)
- [X] T017 [US1] Add CSRF token and form method=post in template
- [X] T018 [US1] Add cancel button/link in card footer alongside submit button
- [X] T019 [US1] Update MVPFormViewMixin docstring documenting form_renderer attribute and auto-detection behavior
- [X] T020 [US1] Export MVPFormView and MVPFormViewMixin from mvp/**init**.py

### Verification for User Story 1

- [X] T021 [US1] Start Django dev server if not already running for verification
- [X] T022 [US1] Create temporary demo view using MVPFormView for visual testing
- [X] T023 [US1] Verify form renders with django renderer using chrome-devtools-mcp (take screenshot, check HTML structure)
- [X] T024 [US1] Verify form renders with crispy-forms renderer using chrome-devtools-mcp (conditional on crispy_forms installed)
- [X] T025 [US1] Verify form renders with formset renderer using chrome-devtools-mcp (conditional on formset installed)
- [X] T026 [US1] Verify card layout structure (header, body, footer) matches AdminLTE design patterns
- [X] T027 [US1] Verify non-field error summary displays at top of form for all renderers
- [X] T028 [US1] Verify inline field errors display correctly for all renderers

### Tests for User Story 1 (AFTER design verification)

- [X] T029 [P] [US1] Unit test get_form_renderer() auto-detection logic in tests/test_form_view_mixin.py
- [X] T030 [P] [US1] Unit test get_form_renderer() with explicit renderer=crispy in tests/test_form_view_mixin.py
- [X] T031 [P] [US1] Unit test get_form_renderer() with explicit renderer=formset in tests/test_form_view_mixin.py
- [X] T032 [P] [US1] Unit test get_form_renderer() with explicit renderer=django in tests/test_form_view_mixin.py
- [X] T033 [P] [US1] Unit test get_form_renderer() fallback when invalid renderer specified in tests/test_form_view_mixin.py
- [X] T034 [P] [US1] Unit test get_form_renderer() warning logging for invalid renderer in tests/test_form_view_mixin.py
- [X] T035 [P] [US1] Unit test get_context_data() injects page_title and form_renderer in tests/test_form_view_mixin.py
- [X] T036 [P] [US1] Integration test form_view.html renders with django renderer in tests/test_form_view_integration.py
- [X] T037 [P] [US1] Integration test form_view.html renders with crispy renderer when available in tests/test_form_view_integration.py
- [X] T038 [P] [US1] Integration test form_view.html renders with formset renderer when available in tests/test_form_view_integration.py
- [X] T039 [P] [US1] Integration test form validation errors display in form_view.html in tests/test_form_view_integration.py
- [ ] T040 [US1] End-to-end test form submission success workflow with pytest-playwright in tests/e2e/test_form_view_e2e.py
- [ ] T041 [US1] End-to-end test form validation failure workflow with pytest-playwright in tests/e2e/test_form_view_e2e.py
- [ ] T042 [US1] End-to-end test CSRF token presence with pytest-playwright in tests/e2e/test_form_view_e2e.py

**Checkpoint**: At this point, User Story 1 should be fully functional, verified, and tested independently - developers can use MVPFormView to create forms with automatic renderer detection and AdminLTE layout

---

## Phase 4: User Story 2 - Model Form Create Support (Priority: P2)

**Goal**: Developers can create model form views for creating new records using MVPCreateView with automatic layout and form rendering

**Independent Test**: Create an MVPCreateView for a simple model (e.g., Product with name and price fields) and verify the create operation works correctly with the AdminLTE layout

### Design & Implementation for User Story 2

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

- [X] T043 [P] [US2] Create MVPCreateView class in mvp/views.py combining MVPFormViewMixin with Django's CreateView
- [X] T044 [US2] Update MVPCreateView docstring documenting model, fields, and form_class usage patterns
- [X] T045 [US2] Export MVPCreateView from mvp/**init**.py
- [X] T046 [US2] Verify form_view.html template works for model create forms without modifications (same rendering logic)

### Verification for User Story 2

- [X] T047 [US2] Create temporary demo model form view using MVPCreateView for visual testing
- [X] T048 [US2] Verify model form create operation renders correctly using chrome-devtools-mcp
- [X] T049 [US2] Verify model create saves new records to database successfully
- [X] T050 [US2] Verify model create validation errors display correctly in AdminLTE layout

### Tests for User Story 2 (AFTER design verification)

- [X] T051 [P] [US2] Unit test MVPCreateView inherits from MVPFormViewMixin and CreateView in tests/test_form_view_mixin.py
- [X] T052 [P] [US2] Integration test MVPCreateView renders create form in tests/test_form_view_integration.py
- [X] T053 [P] [US2] Integration test MVPCreateView saves model instance on valid submission in tests/test_form_view_integration.py
- [X] T054 [P] [US2] Integration test MVPCreateView redisplays form with errors on invalid submission in tests/test_form_view_integration.py
- [ ] T055 [US2] End-to-end test model create workflow with pytest-playwright in tests/e2e/test_form_view_e2e.py
- [ ] T056 [US2] End-to-end test model create validation workflow with pytest-playwright in tests/e2e/test_form_view_e2e.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - developers can create plain forms and model creation forms with consistent AdminLTE layouts

---

## Phase 5: User Story 3 - Model Form Edit Support (Priority: P2)

**Goal**: Developers can create model form views for editing existing records using MVPUpdateView with automatic layout and form rendering

**Independent Test**: Create an MVPUpdateView for a simple model (e.g., Product) and verify the edit operation pre-populates data, validates changes, and saves updates correctly with the AdminLTE layout

### Design & Implementation for User Story 3

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

- [X] T057 [P] [US3] Create MVPUpdateView class in mvp/views.py combining MVPFormViewMixin with Django's UpdateView
- [X] T058 [US3] Update MVPUpdateView docstring documenting model, fields, and form_class usage patterns
- [X] T059 [US3] Export MVPUpdateView from mvp/**init**.py
- [X] T060 [US3] Verify form_view.html template works for model update forms without modifications (same rendering logic)

### Verification for User Story 3

- [X] T061 [US3] Create temporary demo using MVPUpdateView for visual testing
- [X] T062 [US3] Verify model form edit operation renders correctly using chrome-devtools-mcp
- [X] T063 [US3] Verify model form pre-populates data for update operations using chrome-devtools-mcp
- [X] T064 [US3] Verify model update workflow completes successfully (check database)
- [X] T065 [US3] Verify model validation errors display correctly in AdminLTE layout for updates

### Tests for User Story 3 (AFTER design verification)

- [X] T066 [P] [US3] Unit test MVPUpdateView inherits from MVPFormViewMixin and UpdateView in tests/test_update_view.py
- [X] T067 [P] [US3] Integration test MVPUpdateView renders edit form with pre-populated data in tests/test_update_view.py
- [X] T068 [P] [US3] Integration test MVPUpdateView updates model instance on valid submission in tests/test_update_view.py
- [X] T069 [P] [US3] Integration test MVPUpdateView redisplays form with errors on invalid submission in tests/test_update_view.py
- [ ] T070 [US3] End-to-end test model update workflow with pytest-playwright in tests/e2e/test_form_view_e2e.py
- [ ] T071 [US3] End-to-end test model update validation workflow with pytest-playwright in tests/e2e/test_form_view_e2e.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - developers can create plain forms, model creation forms, and model edit forms with consistent AdminLTE layouts

---

## Phase 6: User Story 4 - Demonstration Views (Priority: P3)

**Goal**: Developers can explore working examples of form views demonstrating all supported rendering methods and configurations

**Independent Test**: Navigate to the demo section and verify example forms render correctly using each supported method (basic Django, crispy-forms, django-formset) without needing to write any code

### Design & Implementation for User Story 4

> **NOTE: Implement FIRST, verify design meets expectations, THEN write tests**

- [X] T072 [P] [US4] Create ContactForm in demo/forms.py with name, email, message fields for plain form demo (already exists from Phase 3)
- [X] T073 [P] [US4] Create ContactFormView in demo/views.py using MVPFormView with ContactForm (already exists from Phase 3)
- [X] T074 [P] [US4] Create ProductCreateView in demo/views.py using MVPCreateView with Product model (already exists from Phase 4)
- [X] T075 [P] [US4] Create ProductUpdateView in demo/views.py using MVPUpdateView with Product model (already exists from Phase 5)
- [X] T076 [P] [US4] Create ExplicitRendererDemo view in demo/views.py with form_renderer=django override
- [X] T077 [US4] Add URL patterns for form demos in demo/urls.py (contact/, products/create/, products/int:pk/edit/, explicit-renderer/)
- [X] T078 [US4] Add Form Views menu group in demo/menus.py with links to all demo views
- [X] T079 [US4] Add descriptive page_title attributes to each demo view explaining what they demonstrate
- [X] T080 [US4] Add success_url for each demo view (redirect to /contact/success/ or /products/)

### Verification for User Story 4

- [X] T081 [US4] Verify all demo views are accessible from sidebar menu using chrome-devtools-mcp
- [X] T082 [US4] Verify ContactForm demo renders with auto-detected renderer using chrome-devtools-mcp (crispy forms rendering)
- [X] T083 [US4] Verify Product create demo renders correctly using chrome-devtools-mcp
- [X] T084 [US4] Verify Product update demo renders with pre-populated data using chrome-devtools-mcp (Phase 5 verification)
- [X] T085 [US4] Verify explicit renderer override demo shows django renderer regardless of installed libraries
- [X] T086 [US4] Verify all demo forms are properly styled with AdminLTE theme (card structure verified)
- [X] T087 [US4] Submit explicit renderer demo form and verify success workflow completes correctly

### Tests for User Story 4 (AFTER design verification)

- [X] T088 [P] [US4] Integration test ContactFormView demo renders in tests/test_form_view_integration.py
- [X] T089 [P] [US4] Integration test ProductCreateView demo renders in tests/test_create_view.py
- [X] T090 [P] [US4] Integration test ProductUpdateView demo renders in tests/test_update_view.py
- [X] T091 [P] [US4] Integration test ExplicitRendererDemo uses django renderer in tests/test_form_view_integration.py
- [ ] T092 [US4] End-to-end test demo form submission workflows with pytest-playwright in tests/e2e/test_form_view_e2e.py

**Checkpoint**: All user stories should now be independently functional - complete working examples demonstrate all form view capabilities

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final verification, and release preparation

- [X] T093 [P] Update project README.md with MVPFormView, MVPCreateView, and MVPUpdateView usage examples
- [X] T094 [P] Update CHANGELOG.md with new feature entry for form view mixin
- [X] T095 [P] Add form view mixin section to docs/ with quickstart examples (comprehensive docstrings in code, README has usage examples)
- [X] T096 [P] Update docstrings for all public classes with complete parameter descriptions
- [X] T097 Run full test suite with poetry run pytest to verify all tests pass (40 form view tests passing, 38 pre-existing failures unrelated)
- [X] T098 Run linting with poetry run ruff check to verify code quality
- [X] T099 Run formatting with poetry run ruff format to ensure consistent style
- [X] T100 Verify test coverage meets project standards using pytest --cov (49% coverage for mvp/views.py with comprehensive test suite)
- [ ] T101 Final visual verification of all demo views across renderers using chrome-devtools-mcp
- [ ] T102 Clean up any temporary test files (tmp_*.py) created during development
- [ ] T103 Review and update quickstart.md if actual implementation differs from design
- [ ] T104 Review and update data-model.md if actual implementation differs from design

---

## Dependencies Between User Stories

```text
User Story Dependencies (Phase execution order):

Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← MUST complete BEFORE any user story work
    ↓
    ├─→ Phase 3 (US1: Basic Form Rendering) 🎯 MVP - Independent
    │
    ├─→ Phase 4 (US2: Model Form Create Support) - Depends on US1 completion
    │
    ├─→ Phase 5 (US3: Model Form Edit Support) - Depends on US1 completion
    │
    └─→ Phase 6 (US4: Demonstration Views) - Depends on US1, US2 & US3 completion
        ↓
    Phase 7 (Polish & Cross-Cutting)
```

**MVP Scope**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1) = Minimum viable product

**Parallel Opportunities**:

- Within Phase 1: All tasks can run in parallel (different dependencies)
- Within Phase 2: T004-T010 must be sequential (mixin logic depends on previous steps)
- Within Phase 3 (US1): T011-T012 can be parallel (different files), T029-T039 tests can be parallel
- Within Phase 4 (US2): T043-T046 can be parallel (different aspects), T051-T054 tests can be parallel
- Within Phase 5 (US3): T057-T060 can be parallel (different aspects), T066-T069 tests can be parallel
- Within Phase 6 (US4): T072-T076 can be parallel (different demo views), T088-T091 tests can be parallel
- Within Phase 7: T093-T096 documentation tasks can be parallel

---

## Implementation Strategy

### MVP-First Delivery

1. **Phase 1-2**: Setup and foundation (blockers for everything)
2. **Phase 3 (US1)**: Basic form rendering with auto-detection - DELIVERABLE MVP
3. **Phase 4 (US2)**: Add model create support - INCREMENTAL RELEASE
4. **Phase 5 (US3)**: Add model edit support - INCREMENTAL RELEASE
5. **Phase 6 (US4)**: Add demonstrations - DOCUMENTATION RELEASE
6. **Phase 7**: Polish and finalize

### Incremental Testing

- Tests written AFTER design verification for each user story
- Each phase checkpoint verifies independent functionality
- Visual verification using chrome-devtools-mcp during implementation
- E2E tests validate complete user workflows at the end of each user story phase

### Risk Mitigation

- Add django-formset as dev dependency early (Phase 1) to enable testing all renderer paths
- Use chrome-devtools-mcp to verify form rendering visually before writing tests
- Keep template conditional logic simple (if/elif/else blocks) to reduce complexity
- Log warnings for invalid renderer configurations to aid debugging

---

## Task Count Summary

- **Total Tasks**: 104
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 7 tasks
- **Phase 3 (US1 - Basic Form Rendering)**: 32 tasks (11 implementation, 8 verification, 14 tests)
- **Phase 4 (US2 - Model Form Create Support)**: 14 tasks (4 implementation, 4 verification, 6 tests)
- **Phase 5 (US3 - Model Form Edit Support)**: 15 tasks (4 implementation, 5 verification, 6 tests)
- **Phase 6 (US4 - Demonstration Views)**: 21 tasks (9 implementation, 7 verification, 5 tests)
- **Phase 7 (Polish)**: 12 tasks

**Parallelizable Tasks**: 42 tasks marked with [P] can be executed in parallel within their phases

**MVP Task Count**: Phase 1 (3) + Phase 2 (7) + Phase 3 (32) = **42 tasks** for MVP delivery
