# Sidebar Menu Patterns

## Flat Menu (7 items or fewer)

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu

AppMenu.extend([
    MenuItem("name", view_name="url_name",
             extra_context={"label": "Display Label", "icon": "icon-name"}),
])
```

## Grouped Menu (MenuGroup — section headers)

`MenuGroup` renders as a non-clickable uppercase section header:

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuGroup

AppMenu.extend([
    MenuGroup("tracking", children=[
        MenuItem("episodes", view_name="episode-list",
                 extra_context={"label": "Episodes", "icon": "journal-text"}),
        MenuItem("dashboard", view_name="home",
                 extra_context={"label": "Dashboard", "icon": "speedometer2"}),
    ], extra_context={"label": "Tracking"}),
])
```

## Collapsible Menu (MenuCollapse — treeview)

`MenuCollapse` renders as a collapsible parent with AdminLTE treeview behaviour:

```python
from mvp.menus import AppMenu, MenuCollapse
from flex_menu import MenuItem

AppMenu.extend([
    MenuCollapse("reports", children=[
        MenuItem("analytics", view_name="analytics",
                 extra_context={"label": "Analytics", "icon": "graph-up"}),
        MenuItem("export", view_name="export",
                 extra_context={"label": "Export", "icon": "download"}),
    ], extra_context={"label": "Reports", "icon": "bar-chart"}),
])
```

## Visibility Checks

```python
from flex_menu.checks import (
    user_is_authenticated,
    user_is_staff,
    user_is_superuser,
    user_in_any_group,
    user_has_any_permission,
)

# Show only to authenticated users
MenuItem("dashboard", view_name="home", check=user_is_authenticated, ...)

# Show only to staff
MenuItem("admin_panel", view_name="admin", check=user_is_staff, ...)

# Custom callable check
MenuItem("beta_feature", view_name="beta",
         check=lambda request, **kwargs: request.user.profile.is_beta_tester,
         ...)
```

## Badge / Count Indicator

Pass badge data via `extra_context`:

```python
MenuItem("inbox", view_name="inbox",
         extra_context={"label": "Inbox", "icon": "envelope", "badge": "5",
                        "badge_classes": "badge bg-danger"})
```

The sidebar item template renders `{{ badge }}` with `{{ badge_classes }}` if present.

## Active State

Active state is **automatic** — the `AdminLTERenderer` performs an exact path match
(`request.path == item.url`). No manual work needed. The `.active` CSS class is applied 
by `<c-app.sidebar.menu.item>` when `selected=True`.

For prefix-based matching (e.g., highlight "Episodes" for any URL starting with `/episodes/`),
the built-in renderer doesn't support it. Workaround: set `check` to a custom callable
that compares `request.path.startswith(prefix)` and expose via `extra_context`.

## Menu Autodiscovery

`FlexMenuConfig.ready()` calls `autodiscover_modules("menus")` then
`warm_url_params_cache()`. You do NOT need to:
- Import `menus.py` anywhere
- Override `ready()` in your app's `AppConfig`
- Manually trigger menu loading

Just ensure:
1. The app is in `INSTALLED_APPS`
2. `menus.py` exists at the app root
3. `AppMenu.extend([...])` is called at module level (not inside a function/class)
