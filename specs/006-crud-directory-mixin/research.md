# Research: CRUD Directory Mixin

**Branch**: `006-crud-directory-mixin` | **Date**: 2026-05-03
**Purpose**: Audit the current `CRUDDirectoryMixin` implementation against every functional requirement in the spec; identify all gaps; decide on naming conventions and URL kwargs strategy; determine the full scope of work.

---

## Research Question 1: Does the current implementation satisfy FR-001 through FR-012?

**Task**: Perform a line-by-line review of `CRUDDirectoryMixin` in `mvp/views/detail.py` against every functional requirement. The user explicitly stated: "the implementation was experimental at best."

**Findings**:

| Requirement | Status | Notes |
|---|---|---|
| FR-001: `directory` attribute accepts a list of action names | ✅ | `directory = []` declared; iterated in `get_directory()` |
| FR-002: Each action resolved to URL via `crud_views` name pattern + model name/app label | ✅ | `_get_view_name(action)` calls `crud_views[action].format(model_name=..., app_name=...)` |
| FR-003: Context key `directory` with `{action}_url` entries | ✅ | `get_directory()` returns `{"list_url": ..., "update_url": ...}` etc. |
| FR-004: Exclude URL when `has_{action}_permission` is False, absent, or callable returning False | ⚠️ **GAP** | Works for actions where the permission attribute name matches. However: (1) `has_read_permission` is declared but action key is `"detail"` → code checks `has_detail_permission`, which is never declared → gap is that `has_read_permission` is a dead attribute; (2) `has_list_permission` is never declared — list URL is always excluded from directory unless developer explicitly adds `has_list_permission = True` |
| FR-005: Include URL when `has_{action}_permission` True or callable returning True | ✅ | Logic correct when attribute name matches action |
| FR-006: Default URL kwargs from `self.kwargs` for object-level URLs | ⚠️ **GAP** | `get_lookup_kwargs()` returns `dict(self.kwargs)` and is used for ALL actions, including collection-level ones ("list", "create"). On detail/edit views where `self.kwargs = {"pk": 123}`, reversing a "list" URL with `{"pk": 123}` causes `NoReverseMatch`. This is a latent bug — currently undetected because no demo view sets `"list"` in `directory` while on a detail view. |
| FR-007: Override point for URL kwargs | ✅ | `get_lookup_kwargs()` exists as a public override method |
| FR-008: Object-level actions excluded when kwargs empty | ✅ | `if action in self._OBJECT_ACTIONS and not lookup_kwargs: return None` |
| FR-009: `"list"` and `"create"` actions always use empty kwargs | ❌ **MISSING** | No distinction between object-level and collection-level kwargs (see FR-006 gap). Collection actions use whatever `get_lookup_kwargs()` returns. |
| FR-010: Unknown action in `directory` raises informative error | ✅ | `_get_view_name` raises `ValueError` with action name and valid options |
| FR-011: `directory` key always present in context | ✅ | `get_directory()` returns `{}` when nothing resolves; always injected via `get_context_data()` |
| FR-012: Composable with `ModelInfoMixin` | ✅ | `CRUDDirectoryMixin(ModelInfoMixin)` — already inherits it |

**Summary of gaps**: 3 functional gaps found. Detailed decisions below.

---

## Research Question 2: What permission attributes should be declared on the class?

**Decision**: Rename `has_read_permission` → `has_detail_permission`. Add `has_list_permission = False`.

**Rationale**: The `directory` mechanism is action-name-driven: when `"detail"` is in `directory`, `resolve_crud_url` checks `getattr(self, "has_detail_permission", None)`. The current class declares `has_read_permission`, which is never checked by this mechanism. It is a dead attribute — it neither gates nor enables any directory URL. Renaming it to `has_detail_permission` makes the declared defaults consistent with the resolution logic.

The standard actions in `crud_views` are: `list`, `detail`, `create`, `update`, `delete`. The class should declare a default permission attribute for each:

```python
has_list_permission   = False
has_detail_permission = False  # was: has_read_permission (dead attribute)
has_create_permission = False
has_update_permission = False
has_delete_permission = False
```

**Alternatives considered**:

