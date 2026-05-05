# Tasks: MVPCreateView — Zero-Config Model Create View

**Input**: Design documents from `specs/011-mvp-create-view/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Scope**: One class (`MVPCreateView`), two new methods, one source file.
Relocate 3 existing tests; add 11 new tests (8 unit + 3 E2E).
No template, model, migration, or URL changes.

---

## Phase 1: Setup

**Purpose**: Confirm the baseline is green before any changes are made.

- [X] T001 Verify `pytest tests/test_views/test_edit_view.py` passes (baseline for `mvp/views/edit.py`)
- [X] T002 Verify `python manage.py check` passes with zero errors or warnings

---

## Phase 2: Foundational — Relocate Decoupled Tests

**Purpose**: The three existing `TestGetSuccessMessage` tests currently use `MVPCreateView`
as their test vehicle for `MVPModelFormBase.get_success_message()` behaviour. After the
`MVPCreateView` override is added in Phase 3 they will fail. Move them now — while
they still pass — so we have a clean baseline before implementation begins.

**⚠️ CRITICAL**: This phase must complete before Phase 3 implementation starts.

- [X] T003 Relocate `TestGetSuccessMessage` tests to `MVPUpdateView` vehicle in `tests/test_views/test_edit_view.py`

  Move the three test methods to a new class `TestMVPModelFormBaseSuccessMessage` that
  builds its test view using `MVPUpdateView` instead of `MVPCreateView`.  Helper to add:

  ```python
  def make_update_view(extra_attrs=None):
      rf = RequestFactory()
      request = rf.post("/", data={})
      request.user = User()
      attrs = {
          "model": Product,
          "fields": ["name"],
          "template_name": "form_view.html",
          "has_list_permission": True,
          "has_detail_permission": True,
          "has_create_permission": True,
          "has_update_permission": True,
          "has_delete_permission": True,
          **(extra_attrs or {}),
      }
      view_cls = type("StubUpdateView", (MVPUpdateView,), attrs)
      view = view_cls()
      view.request = request
      view.kwargs = {}
      view.args = []
      view.object = None
      return view
  ```

  Tests to move (keep the same assertion logic, switch to `make_update_view()`):
  - `test_verbose_name_only_resolves` → asserts lowercase: `f"{Product._meta.verbose_name} created."`
  - `test_missing_field_placeholder_substitutes_empty_string` → asserts lowercase verbose_name
  - `test_field_value_and_verbose_name_both_resolve` → asserts lowercase verbose_name

- [X] T004 Run `pytest tests/test_views/test_edit_view.py` to confirm all tests still pass after relocation

**Checkpoint**: All existing tests green; `TestGetSuccessMessage` class removed; `TestMVPModelFormBaseSuccessMessage` passes.

---

## Phase 3: User Story 1 — Zero-Config Create Page (Priority: P1) 🎯 MVP

**Goal**: `MVPCreateView` produces a model-aware title, title-cased success message, and
correct defaults (icon, CSS) with only `model` and `fields` set.

**Independent Test**: `class ProductCreateView(MVPCreateView): model = Product; fields = ["name"]`
— navigate to the create URL, assert title "Create Product", icon "add", CSS classes, success
message "Product successfully created.", breadcrumb to list.

### Tests for User Story 1 — write first, observe failing

- [X] T005 [P] [US1] Write `TestMVPCreateViewDefaults` in `tests/test_views/test_edit_view.py`

  Three tests verifying class-level defaults with no overrides:

  ```python
  class TestMVPCreateViewDefaults:
      def test_page_icon_is_add(self): ...       # MVPCreateView.page_icon == "add"
      def test_page_class_contains_create(self): ...  # "mvp-create-page" in MVPCreateView.page_class
      def test_no_page_title_class_attr(self): ...    # MVPCreateView.__dict__ does not contain "page_title"
  ```

- [X] T006 [P] [US1] Write `TestMVPCreateViewPageTitle` in `tests/test_views/test_edit_view.py`

  Five tests for `get_page_title()`:

  ```python
  class TestMVPCreateViewPageTitle:
      def test_default_title_single_word_verbose_name(self): ...
          # make_create_view() → get_page_title() == "Create Product"
      def test_default_title_multi_word_verbose_name(self): ...
          # model with verbose_name="order line" → "Create Order Line"
      def test_explicit_page_title_returned(self): ...
          # page_title="Add a new product" → "Add a new product"
      def test_empty_string_page_title_falls_back(self): ...
          # page_title="" → "Create Product"
      def test_lazy_string_page_title_returned(self): ...
          # page_title=_("Add Product") → "Add Product"
  ```

- [X] T007 [P] [US1] Write `TestMVPCreateViewSuccessMessage` in `tests/test_views/test_edit_view.py`

  Three tests for `get_success_message()`:

  ```python
  class TestMVPCreateViewSuccessMessage:
      def test_default_message_uses_title_cased_verbose_name(self): ...
          # get_success_message({}) == "Product successfully created."
      def test_custom_message_with_field_interpolation(self): ...
          # success_message="%(name)s was added.", cleaned_data={"name": "Widget"} → "Widget was added."
      def test_missing_key_substitutes_empty_string(self): ...
          # success_message="%(verbose_name)s %(missing)s done.", cleaned_data={} → "Product  done."
  ```

- [X] T008 [US1] Run `pytest tests/test_views/test_edit_view.py -k "TestMVPCreateView"` — confirm all new tests **FAIL** (expected before implementation)

### Implementation for User Story 1

- [X] T009 [US1] Implement `MVPCreateView.get_page_title()` and `get_success_message()` in `mvp/views/edit.py`

  Changes to `MVPCreateView`:
  1. Remove the `page_title = _("Create Entry")` class attribute.
  2. Add `get_page_title()`:

     ```python
     def get_page_title(self) -> str:
         """Return a model-aware page title, or the explicit override if set.

         When ``page_title`` is falsy (unset or empty string), derives the title
         from the model's ``verbose_name`` — capitalised with ``.title()`` — and
         prepends ``"Create "``. For example, a ``Product`` model with
         ``verbose_name = "product"`` produces ``"Create Product"``; a model with
         ``verbose_name = "order line"`` produces ``"Create Order Line"``.

         When ``page_title`` is set to a truthy value, returns it directly (cast
         to ``str`` to resolve lazy translation strings).

         Returns:
             str: The page title to display.
         """
         if self.page_title:
             return str(self.page_title)
         return f"Create {self.model_meta.verbose_name.title()}"
     ```

  3. Add `get_success_message()`:

     ```python
     def get_success_message(self, cleaned_data: dict) -> str:
         """Interpolate ``success_message`` with a title-cased ``verbose_name``.

         Overrides :meth:`MVPModelFormBase.get_success_message` to inject a
         capitalised ``verbose_name`` (e.g. ``"Product"`` rather than
         ``"product"``), so the default flash message reads
         ``"Product successfully created."`` rather than starting with a
         lowercase letter.

         Any ``%(key)s`` placeholder absent from ``cleaned_data`` silently
         substitutes ``""`` via ``collections.defaultdict(str)``; no
         ``KeyError`` is raised.

         Args:
             cleaned_data (dict): Validated form field values.

         Returns:
             str: The formatted success message.
         """
         data = defaultdict(str, cleaned_data)
         data["verbose_name"] = self.model_meta.verbose_name.title()
         return self.success_message % data
     ```

- [X] T010 [US1] Run `pytest tests/test_views/test_edit_view.py -k "TestMVPCreateView"` — confirm all new tests **PASS**
- [X] T011 [US1] Run `python manage.py check` — confirm zero errors or warnings
- [X] T012 [US1] Run `pytest tests/test_views/` — confirm full suite still passes (no regressions in UpdateView/DeleteView/FormView tests)

**Checkpoint**: User Story 1 fully functional. Title, icon, CSS, success message, and breadcrumb all work with zero-config. All tests green.

---

## Phase 4: User Story 2 — Customised Title and Message (Priority: P2)

**Goal**: Every default can be independently overridden by setting a class attribute or
overriding a `get_*()` method, without affecting any other default.

**Independent Test**: Set `page_title = "Add a new product"` and `success_message = "%(name)s was added."` — verify correct title on render and custom flash on save.

*Note*: The five tests for this story are already written in `TestMVPCreateViewPageTitle`
(T006 covers `test_explicit_page_title_returned` and `test_lazy_string_page_title_returned`)
and `TestMVPCreateViewSuccessMessage` (T007 covers `test_custom_message_with_field_interpolation`).
The only remaining gap is a test for icon and CSS overrides.

### Tests for User Story 2

- [X] T013 [P] [US2] Write `TestMVPCreateViewOverrides` in `tests/test_views/test_edit_view.py`

  Two tests verifying that each remaining default is independently overridable:

  ```python
  class TestMVPCreateViewOverrides:
      def test_page_icon_overridable(self): ...
          # page_icon="edit" → get_page_icon() == "edit"
      def test_page_class_overridable(self): ...
          # page_class="custom-class" → "custom-class" in view.get_page_class()
  ```

- [X] T014 [US2] Run `pytest tests/test_views/test_edit_view.py -k "TestMVPCreateViewOverrides"` — confirm tests **PASS** (these test existing `PageMixin` behaviour; should pass without code changes)
- [X] T015 [US2] Run `pytest tests/test_views/` — confirm full suite still passes

**Checkpoint**: User Stories 1 AND 2 fully functional and independently testable.

---

## Phase 5: User Story 3 — Breadcrumb When No List View Exists (Priority: P3)

**Goal**: When `has_list_permission` is falsy or no list URL is registered, the breadcrumb
first item renders as a `<span>` (plain text) rather than an `<a>` tag.

**Independent Test**: `has_list_permission = False` → breadcrumb renders without `href`
on the list item.

*Note*: Research confirmed this is already satisfied by the base class via the
`django-cotton-bs5` breadcrumbs component's `href|yesno:"a,span"` logic. The task here
is to verify and document with an explicit unit test.

### Tests for User Story 3

- [X] T016 [P] [US3] Write `TestMVPCreateViewBreadcrumb` in `tests/test_views/test_edit_view.py`

  Six tests verifying breadcrumb structure and override behaviour under `PageObjectMixin.get_breadcrumbs()` (covers SC-003 breadcrumb override requirement):

  ```python
  class TestMVPCreateViewBreadcrumb:
      def test_breadcrumb_has_two_items(self): ...
          # make_create_view() → len(view.get_breadcrumbs()) == 2
      def test_first_item_has_no_href_when_list_permission_false(self): ...
          # has_list_permission=False → breadcrumbs[0].get("href") is falsy
      def test_first_item_has_href_when_list_permission_true(self): ...
          # has_list_permission=True → breadcrumbs[0]["href"] == reverse("product-list")
      def test_second_item_has_no_href(self): ...
          # breadcrumbs[1].get("href") is None/absent (current page)
      def test_second_item_text_matches_page_title(self): ...
          # breadcrumbs[1]["text"] == view.get_page_title() == "Create Product"
      def test_get_breadcrumbs_override_is_respected(self): ...
          # subclass overrides get_breadcrumbs() → custom list returned (SC-003 breadcrumb override)
  ```

- [X] T017 [US3] Run `pytest tests/test_views/test_edit_view.py -k "TestMVPCreateViewBreadcrumb"` — confirm tests **PASS** (no code changes expected; tests the existing base class behaviour)
- [X] T018 [US3] Run `pytest tests/test_views/` — confirm full suite still passes

**Checkpoint**: All three user stories independently functional and tested.

---

## Phase 6: E2E Verification & Polish

**Purpose**: Full browser round-trip verification (Playwright MCP + pytest-playwright),
Ruff lint check, and skill currency update.

### E2E — Playwright MCP (Principle VI)

- [X] T019 Use the Playwright MCP server to open the product create page at `http://localhost:8000/products/create/` and verify:
  - Page title renders as "Create Product" (not "Create Entry")
  - Breadcrumb first item links to the product list
  - Icon element reflects "add"

