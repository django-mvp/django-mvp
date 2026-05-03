# Quickstart: CRUD Directory Mixin

**Branch**: `006-crud-directory-mixin` | **Date**: 2026-05-03
**Audience**: Developers building views with `django-mvp`

---

## Overview

`CRUDDirectoryMixin` removes all URL wiring boilerplate from model-driven views. Declare which CRUD actions you want available, set a permission flag per action, and the mixin resolves the correct URLs automatically. Templates use the presence or absence of a `{action}_url` key in the `directory` context variable to conditionally render action buttons and navigation links.

---

## 1. Basic Usage — Flat URL Structure

For a standard single-resource URL structure (e.g. `/products/`, `/products/<pk>/`, etc.) that follows the default `{model_name}-{action}` naming convention:

```python
# views.py
from mvp.views import MVPDetailView

class ProductDetailView(MVPDetailView):
    model = Product

    # Declare which actions to resolve
    directory = ["list", "detail", "update", "delete"]

    # Grant permissions (all denied by default)
    has_list_permission = True
    has_detail_permission = True
    has_update_permission = True
    has_delete_permission = True
```

```python
# urls.py
urlpatterns = [
    path("products/",              ProductListView.as_view(),   name="product-list"),
    path("products/<int:pk>/",     ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product-update"),
    path("products/<int:pk>/del/",  ProductDeleteView.as_view(), name="product-delete"),
]
```

In the template:

```html
{% if directory.update_url %}
  <a href="{{ directory.update_url }}" class="btn btn-primary">Edit</a>
{% endif %}

{% if directory.delete_url %}
  <a href="{{ directory.delete_url }}" class="btn btn-danger">Delete</a>
{% endif %}

{% if directory.list_url %}
  <a href="{{ directory.list_url }}">&larr; Back to list</a>
{% endif %}
```

The `directory` context key is **always present** — even when all permissions are denied, it is an empty dict. Templates can rely on `{% if directory.update_url %}` without a fallback.

---

## 2. Permission-Based Gating

Permissions default to `False` for all five actions. Enable only what the view should expose:

```python
class ProductUpdateView(MVPUpdateView):
    model = Product
    directory = ["list", "delete"]

    # Only list and delete URLs will appear in the directory
    has_list_permission = True
    has_delete_permission = True
    # has_update_permission not set → update_url absent from directory
```

### Callable permissions

For dynamic permission logic (e.g. staff-only access), use a callable. The callable receives `request.user` as its sole argument:

```python
class ProductUpdateView(MVPUpdateView):
    model = Product
    directory = ["list", "delete"]

    has_list_permission = True

    @staticmethod
    def has_delete_permission(user):
        return user.is_staff
```

---

## 3. Custom URL Naming Convention

If your project does not follow the `{model_name}-{action}` convention, override `crud_views`:

```python
class ProductDetailView(MVPDetailView):
    model = Product
    directory = ["list", "update"]
    has_list_permission = True
    has_update_permission = True

    crud_views = {
        "list":   "catalogue:{model_name}-index",
        "detail": "catalogue:{model_name}-view",
        "update": "catalogue:{model_name}-modify",
        "create": "catalogue:{model_name}-new",
        "delete": "catalogue:{model_name}-remove",
    }
```

Both `{model_name}` and `{app_name}` substitution tokens are supported.

---

## 4. Nested URL Patterns

For nested resources (e.g. `/projects/<project_pk>/tasks/<pk>/`), override `get_url_kwargs(action)` and branch on the action name to control which kwargs are forwarded:

```python
class TaskUpdateView(MVPUpdateView):
    model = Task
    directory = ["list", "detail", "update", "delete"]
    has_list_permission = True
    has_detail_permission = True
    has_update_permission = True
    has_delete_permission = True

    def get_url_kwargs(self, action: str) -> dict | None:
        project_pk = self.kwargs["project_pk"]
        if action in {"list", "create"}:
            # Collection-level URLs only need the parent identifier
            return {"project_pk": project_pk}
        pk = self.kwargs.get("pk")
        if pk is None:
            return None  # suppress silently if no object in scope
        return {"project_pk": project_pk, "pk": pk}
```

```python
# urls.py
urlpatterns = [
    path("projects/<int:project_pk>/tasks/",
         TaskListView.as_view(), name="task-list"),
    path("projects/<int:project_pk>/tasks/<int:pk>/",
         TaskDetailView.as_view(), name="task-detail"),
    path("projects/<int:project_pk>/tasks/<int:pk>/edit/",
         TaskUpdateView.as_view(), name="task-update"),
    path("projects/<int:project_pk>/tasks/<int:pk>/del/",
         TaskDeleteView.as_view(), name="task-delete"),
]
```

---

## 5. Using on a List View

`CRUDDirectoryMixin` is included in `MVPListViewMixin`. On a list view, object-level actions (`detail`, `update`, `delete`) are automatically suppressed (no object in scope), so only `list` and `create` URLs can appear:

```python
class ProductListView(MVPListViewMixin, ListView):
    model = Product
    directory = ["create"]
    has_create_permission = True  # "Add Product" button appears in toolbar
```

Object-level URLs (`detail_url`, `update_url`, `delete_url`) are generated **per-item** directly in list item templates (e.g., using `object.get_absolute_url()`), not via the directory.

---

## 6. How URL Resolution Works (Reference)

For each action in `directory`:

1. Look up the URL name pattern in `crud_views` and format it with `model_name` and `app_name`.
2. Check the `has_{action}_permission` attribute:
   - Missing → exclude
   - `False` → exclude
   - `True` → include
   - Callable → call with `request.user`; include if result is truthy
3. Call `get_url_kwargs(action)` to get the URL kwargs:
   - Returns `None` → exclude silently (no reversal attempted)
   - Returns `{}` → reverse with no kwargs
   - Returns non-empty dict → reverse with those kwargs
4. Call `reverse(url_name, kwargs=<resolved kwargs>)`.
5. Store as `directory["{action}_url"]`.

---

## 7. Default URL Name Convention

The default `crud_views` mapping (settable globally via `MVP_DEFAULT_VIEW_NAMES`):

| Action | Default URL name pattern | Example (model: `product`) |
|---|---|---|
| `list` | `{model_name}-list` | `product-list` |
| `detail` | `{model_name}-detail` | `product-detail` |
| `create` | `{model_name}-create` | `product-create` |
| `update` | `{model_name}-update` | `product-update` |
| `delete` | `{model_name}-delete` | `product-delete` |
