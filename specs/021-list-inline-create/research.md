# Research: List View Inline Create

**Feature**: `021-list-inline-create`
**Date**: 2026-06-02
**Status**: Complete — no NEEDS CLARIFICATION items remain

---

## 1. `?next=` Redirect Support in `MVPCreateView`

**Question**: Does `MVPCreateView` already honour the `?next=` query parameter so the modal form action can redirect back to the list page after a successful create?

**Finding**: Yes, fully implemented. `NextURLMixin` (`mvp/views/edit.py:25`) is composed into `MVPFormBase` and therefore into `MVPModelFormBase` and `MVPCreateView`. The mixin:

- Reads `?next=` from the POST body on POST, or from the query string on GET
- Validates the candidate URL with `url_has_allowed_host_and_scheme` (open-redirect protection)
- Rejects bare words that don't start with `/` or contain `://`
- Also supports CRUD shorthands (e.g. `"list"`) resolved via `resolve_crud_url()`
- Priority in `get_success_url()`: `next_url` → `success_url` → list URL → error

**Decision**: No changes needed to `MVPCreateView`. The modal form action URL only needs to append `?next={{ request.path }}` in the template; the create view already handles it.

**Alternative considered**: Adding a dedicated `?back=` parameter (as used by `MVPDeleteView`). Rejected — `next` is the Django standard, already validated and used by `MVPCreateView`.

---

## 2. Permission Gating for `create_form` Injection

**Question**: How should `MVPListViewMixin.get_context_data()` check permission before injecting `create_form`, given that the spec requires the check to be independent of `create_url` availability?

**Finding**: `CRUDDirectoryMixin` (from which `MVPListViewMixin` inherits) defines `has_create_permission = False` as a class attribute. The existing `resolve_crud_url()` method checks it via:

```python
perm = getattr(self, f"has_{action}_permission", None)
allowed = perm(self.request.user) if callable(perm) else bool(perm)
```

This pattern handles both `has_create_permission = True` (boolean) and `has_create_permission = staticmethod(lambda user: user.is_staff)` (callable).

**Decision**: Replicate the same two-liner permission check inside `MVPListViewMixin.get_context_data()` — read `self.has_create_permission`, evaluate it (callable or bool), and only inject `create_form` when it resolves to `True`. Do not call `resolve_crud_url("create")` for this check (per FR-004 and Q3 answer: `create_form` is independent of `create_url`).

**Alternative considered**: Exposing a shared `_check_permission(action)` helper on `CRUDDirectoryMixin`. Rejected — adds an extra method for a two-line pattern; not worth the abstraction.

---

## 3. Context Key for Modal Metadata

**Question**: Should `create_modal_title` be passed as a top-level context variable, or bundled into a `create_modal` dict alongside the form?

**Finding**: The existing list view template uses flat top-level context keys (`create_form`, `filter`, `directory`, `page`, etc.). Bundling into a dict would require template changes to access `create_modal.form` instead of `create_form`.

**Decision**: Pass as two separate top-level context keys: `create_form` (form instance) and `create_modal_title` (string). This is consistent with the existing template and requires the smallest template change (replacing the hardcoded `"Create product"` string with `{{ create_modal_title }}`).

---

## 4. `create_modal_title` Default Formula

**Question**: What is the exact default string for the auto-derived modal title?

**Finding**: Django's `model._meta.verbose_name` returns the lower-case singular name (e.g. `"product"`). The pattern `verbose_name.title()` capitalises it to `"Product"`. This is consistent with how `MVPModelFormBase.get_page_title()` formats its titles.

**Decision**: Default = `f"Add {self.model._meta.verbose_name.title()}"`, e.g. `"Add Product"`. Overridable via `create_modal_title` class attribute. The mixin injects the resolved title under the key `create_modal_title` in context.

---

## 5. Cotton Template Changes Scope

**Question**: Which templates require changes, and are any Cotton `django-cotton-bs5` prebuilt components available that we should prefer?

**Finding**:

- `mvp/templates/list_view.html` — has a hardcoded `title="{% trans "Create product" %}"` and a hardcoded `action="{{ directory.create_url }}"` with no `?next=`. Both need updating.
- `mvp/templates/cotton/list/toolbar.html` — already has the correct three-state conditional logic. No changes required.
- The `<c-form>` and `<c-modal>` components used in the modal are `django-cotton-bs5` prebuilt components — no new components needed.
- The `<c-button>` component in the toolbar already has `data-bs-toggle="modal"` / `href=` variant selection.

**Decision**: Minimal template changes — only `list_view.html` needs updates. No new Cotton components required. No djlint violations expected from the changes.

---

## 6. Test Coverage Strategy

**Question**: What can be covered by pytest/Django test client vs what requires Playwright?

**Finding per Constitution VIII (Simplicity Mandate)**:

- Context injection (`create_form` present/absent) → Django test client (`Client.get()`)
- Permission gating (boolean and callable) → Django test client
- Toolbar HTML states (modal button / link button / no button) → Django test client response content
- Modal open/close, Bootstrap JS-driven interaction → **Playwright required** (genuine browser behaviour)
- Form submission via modal and `?next=` redirect → Playwright (multi-step navigation with browser state)

**Decision**: Unit/integration tests in `tests/test_views/test_list_view.py`; E2E Playwright tests in `tests/test_views/test_list_view_e2e.py` (new file, following the naming pattern of `test_edit_view_e2e.py`).

---

## Summary of Decisions

| Decision | Choice | Rationale |
|---|---|---|
| `?next=` in create view | Already supported — no changes | `NextURLMixin` already handles it |
| Permission check in list view | Read `has_create_permission` directly; evaluate callable or bool | Independent of `create_url`; reuse same 2-line pattern |
| Context keys | Two flat keys: `create_form` + `create_modal_title` | Consistent with existing template conventions |
| Modal title default | `f"Add {model._meta.verbose_name.title()}"` | Consistent with MVPModelFormBase pattern |
| Template changes | Only `list_view.html` (title + action with ?next) | Toolbar already correct |
| Test split | pytest for context/HTML; Playwright for modal JS interaction | Constitution VIII Simplicity Mandate |
