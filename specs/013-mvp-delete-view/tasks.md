# Tasks: MVP Delete View

**Feature**: `013-mvp-delete-view`  
**Input**: `specs/013-mvp-delete-view/plan.md`, `specs/013-mvp-delete-view/spec.md`  
**Branch**: `013-mvp-delete-view`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different file, no pending dependencies)
- **[Story]**: Which user story this task belongs to (US1â€“US4)

---

## Phase 1: Setup

**Purpose**: Establish a green baseline before any changes.

- [X] T001 Run existing test suite as baseline: `pytest tests/test_views/test_delete_view.py -v` â€” record current pass/fail state before modifications begin

---

## Phase 2: Foundational â€” `DeleteConfirmForm` Contract

**Purpose**: Update `DeleteConfirmForm` to accept a `confirmation_value` kwarg and enforce
it in validation. This is the only foundational blocking prerequisite because US4 (type-to-confirm)
depends on the updated form contract, and the form tests verify the correct interface before
view-layer code is written.

**âš ï¸ CRITICAL**: US4 view tasks (T016â€“T019) cannot begin until this phase is complete.

- [X] T002 Add `__init__(self, *args, confirmation_value=None, **kwargs)` and `clean_confirmation()` to `DeleteConfirmForm` in `mvp/forms.py` â€” `clean_confirmation()` compares stripped user input to `self._confirmation_value`; raises `ValidationError(_("The value you entered does not match. Please try again."))` on mismatch; when `confirmation_value` is `None` no value check is applied
- [X] T003 Run `python manage.py check` to confirm no import/structural errors from T002

**Checkpoint**: `DeleteConfirmForm` now validates the typed value against a known string.

---

## Phase 3: User Story 1 â€” Simple Confirmation (Priority: P1) ðŸŽ¯ MVP

**Goal**: A zero-config delete view that shows a warning, displays the correct interpolated
page title ("Delete Product"), renders a 3-level breadcrumb (List â†’ Detail â†’ Delete), and
after POST deletes the object, emits a flash message, and redirects via the correct priority
chain (`?next=` â†’ `success_url` â†’ list URL).

**Independent Test**: GET returns HTTP 200 with title containing model verbose_name; breadcrumbs
has three items; POST with no body returns 302 to list URL, object gone, one Django message present.

### Implementation for User Story 1

- [X] T004 [US1] Change `page_title` from `_("Delete Entry")` to `_("Delete %(verbose_name)s")` in `MVPDeleteView` class attributes in `mvp/views/edit.py` (one-line change; title is interpolated via `MVPModelFormBase.get_page_title()`)
- [X] T005 [US1] Add `get_breadcrumbs()` method to `MVPDeleteView` in `mvp/views/edit.py` â€” returns three-item list: `{"text": self.get_list_title(), "href": self.resolve_crud_url("list")}`, `{"text": str(self.object), "href": self.resolve_crud_url("detail")}`, `{"text": self.get_page_title()}` (no href on final item)
- [X] T006 [US1] In `MVPDeleteView` in `mvp/views/edit.py`, make two tightly coupled changes: (1) **Remove** the `get_next_url()` override entirely â€” its unconditional list-URL fallback matches at Step 1 of `MVPModelFormBase.get_success_url()`, making the `success_url` attribute (Step 2) permanently unreachable; (2) **Replace** `get_success_url()` body with: `try: return super().get_success_url() except ImproperlyConfigured: url = self.resolve_crud_url("list"); if url: return url; raise` â€” this restores the correct `?next=` â†’ `success_url` â†’ list priority chain without bypassing the `success_url` attribute
- [X] T007 [US1] Run `python manage.py check` + `pytest tests/test_views/test_delete_view.py::TestMVPDeleteViewBasic -x`

### Tests for User Story 1

- [X] T008 [P] [US1] Update `TestMVPDeleteViewBasic` in `tests/test_views/test_delete_view.py` â€” add/update assertions: (a) GET response title contains model verbose_name (e.g. "Delete Product"); (b) `context["breadcrumbs"]` has exactly 3 items; (c) POST without body returns 302 to list URL; (d) object is deleted from database; (e) one `messages.success` message is present; (f) `success_url = "list"` on the view class also redirects to list URL (not 404); (g) `context["page_icon"] == "delete"` and `"mvp-delete-page" in context["page_class"]` â€” verifies FR-012 AdminLTE integration
- [X] T009 [P] [US1] Update `TestMVPDeleteViewBackUrl` in `tests/test_views/test_delete_view.py` â€” verify existing `?back=` tests still pass; add assertion that `?back=` with an external/unsafe URL falls back to list URL (not the external URL)