- [X] T020 Use the Playwright MCP server to submit the create form with valid data and verify:
  - Flash message reads "Product successfully created." (title-cased, not lowercase)
  - User is redirected to the product detail or list page

### E2E — pytest-playwright (Principle VIII)

- [X] T021 [P] Write `TestMVPCreateViewE2E` in `tests/test_views/test_edit_view_e2e.py`

  Three pytest-playwright tests:

  ```python
  @pytest.mark.django_db(transaction=True)
  def test_US1_create_page_title_is_model_aware(page, live_server): ...
      # Navigate to /products/create/ → page title element contains "Create Product"

  @pytest.mark.django_db(transaction=True)
  def test_US1_success_message_is_title_cased(page, live_server, category): ...
      # Fill and submit create form → flash message contains "Product successfully created."

  @pytest.mark.django_db(transaction=True)
  def test_US1_breadcrumb_links_to_list(page, live_server): ...
      # Navigate to /products/create/ → first breadcrumb <a> href == "/products/"
  ```

- [X] T022 Run `pytest tests/test_views/test_edit_view_e2e.py -m e2e` — confirm all E2E tests **PASS**

### Polish

- [X] T023 [P] Run `poetry run ruff check mvp/views/edit.py tests/test_views/test_edit_view.py` — fix any lint issues
- [X] T024 [P] Update `skills/django-mvp/SKILL.md` — amend the `MVPCreateView` entry to document auto-derived title (`get_page_title()`) and title-cased success message (`get_success_message()`)
- [X] T025 Run `pytest tests/` — full suite green with all new tests included
- [X] T026 Run `python manage.py check` — zero errors or warnings confirmed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start here.
- **Phase 2 (Foundational)**: Depends on Phase 1. Must complete before Phase 3.
- **Phase 3 (US1)**: Depends on Phase 2. Tests must fail before T009; pass after.
- **Phase 4 (US2)**: Depends on Phase 3 completion (overrides build on confirmed defaults).
- **Phase 5 (US3)**: Depends on Phase 3 completion; can run in parallel with Phase 4.
- **Phase 6 (Polish)**: Depends on Phases 3–5 all complete.