- Keep `has_read_permission` and map `"detail"` action to it specially — rejected. Would require special-casing one action name, creating a two-tier naming system (action names ≠ permission names). Every convention a developer must memorise is a potential mistake.
- Introduce a separate `permission_map` dict — rejected. Over-engineering for five standard actions. The `has_{action}_permission` pattern is self-documenting and discoverable.

---

## Research Question 3: How should URL kwargs be handled for collection-level vs object-level actions?

**Decision**: Introduce two separate override methods. Rename `get_lookup_kwargs()` → `get_object_url_kwargs()` and add `get_collection_url_kwargs()` returning `{}` by default. The internal `resolve_crud_url` dispatches to the correct getter based on whether the action is in `_OBJECT_ACTIONS`.

> **⚠️ Superseded** (2026-05-03): This two-method design was replaced during clarification by a single `get_url_kwargs(action: str) -> dict | None` method. See spec.md § Clarifications for the final design. The code examples below are retained for historical context only.

**Rationale**: The single `get_lookup_kwargs()` method is ambiguous — its docstring says "URL kwargs for reversing object-level URLs" but the implementation uses it for all actions. This creates the latent `NoReverseMatch` bug described under FR-006 above. Splitting into two named methods is:

1. **Correct by default**: `get_collection_url_kwargs()` returning `{}` means list and create URLs work on both list views and detail views without developer intervention.
2. **Explicit for nested resources**: Developers with nested URL patterns override **both** methods to supply the right kwargs for each action category — no need to decode which action is being resolved inside a single method.
3. **Consistent naming**: `get_object_url_kwargs()` signals "kwargs needed to identify a specific object"; `get_collection_url_kwargs()` signals "kwargs needed to scope a collection (e.g. parent resource in a nested URL)".

**Nested URL example** (standard non-nested):

```python
# No override needed — defaults work
class TaskUpdateView(MVPUpdateView):
    model = Task
    directory = ["list", "detail", "update", "delete"]
    has_list_permission = True
    has_detail_permission = True
    has_update_permission = True
    has_delete_permission = True
```

**Nested URL example** (project → tasks):

```python
class TaskUpdateView(MVPUpdateView):
    model = Task
    directory = ["list", "detail", "update", "delete"]
    # Override to pass only object pk to object-level URLs:
    def get_object_url_kwargs(self):
        return {"pk": self.kwargs["pk"]}
    # Override to pass project_pk to collection-level URLs:
    def get_collection_url_kwargs(self):
        return {"project_pk": self.kwargs["project_pk"]}
```

**Alternatives considered**:

- Keep a single `get_lookup_kwargs(action)` taking an action argument — rejected. Action-aware logic inside the override method adds cognitive burden; developers must inspect which action triggered the call.
- Keep the current single `get_lookup_kwargs()` for object-level only, hard-code `{}` for collection-level, no override point for collection kwargs — rejected. Breaks nested-resource scenarios where collection URLs need parent kwargs.
- Do nothing (document the bug, let developers work around it) — rejected. The user explicitly said the implementation was experimental and wants a clean design.

---

## Research Question 4: Should `_OBJECT_ACTIONS` be a class attribute?

**Decision**: Remove `_OBJECT_ACTIONS = _OBJECT_ACTIONS` from the class body. Reference the module-level `_OBJECT_ACTIONS` frozenset directly in method bodies.