**Checkpoint**: US1 fully functional. `TestMVPDeleteViewBasic` and `TestMVPDeleteViewBackUrl` pass.

---

## Phase 4: User Story 2 â€” Related-Objects Summary (Priority: P2)

**Goal**: `show_related_objects = True` shows cascade-deleted related records grouped by model,
capped at `related_objects_max_per_group` per group, with an overflow note ("â€¦ and N more") when
truncated.

**Independent Test**: Configure `show_related_objects = True`; GET returns context where
`related_objects` is a list of 3-tuples `(label, display_list, overflow_count)`;
overflow_count is positive when objects > cap; overflow note appears in HTML; no overflow note
when objects â‰¤ cap.

### Implementation for User Story 2

- [X] T010 [US2] Add `related_objects_max_per_group: int = 25` class attribute to `MVPDeleteView` in `mvp/views/edit.py` (immediately below the existing `confirmation_label` attribute)
- [X] T011 [US2] Update the `related_objects` list comprehension in `get_context_data()` in `mvp/views/edit.py` â€” change from 2-tuple `(label, objs)` to 3-tuple `(label, list(instances)[:cap], max(0, len(instances) - cap))` where `cap = self.related_objects_max_per_group`
- [X] T012 [US2] Update `delete_view.html` â€” change `{% for label, objs in related_objects %}` to `{% for label, objs, overflow in related_objects %}`; add `{% if overflow %}<p class="text-muted small mb-0">â€¦ and {{ overflow }} more</p>{% endif %}` inside the loop after the related-items list

### Tests for User Story 2

- [X] T013 [P] [US2] Update `TestMVPDeleteViewRelatedObjects` in `tests/test_views/test_delete_view.py` â€” cover: (a) `related_objects` context is a list of 3-tuples; (b) display list is capped at `related_objects_max_per_group`; (c) `overflow` count equals `total - cap` when overflow exists; (d) overflow note appears in rendered HTML; (e) no overflow note when objects â‰¤ cap; (f) when `show_related_objects = False`, `related_objects` is empty list; (g) POST still deletes correctly when related objects exist

**Checkpoint**: US2 functional. `TestMVPDeleteViewRelatedObjects` passes.

---

## Phase 5: User Story 3 â€” Protected-Record Detection (Priority: P2)

**Goal**: When a PROTECT FK constraint would block deletion, the view auto-detects this
via `_collect_deletion_data()`, sets `is_protected=True` in context, hides the Delete button,
and lists the blocking records. A crafted POST to a protected object re-renders the page
(HTTP 200) and does not raise an unhandled 500.

**Independent Test**: Create object with PROTECT FK referencing it; GET returns
`context["is_protected"] == True`; rendered HTML has no Delete button; POST returns HTTP 200
re-rendering the page; object still exists in database.

### Implementation for User Story 3

- [X] T014 [US3] Verify `delete_view.html` â€” confirm the existing `{% if is_protected %}` branch already: (a) hides the Delete button, (b) shows `protected_objects` list, (c) shows a suitable alert. **No code change is expected** â€” the existing branching was implemented in a prior session. Mark complete after visual confirmation. If any gap is found, apply the minimal targeted fix in `mvp/templates/delete_view.html` and document the change.

### Tests for User Story 3

- [X] T015 [P] [US3] Update `TestMVPDeleteViewProtected` in `tests/test_views/test_delete_view.py` â€” add/confirm: (a) GET with protected object returns 200 with `is_protected=True` in context; (b) HTML contains protection explanation but no Delete button; (c) POST to protected object returns 200 (re-render), not 302 or 500; (d) protected object is not deleted

**Checkpoint**: US3 functional. `TestMVPDeleteViewProtected` passes.

---

## Phase 6: User Story 4 â€” Type-to-Confirm (Priority: P3)

**Goal**: `require_confirmation = True` routes the delete through `DeleteConfirmForm` via
Django's standard form machinery (`get_form_class()` / `get_form_kwargs()` / `form_valid()` /
`form_invalid()`). Wrong value â†’ `form_invalid()` re-renders with form errors. Correct value â†’
`form_valid()` deletes and redirects.

