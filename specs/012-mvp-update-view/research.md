# Research: MVPUpdateView — Phase 0 Findings

**Feature**: `012-mvp-update-view` | **Date**: 2026-05-05

All NEEDS CLARIFICATION items were resolved via direct source inspection.
No external documentation retrieval was required.

---

## Finding 1 — `resolve_crud_url("detail")` is valid

**Question**: Is `"detail"` a recognised key in the CRUD directory, safe to pass to `resolve_crud_url()`?

**Source inspected**: `mvp/config.py`

```python
MVP_DEFAULT_VIEW_NAMES = {
    "list":   "{model_name}-list",
    "detail": "{model_name}-detail",
    "create": "{model_name}-create",
    "update": "{model_name}-update",
    "delete": "{model_name}-delete",
}
```

**Decision**: Use `self.resolve_crud_url("detail")` in `get_breadcrumbs()` — no `ValueError` risk. `CRUDDirectoryMixin._get_view_name()` validates against this dict; "detail" is always present.

**Alternatives considered**: Calling `self.object.get_absolute_url()` directly (current code) — rejected because it bypasses the permissions system (`has_detail_permission`) and raises `AttributeError` if the model does not define `get_absolute_url()`.

---

## Finding 2 — Template delete button gate is `{% if object %}`, not `{% if delete_url %}`

**Question**: Does `form_view.html` already gate the Delete button on the `delete_url` context variable?

**Source inspected**: `mvp/templates/form_view.html` lines 51–57

```html
{% if object %}
  <c-button text="{% trans "Delete" %}"
            href="{{ delete_url }}"
            icon="delete"
            variant="danger" />
{% endif %}
```

**Finding**: The guard is `{% if object %}`. For `MVPUpdateView`, `object` is always set during rendering, so the Delete button always appears regardless of whether `delete_url` is an empty string.

**Decision**: Change the guard to `{% if delete_url %}`. This correctly hides the button when `get_delete_url()` returns `""` (no delete view registered / no permission), and shows it when a valid URL was built. This is a bug fix, not a new feature.

**Alternatives considered**: Keeping `{% if object and delete_url %}` — rejected as redundant; when `delete_url` is truthy, `object` is always set on an update view.

---

## Finding 3 — Breadcrumb degradation is fully automatic

**Question**: Does the Cotton breadcrumbs component handle `None`/empty-string `href` values automatically, or does `get_breadcrumbs()` need a Python guard?

**Source inspected**: `django-cotton-bs5` breadcrumbs component (used in `PageObjectMixin`) — confirmed by prior 011 plan research and `href|yesno:"a,span"` pattern.

**Decision**: No Python guard needed in `get_breadcrumbs()`. Passing the result of `resolve_crud_url("detail")` directly as `href` is sufficient — the component renders a `<span>` when `href` is falsy and an `<a>` when it is truthy.

---

## Finding 4 — `MVPModelFormBase.get_page_title()` handles interpolation

**Question**: Does `MVPUpdateView` need to override `get_page_title()` to produce a model-aware title?

**Source inspected**: `mvp/views/edit.py` — `MVPModelFormBase.get_page_title()`:

```python
def get_page_title(self) -> str:
    if not self.page_title:
        return self.page_title
    return self.page_title % {"verbose_name": self.model_meta.verbose_name.title()}
```

**Decision**: No override needed. Set `page_title = _("Update %(verbose_name)s")` on the class; the base method interpolates it at request time. Same pattern confirmed working for `MVPCreateView`.

---

## Finding 5 — Existing test coverage for delete URL params

**Question**: Do tests for `get_delete_url()` back/next params already exist?

**Source inspected**: `tests/test_views/test_delete_view.py` — `TestMVPUpdateViewDeleteUrl` (3 tests covering `?back` and `?next` params).

**Decision**: Do not duplicate. New tests cover page title, breadcrumb structure, and delete-link visibility gate only.

---

## Finding 6 — `make_update_view()` fixture helper already exists

**Question**: Is there a fixture helper for building `MVPUpdateView` stubs in unit tests?

**Source inspected**: `tests/test_views/test_edit_view.py` lines 82–112.

**Decision**: Reuse `make_update_view()` directly in new test classes.

---

## Resolved Unknowns Summary

| Unknown | Resolution |
|---------|-----------|
| `resolve_crud_url("detail")` safety | ✅ Safe — "detail" is in `MVP_DEFAULT_VIEW_NAMES` |
| Template gate for Delete button | ✅ Bug found — guard is `{% if object %}`; fix to `{% if delete_url %}` |
| Breadcrumb `None` href handling | ✅ Automatic via Cotton component |
| `get_page_title()` override needed? | ✅ No — base class handles interpolation |
| Existing delete-URL test coverage | ✅ Already in `test_delete_view.py` — do not duplicate |
| `make_update_view()` fixture helper | ✅ Already exists in `test_edit_view.py` |