### User Story Dependencies

- **US1 (P1)**: Blocks US2 and US3 — core implementation must exist first.
- **US2 (P2)**: Can proceed after US1; shares the same source file with no conflict.
- **US3 (P3)**: Independent of US2; tests the base class, no code changes required.

### Within Phase 3

- T005, T006, T007 are all `[P]` — write all three test classes before running T008.
- T009 (implementation) must follow T008 (confirmed failing tests).
- T010, T011, T012 are sequential validation steps.

### Parallel Opportunities

| Parallel group | Tasks |
|----------------|-------|
| Write US1 test classes | T005, T006, T007 |
| Write US2 and US3 tests (after Phase 3 complete) | T013, T016 |
| Polish (after all stories green) | T021, T023, T024 |

---

## Parallel Example: User Story 1 Tests

```bash
# Write all three test classes in parallel before observing failures:
Task T005: Write TestMVPCreateViewDefaults in tests/test_views/test_edit_view.py
Task T006: Write TestMVPCreateViewPageTitle in tests/test_views/test_edit_view.py
Task T007: Write TestMVPCreateViewSuccessMessage in tests/test_views/test_edit_view.py

# Then run T008 to confirm all fail, then T009 to implement.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Confirm baseline green (T001–T002)
2. Phase 2: Relocate decoupled tests (T003–T004)
3. Phase 3: Write failing tests → implement → validate (T005–T012)
4. **STOP and VALIDATE**: `pytest tests/test_views/` all green; `manage.py check` clean
5. Ship US1 — developer can now use `MVPCreateView` with zero config

### Full Delivery

Continue with Phase 4 (US2 override tests), Phase 5 (US3 breadcrumb tests), then Phase 6
(E2E, lint, skill update) for the complete feature.

---

## Task Summary

| Phase | Tasks | Story | Parallelisable |
|-------|-------|-------|---------------|
| 1 — Setup | T001–T002 | — | No |
| 2 — Foundational | T003–T004 | — | No |
| 3 — US1 Implementation | T005–T012 | US1 | T005, T006, T007 |
| 4 — US2 Overrides | T013–T015 | US2 | T013 |
| 5 — US3 Breadcrumb | T016–T018 | US3 | T016 |
| 6 — E2E & Polish | T019–T026 | — | T021, T023, T024 |
| **Total** | **26 tasks** | | |

**New tests added**: 8 unit test methods relocated/added in `test_edit_view.py` + 3 E2E tests in `test_edit_view_e2e.py` = **11 tests**
**Source changes**: `mvp/views/edit.py` — 2 methods added, 1 class attribute removed