**Independent Test**: POST with wrong text â†’ HTTP 200, `form.errors["confirmation"]` present;
POST with empty text â†’ HTTP 200, required-field error; POST with correct text â†’ HTTP 302,
object deleted, flash message present.

**Dependencies**: Requires T002 (`DeleteConfirmForm` with `confirmation_value` kwarg).

### Implementation for User Story 4

- [X] T016 [US4] Add `get_form_class()` to `MVPDeleteView` in `mvp/views/edit.py` â€” returns `DeleteConfirmForm` when `self.require_confirmation` is `True`, otherwise delegates to `super().get_form_class()`
- [X] T017 [US4] Add `get_form_kwargs()` to `MVPDeleteView` in `mvp/views/edit.py` â€” calls `super().get_form_kwargs()` then injects `kwargs["confirmation_value"] = self.get_confirmation_value()` when `self.require_confirmation` is `True`; returns kwargs
- [X] T018 [US4] Add `form_valid()` to `MVPDeleteView` in `mvp/views/edit.py` â€” computes `success_url = self.get_success_url()` **before** deletion (object still exists at this point), calls `self.object.delete()`, calls `messages.success(self.request, self.get_success_message({}))`, returns `HttpResponseRedirect(success_url)`
- [X] T019 [US4] Refactor `post()` in `MVPDeleteView` in `mvp/views/edit.py` â€” new body: (1) `self.object = self.get_object()`; (2) `_, protected = self._collect_deletion_data()`; (3) if protected, `return self.render_to_response(self.get_context_data())`; (4) `form = self.get_form()`; (5) `return self.form_valid(form) if form.is_valid() else self.form_invalid(form)` â€” remove the manual `require_confirmation` string-check block and the inline `ProtectedError` try/except
- [X] T020 [US4] Remove `context.setdefault("confirmation_error", kwargs.get("confirmation_error", ""))` from `get_context_data()` in `mvp/views/edit.py` â€” errors are now carried by the form object, not a separate context key
- [X] T021 [US4] Run `python manage.py check` + `pytest tests/test_views/test_delete_view.py -x`

### Tests for User Story 4

- [X] T022 [P] [US4] Update `TestDeleteConfirmForm` in `tests/test_views/test_delete_view.py` â€” add: (a) `DeleteConfirmForm(data={"confirmation": "correct"}, confirmation_value="correct").is_valid()` returns `True`; (b) `DeleteConfirmForm(data={"confirmation": "wrong"}, confirmation_value="correct").is_valid()` returns `False` with `"confirmation"` in errors; (c) `DeleteConfirmForm(data={"confirmation": ""}, confirmation_value="correct").is_valid()` returns `False` (required field); (d) `DeleteConfirmForm(data={"confirmation": "x"}, confirmation_value=None).is_valid()` returns `True` (no check when `confirmation_value` is None)
- [X] T023 [P] [US4] Update `TestMVPDeleteViewTypeToConfirm` in `tests/test_views/test_delete_view.py` â€” update to form-machinery contract: (a) POST with wrong value returns 200 with `form.errors["confirmation"]` in context (not manual `confirmation_error` key); (b) POST with empty value returns 200 with required-field error; (c) POST with correct value returns 302, object deleted, flash present; (d) `require_confirmation = False` (default) skips confirmation entirely on POST; (e) assert `context["confirmation_label"]` is a lazy translation object (call `str()` on it and confirm it matches the expected English string â€” verifies FR-009 i18n compliance without importing Django internals)

**Checkpoint**: All four scenarios operational. Full test suite passes:
`pytest tests/test_views/test_delete_view.py -v`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Docstrings, skill documentation, linting, E2E tests, full test run, and UI verification.