**Rationale**: Class attributes form part of the public API surface. Internal constants used only in method logic should remain module-level private. Exposing `_OBJECT_ACTIONS` on the class invites accidental override (a subclass setting `_OBJECT_ACTIONS = frozenset(...)` would silently change the mixin's behaviour). The module-level frozenset is already accessible within the methods by lexical scope; there is no technical reason to promote it to a class attribute.

**Alternatives considered**: None meaningful. This is a clean-up with no trade-offs.

---

## Research Question 5: What other code interacts with `CRUDDirectoryMixin` and may need updates?

**Task**: Identify all callers and inheritors that would be affected by the changes above.

**Findings**:

| Location | Relationship | Impact |
|---|---|---|
| `mvp/views/detail.py` — `CRUDDirectoryMixin` | Modified directly | All changes land here |
| `mvp/views/detail.py` — `PageObjectMixin` | Inherits `CRUDDirectoryMixin` + `ModelInfoMixin` | `ModelInfoMixin` in explicit bases is redundant (already inherited via `CRUDDirectoryMixin`). Remove it. |
| `mvp/views/edit.py` — `MVPModelFormBase.get_lookup_kwargs()` | Overrides `get_lookup_kwargs()` | Must be renamed to `get_object_url_kwargs()`. Also extends with CreateView fallback (adding `object.pk` after save) — this remains correct. |
| `mvp/views/edit.py` — `MVPUpdateView.get_delete_url()` | Calls `_get_view_name("delete")` directly, ignores `has_delete_permission` | Should call `resolve_crud_url("delete")` to respect permission gating. Currently generates the delete URL unconditionally. The method appends `?back=...&next=...` params (UX logic) — this special logic means it cannot simply be replaced by reading from `get_directory()`, but the permission gate can be applied via `resolve_crud_url`. |
| `mvp/views/list.py` — `MVPListViewMixin` | Inherits `CRUDDirectoryMixin` from `detail.py` | No logic change. Import path unchanged. |
| `demo/views.py` | Uses `MVPCreateView`, `MVPUpdateView`, `MVPDeleteView`, `MVPListViewMixin` | No `directory` or permission attributes set anywhere → currently dormant usage. No code change needed in demo views unless a demo page is added to showcase the feature. |
| `tests/test_views/` | No tests for `CRUDDirectoryMixin` | Full unit test suite must be written. |

---

## Research Question 6: What is the complete test coverage plan?

**Findings**: No tests for `CRUDDirectoryMixin` exist. The following test cases are required, organized by user story:

**US1 — Declarative directory resolution:**

- `test_resolves_list_url_when_list_in_directory_with_list_permission`
- `test_resolves_detail_url_when_detail_in_directory_with_detail_permission`
- `test_resolves_create_url_when_create_in_directory_with_create_permission`
- `test_resolves_update_url_when_update_in_directory_with_update_permission`
- `test_resolves_delete_url_when_delete_in_directory_with_delete_permission`
- `test_empty_directory_produces_empty_dict`
- `test_unknown_action_in_directory_raises_value_error`

**US2 — Permission gating:**

- `test_excludes_url_when_permission_is_false`
- `test_excludes_url_when_permission_attribute_absent`
- `test_includes_url_when_permission_attribute_is_true`
- `test_includes_url_when_permission_is_callable_returning_true`
- `test_excludes_url_when_permission_is_callable_returning_false`

**US3 — URL kwargs override for nested resources:**

- `test_object_url_uses_get_object_url_kwargs`
- `test_collection_url_uses_get_collection_url_kwargs`
- `test_collection_url_uses_empty_kwargs_by_default`
- `test_object_url_excluded_when_object_url_kwargs_is_empty`
- `test_override_get_object_url_kwargs_strips_parent_kwargs`
- `test_override_get_collection_url_kwargs_adds_parent_kwargs`

**US4 — Custom crud_views mapping:**

- `test_custom_crud_views_pattern_used_for_resolution`

**Edge cases:**

- `test_directory_key_always_present_in_context_even_when_empty`
- `test_all_permissions_denied_produces_empty_directory`
- `test_callable_permission_receives_request_user`

---

## Decisions Summary

| Question | Decision |
|---|---|
| Permission attribute names | `has_{action}_permission` must match action names exactly. Rename `has_read_permission` → `has_detail_permission`. Add `has_list_permission = False`. |
| URL kwargs | Two separate override methods: `get_object_url_kwargs()` (was `get_lookup_kwargs()`) and `get_collection_url_kwargs()` returning `{}`. |
| `_OBJECT_ACTIONS` class attr | Remove from class. Keep as module-level frozenset only. |
| `PageObjectMixin` MRO | Remove redundant `ModelInfoMixin` from explicit bases. |
| `MVPModelFormBase.get_lookup_kwargs()` | Rename to `get_object_url_kwargs()`. |
| `MVPUpdateView.get_delete_url()` | Apply `has_delete_permission` gate via `resolve_crud_url`. |
| Test file | `tests/test_views/test_crud_directory_mixin.py` (new file) |
| Demo update | Add a showcase view to the demo app demonstrating `directory` usage. |