- [X] T024 [P] Update `MVPDeleteView` class docstring in `mvp/views/edit.py` â€” add full `Config:` block (documenting all class attributes and their defaults), `Override hooks:` block (listing `get_breadcrumbs`, `get_confirmation_value`, `get_back_url`, `get_form_class`, `get_form_kwargs`, `form_valid`, `get_success_url`), and an `Example::` block showing minimal subclass with `model`, `fields`, and optional `show_related_objects = True`
- [X] T025 [P] Update `skills/django-mvp/SKILL.md` â€” document `MVPDeleteView` public API: corrected `page_title` default, `get_breadcrumbs()`, `related_objects_max_per_group`, `get_success_url()` priority chain (`?next=` â†’ `success_url` â†’ list URL), and the four deletion scenarios
- [X] T026 Run `ruff check mvp/views/edit.py mvp/forms.py` and fix any linting errors
- [X] T027 [P] Run `djlint mvp/templates/delete_view.html` and fix any template linting errors
- [X] T028 Create `tests/test_views/test_delete_view_e2e.py` with pytest-playwright E2E tests covering all four deletion scenarios â€” (a) US1: navigate to delete page, assert Delete button and permanent-deletion warning present, click Delete, assert redirect to list URL and object absent from list; (b) US2: `show_related_objects=True`, assert grouped related-items section visible, assert "â€¦ and N more" overflow note appears when related objects exceed cap; (c) US3: navigate to delete page for a protected record, assert Delete button is absent and protection-blocking message present, submit form via POST, assert page re-renders (200) with protection message and object still exists; (d) US4: `require_confirmation=True`, submit wrong text, assert inline field error on `confirmation` field, submit correct text, assert redirect to list and object deleted â€” constitution Principle VIII
- [X] T029 Run full test suite including E2E: `pytest tests/test_views/test_delete_view.py tests/test_views/test_delete_view_e2e.py -v` â€” all tests pass
- [X] T030 [P] Playwright MCP UI verification â€” navigate all four delete scenarios in the demo app and assert specific UX outcomes: (a) basic delete page: Delete button present, permanent-deletion warning visible, breadcrumb has three levels (List â†’ object name â†’ Delete); (b) `show_related_objects=True` page: grouped related-items section visible, "â€¦ and N more" overflow note present when objects exceed cap; (c) protected-object page: protection alert shown, Delete button absent, blocking record names listed; (d) `require_confirmation=True` page: confirmation input visible with expected string shown in prompt â€” submit wrong value and assert inline error adjacent to field, submit correct value and assert redirect to list â€” constitution Principle VI

---

## Dependencies

```
T001
  â””â”€> T002 â†’ T003
        â””â”€> T004 â†’ T005 â†’ T006 â†’ T007
              â”œâ”€> T008 [P]    (US1 verify)
              â”œâ”€> T009 [P]    (US1 verify)
              â”œâ”€> T010 â†’ T011 â†’ T012 â†’ T013 [P]   (US2)
              â””â”€> T014 â†’ T015 [P]                  (US3)
T003 + T007
  â””â”€> T016 â†’ T017 â†’ T018 â†’ T019 â†’ T020 â†’ T021
        â”œâ”€> T022 [P]    (US4 form verify)
        â””â”€> T023 [P]    (US4 view verify)
T021
  â””â”€> T024 [P], T025 [P], T026, T027 [P]
        â””â”€> T028 â†’ T029 â†’ T030 [P]
```

### Parallel Opportunities

**After T007 (US1 checkpoint)**:
- T008 and T009 (US1 verify) â€” parallel with each other
- T010â€“T013 (US2) and T014â€“T015 (US3) â€” can run in parallel with each other

**After T021 (US4 checkpoint)**:
- T022 and T023 (US4 verify) â€” parallel with each other
- T024, T025, T027 (polish docs/template) â€” all parallel

**MVP scope**: Phases 1â€“3 (Setup + Foundational + US1) deliver a fully working delete view.

---

## Implementation Strategy

1. **Start small**: Phase 1 establishes the baseline. Phase 2 updates the form.
2. **US1 first** (P1 priority): Fix page title, add breadcrumbs, fix success_url chain. Smallest changeset that delivers a correct view.
3. **US2 and US3 in parallel** (both P2): Related-objects (T010â€“T013) and protection detection (T014â€“T015) can proceed in parallel because they touch different code paths.
4. **US4 last** (P3): Type-to-confirm refactoring is the most invasive change (refactors `post()`); keeping it last means the simpler scenarios are already verified when the form machinery is wired in.
5. **Polish after all stories**: Docstrings, skill docs, linting, and Playwright verification in the final phase.

> **Note**: The existing `MVPDeleteView` in `mvp/views/edit.py` is already substantially
> implemented. These tasks perform targeted, incremental changes rather than a full rewrite.
> Each task touches at most one class method or template block.

