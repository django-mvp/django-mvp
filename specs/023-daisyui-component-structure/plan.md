# Implementation Plan: DaisyUI-Aligned Cotton Component Structure

**Branch**: `023-daisyui-component-structure` | **Date**: 2026-06-09 | **Spec**: [spec.md](spec.md)
**Input**: Test run — reorganize existing cotton components to match DaisyUI 5 documentation structure

## Summary

Reorganize the `mvp/templates/cotton/` directory so that component paths mirror the [DaisyUI 5 component catalog](https://daisyui.com/components/). This makes it trivial to find the corresponding Cotton component when browsing DaisyUI docs. The task is a **rename + restructure** exercise — no class or behavior changes (those belong in `022-daisyui-migration`).

The new structure uses the `c.<category>.<component>` naming convention that cotton supports, matching DaisyUI's own categorization:

```
cotton/
├── alert/index.html          # ← messages.html
├── avatar/
│   ├── index.html
│   └── group.html
├── breadcrumbs/
│   ├── index.html
│   └── item.html
├── button/index.html
├── card/
│   ├── index.html
│   ├── header.html
│   ├── footer.html
│   └── content.html
├── divider.html              # ← layout/divider.html, dropdown/divider.html
├── dock/
│   ├── index.html
│   └── item.html
├── drawer/
│   ├── index.html
│   └── toggle.html
├── dropdown/
│   ├── index.html
│   ├── item.html
│   └── header.html
├── footer.html               # ← app/footer.html
├── hero.html                 # ← mvp/hero.html
├── list/
│   ├── index.html
│   ├── item.html
│   ├── empty.html
│   └── footer.html
├── menu/
│   ├── index.html
│   ├── item.html
│   ├── group.html
│   └── collapse.html
├── modal.html                # ← modal.html, form/modal.html
├── navbar.html               # ← app/header/navbar.html
├── pagination/
│   ├── index.html
│   ├── link.html
│   └── wrapper.html
├── select.html               # ← form/index.html (partial)
├── skeleton/
│   ├── card.html
│   └── grid.html
├── stat.html                 # ← widgets/stat_tile.html
├── steps/
│   ├── index.html
│   └── item.html
├── swap.html                 # ← actions/theme_switcher.html
├── table.html                # ← addons/django_table.html
├── toast.html                # ← messages.html (also maps to alert)
├── toggle.html               # ← card/toggle/*
├── label.html                # ← form/field.html (partial)
├── input.html                # ← form/field.html (partial)
├── join.html                 # ← group.html, row.html, col.html
└── mvp/                     # MVP-specific helpers (keep as-is)
    ├── hero.html             # already here — keep
    └── ...
```

## Technical Context

**Language/Version**: Python 3.12 — Django 5.2
**Primary Dependencies**: django-cotton 2.6.1
**Storage**: N/A — no models or migrations
**Testing**: Visual verification only (this is a test run)
**Target Platform**: Reusable Django library (`mvp/` package)
**Constraints**: No behavior changes, no class changes. Purely structural reorganization. Update all `{% cotton %}` / `<c-...>` references across the codebase.

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Design-First, Verify Implementation | ✅ PASS | Plan documents every file move and reference update |
| II. Documentation-First | ✅ PASS | This plan serves as the documentation |
| III. Component Quality & Accessibility | ✅ PASS | No behavior changes — accessibility preserved |
| IV. Compatibility & Config-Driven | ✅ PASS | Cotton component names change; all references updated |
| V. Tooling & Consistency | ✅ PASS | Follows project conventions |

## Project Structure

### Documentation (this feature)

```text
specs/023-daisyui-component-structure/
├── plan.md              ← this file
```

### Source Code (files changed by this feature)

All changes are within `mvp/templates/cotton/`. The full diff is in Phase 1 below.

## Detailed File Mapping

### DaisyUI Components (moved to DaisyUI-aligned paths)

| # | Current Path | New Path | Cotton Tag | Notes |
|---|---|---|---|---|
| 1 | `cotton/messages.html` | `cotton/alert/index.html` | `<c-alert>` | Primary mapping; toast also possible |
| 2 | `cotton/avatar/index.html` | `cotton/avatar/index.html` | `<c-avatar>` | No change — already aligned |
| 3 | `cotton/avatar/group.html` | `cotton/avatar/group.html` | `<c-avatar.group>` | No change — already aligned |
| 4 | `cotton/button/index.html` | `cotton/button/index.html` | `<c-button>` | No change — already aligned |
| 5 | `cotton/card/index.html` | `cotton/card/index.html` | `<c-card>` | No change — already aligned |
| 6 | `cotton/card/header.html` | `cotton/card/header.html` | `<c-card.header>` | No change — already aligned |
| 7 | `cotton/card/footer.html` | `cotton/card/footer.html` | `<c-card.footer>` | No change — already aligned |
| 8 | `cotton/card/content.html` | `cotton/card/content.html` | `<c-card.content>` | No change — already aligned |
| 9 | `cotton/navigation/breadcrumbs/index.html` | `cotton/breadcrumbs/index.html` | `<c-breadcrumbs>` | Move from navigation/ |
| 10 | `cotton/navigation/breadcrumbs/item.html` | `cotton/breadcrumbs/item.html` | `<c-breadcrumbs.item>` | Move from navigation/ |
| 11 | `cotton/dropdown/index.html` | `cotton/dropdown/index.html` | `<c-dropdown>` | No change — already aligned |
| 12 | `cotton/dropdown/item.html` | `cotton/dropdown/item.html` | `<c-dropdown.item>` | No change — already aligned |
| 13 | `cotton/dropdown/header.html` | `cotton/dropdown/header.html` | `<c-dropdown.header>` | No change — already aligned |
| 14 | `cotton/dropdown/divider.html` | **DELETE** | — | Merge into `divider.html` (see #20) |
| 15 | `cotton/layout/divider.html` | `cotton/divider.html` | `<c-divider>` | Move from layout/ |
| 16 | `cotton/app/footer.html` | `cotton/footer.html` | `<c-footer>` | Move from app/ |
| 17 | `cotton/mvp/hero.html` | `cotton/hero.html` | `<c-hero>` | Move from mvp/ |
| 18 | `cotton/list/index.html` | `cotton/list/index.html` | `<c-list>` | No change — already aligned |
| 19 | `cotton/list/empty.html` | `cotton/list/empty.html` | `<c-list.empty>` | No change — already aligned |
| 20 | `cotton/list/footer.html` | `cotton/list/footer.html` | `<c-list.footer>` | No change — already aligned |
| 21 | `cotton/app/sidebar/menu/index.html` | `cotton/menu/index.html` | `<c-menu>` | Move from app/sidebar/menu/ |
| 22 | `cotton/app/sidebar/menu/item.html` | `cotton/menu/item.html` | `<c-menu.item>` | Move from app/sidebar/menu/ |
| 23 | `cotton/app/sidebar/menu/group.html` | `cotton/menu/group.html` | `<c-menu.group>` | Move from app/sidebar/menu/ |
| 24 | `cotton/app/sidebar/menu/collapse.html` | `cotton/menu/collapse.html` | `<c-menu.collapse>` | Move from app/sidebar/menu/ |
| 25 | `cotton/modal.html` | `cotton/modal.html` | `<c-modal>` | No change — already aligned |
| 26 | `cotton/form/modal.html` | **DELETE** | — | Merge into `modal.html` (see #30) |
| 27 | `cotton/app/header/navbar.html` | `cotton/navbar.html` | `<c-navbar>` | Move from app/header/ |
| 28 | `cotton/navigation/pagination/index.html` | `cotton/pagination/index.html` | `<c-pagination>` | Move from navigation/ |
| 29 | `cotton/navigation/pagination/link.html` | `cotton/pagination/link.html` | `<c-pagination.link>` | Move from navigation/ |
| 30 | `cotton/navigation/pagination/wrapper.html` | `cotton/pagination/wrapper.html` | `<c-pagination.wrapper>` | Move from navigation/ |
| 31 | `cotton/widgets/stat_tile.html` | `cotton/stat.html` | `<c-stat>` | Rename + move from widgets/ |
| 32 | `cotton/navigation/steps/index.html` | `cotton/steps/index.html` | `<c-steps>` | Move from navigation/ |
| 33 | `cotton/navigation/steps/item.html` | `cotton/steps/item.html` | `<c-steps.item>` | Move from navigation/ |
| 34 | `cotton/actions/theme_switcher.html` | `cotton/swap.html` | `<c-swap>` | Rename + move from actions/ |
| 35 | `cotton/addons/django_table.html` | `cotton/table.html` | `<c-table>` | Rename + move from addons/ |
| 36 | `cotton/card/toggle/collapse.html` | **DELETE** | — | Merge into `toggle.html` (see #40) |
| 37 | `cotton/card/toggle/maximize.html` | **DELETE** | — | Merge into `toggle.html` (see #40) |
| 38 | `cotton/card/toggle/remove.html` | **DELETE** | — | Merge into `toggle.html` (see #40) |
| 39 | `cotton/form/field.html` | `cotton/input.html` | `<c-input>` | Rename + move from form/ |
| 40 | `cotton/form/field.html` (label part) | `cotton/label.html` | `<c-label>` | Extract label to new file |
| 41 | `cotton/form/index.html` | `cotton/select.html` | `<c-select>` | Rename + move from form/ |
| 42 | `cotton/placeholder/card.html` | `cotton/skeleton/card.html` | `<c-skeleton.card>` | Move from placeholder/ |
| 43 | `cotton/placeholder/grid.html` | `cotton/skeleton/grid.html` | `<c-skeleton.grid>` | Move from placeholder/ |

### MVP-Specific Components (keep in place, rename to match DaisyUI where applicable)

| # | Current Path | New Path | Cotton Tag | Notes |
|---|---|---|---|---|
| M1 | `cotton/app/index.html` | `cotton/app/index.html` | `<c-app>` | Keep — app wrapper (not in DaisyUI) |
| M2 | `cotton/app/main.html` | `cotton/app/main.html` | `<c-app.main>` | Keep — main content area |
| M3 | `cotton/app/sidebar/index.html` | `cotton/drawer/index.html` | `<c-drawer>` | Move to drawer/ (DaisyUI has "drawer") |
| M4 | `cotton/app/sidebar/toggle.html` | `cotton/drawer/toggle.html` | `<c-drawer.toggle>` | Move with sidebar → drawer |
| M5 | `cotton/app/sidebar/header.html` | **DELETE** | — | Merge into drawer/index.html |
| M6 | `cotton/container.html` | `cotton/container.html` | `<c-container>` | Keep as-is (Tailwind utility, not DaisyUI) |
| M7 | `cotton/grid.html` | `cotton/grid.html` | `<c-grid>` | Keep as-is (Tailwind grid) |
| M8 | `cotton/row.html` | **DELETE** | — | Merge into `join.html` or remove |
| M9 | `cotton/col.html` | **DELETE** | — | Merge into `join.html` or remove |
| M10 | `cotton/group.html` | `cotton/join.html` | `<c-join>` | Rename to match DaisyUI "join" |
| M11 | `cotton/icon.html` | `cotton/icon.html` | `<c-icon>` | Keep as-is (not a DaisyUI component) |
| M12 | `cotton/logo.html` | `cotton/logo.html` | `<c-brand.logo>` | Keep as-is (MVP-specific) |
| M13 | `cotton/text.html` | `cotton/text.html` | `<c-text>` | Keep as-is (MVP-specific) |
| M14 | `cotton/toolbar.html` | `cotton/toolbar.html` | `<c-toolbar>` | Keep as-is (MVP-specific) |
| M15 | `cotton/page/index.html` | `cotton/page/index.html` | `<c-page>` | Keep as-is (MVP-specific) |
| M16 | `cotton/page/content.html` | `cotton/page/content.html` | `<c-page.content>` | Keep as-is (MVP-specific) |
| M17 | `cotton/page/title.html` | `cotton/page/title.html` | `<c-page.title>` | Keep as-is (MVP-specific) |
| M18 | `cotton/page/toolbar.html` | `cotton/page/toolbar.html` | `<c-page.toolbar>` | Keep as-is (MVP-specific) |
| M19 | `cotton/form/card.html` | `cotton/form/card.html` | `<c-form>` | Keep in form/ (MVP layout helper) |
| M20 | `cotton/form/index.html` | **DELETE** | — | Already mapped to select.html (#41) |
| M21 | `cotton/form/render.html` | `cotton/form/render.html` | `<c-form.render>` | Keep in form/ (MVP layout helper) |
| M22 | `cotton/layouts/form_view.html` | `cotton/layouts/form_view.html` | — | Keep as-is (view template) |
| M23 | `cotton/user/sidebar_menu.html` | `cotton/user/sidebar-menu.html` | `<c-user.sidebar-menu>` | Hyphenate for consistency |
| M24 | `cotton/user/display/compact.html` | `cotton/user/display-compact.html` | `<c-user.display-compact>` | Flatten (single file) |
| M25 | `cotton/widgets/type_a.html` | `cotton/widget/type-a.html` | `<c-widget.type-a>` | Rename widgets → widget, hyphenate |
| M26 | `cotton/widgets/type_b.html` | `cotton/widget/type-b.html` | `<c-widget.type-b>` | Rename widgets → widget, hyphenate |
| M27 | `cotton/widgets/type_c.html` | `cotton/widget/type-c.html` | `<c-widget.type-c>` | Rename widgets → widget, hyphenate |
| M28 | `cotton/widgets/type_d.html` | `cotton/widget/type-d.html` | `<c-widget.type-d>` | Rename widgets → widget, hyphenate |
| M29 | `cotton/actions/search.html` | `cotton/action/search.html` | `<c-action.search>` | actions → action (singular) |
| M30 | `cotton/actions/language_switcher.html` | `cotton/action/language-switcher.html` | `<c-action.language-switcher>` | Hyphenate |
| M31 | `cotton/list/search_widget.html` | **DELETE** | — | Merge into list/index.html or remove |
| M32 | `cotton/list/order_widget.html` | **DELETE** | — | Merge into list/index.html or remove |
| M33 | `cotton/list/toolbar.html` | **DELETE** | — | Merge into list/index.html or remove |

### New Components (DaisyUI catalog, not yet implemented)

| # | New Path | Cotton Tag | DaisyUI Source |
|---|---|---|---|
| N1 | `cotton/accordion/index.html` | `<c-accordion>` | DaisyUI accordion |
| N2 | `cotton/badge/index.html` | `<c-badge>` | DaisyUI badge |
| N3 | `cotton/collapse/index.html` | `<c-collapse>` | DaisyUI collapse |
| N4 | `cotton/progress/index.html` | `<c-progress>` | DaisyUI progress |
| N5 | `cotton/textarea/index.html` | `<c-textarea>` | DaisyUI textarea |
| N6 | `cotton/tooltip/index.html` | `<c-tooltip>` | DaisyUI tooltip |

## Implementation Phases

---

### Phase 1 — Move & Rename Files

**Scope**: File system operations only. No code changes inside files.

#### Step 1.1: Create new directory structure

```bash
# DaisyUI-aligned directories
mkdir -p cotton/alert
mkdir -p cotton/breadcrumbs
mkdir -p cotton/divider
mkdir -p cotton/dock
mkdir -p cotton/drawer
mkdir -p cotton/footer
mkdir -p cotton/hero
mkdir -p cotton/menu
mkdir -p cotton/navbar
mkdir -p cotton/pagination
mkdir -p cotton/select
mkdir -p cotton/skeleton
mkdir -p cotton/stat
mkdir -p cotton/steps
mkdir -p cotton/swap
mkdir -p cotton/table
mkdir -p cotton/toggle
mkdir -p cotton/label
mkdir -p cotton/input
mkdir -p cotton/join
mkdir -p cotton/widget
mkdir -p cotton/action
```

#### Step 1.2: Move DaisyUI-mapped files

| From | To |
|---|---|
| `cotton/navigation/breadcrumbs/index.html` | `cotton/breadcrumbs/index.html` |
| `cotton/navigation/breadcrumbs/item.html` | `cotton/breadcrumbs/item.html` |
| `cotton/layout/divider.html` | `cotton/divider.html` |
| `cotton/app/footer.html` | `cotton/footer.html` |
| `cotton/mvp/hero.html` | `cotton/hero.html` |
| `cotton/app/sidebar/menu/index.html` | `cotton/menu/index.html` |
| `cotton/app/sidebar/menu/item.html` | `cotton/menu/item.html` |
| `cotton/app/sidebar/menu/group.html` | `cotton/menu/group.html` |
| `cotton/app/sidebar/menu/collapse.html` | `cotton/menu/collapse.html` |
| `cotton/app/header/navbar.html` | `cotton/navbar.html` |
| `cotton/navigation/pagination/index.html` | `cotton/pagination/index.html` |
| `cotton/navigation/pagination/link.html` | `cotton/pagination/link.html` |
| `cotton/navigation/pagination/wrapper.html` | `cotton/pagination/wrapper.html` |
| `cotton/widgets/stat_tile.html` | `cotton/stat.html` |
| `cotton/navigation/steps/index.html` | `cotton/steps/index.html` |
| `cotton/navigation/steps/item.html` | `cotton/steps/item.html` |
| `cotton/actions/theme_switcher.html` | `cotton/swap.html` |
| `cotton/addons/django_table.html` | `cotton/table.html` |
| `cotton/app/sidebar/index.html` | `cotton/drawer/index.html` |
| `cotton/app/sidebar/toggle.html` | `cotton/drawer/toggle.html` |

#### Step 1.3: Move MVP-specific files

| From | To |
|---|---|
| `cotton/widgets/type_a.html` | `cotton/widget/type-a.html` |
| `cotton/widgets/type_b.html` | `cotton/widget/type-b.html` |
| `cotton/widgets/type_c.html` | `cotton/widget/type-c.html` |
| `cotton/widgets/type_d.html` | `cotton/widget/type-d.html` |
| `cotton/user/sidebar_menu.html` | `cotton/user/sidebar-menu.html` |
| `cotton/user/display/compact.html` | `cotton/user/display-compact.html` |
| `cotton/actions/search.html` | `cotton/action/search.html` |
| `cotton/actions/language_switcher.html` | `cotton/action/language-switcher.html` |

#### Step 1.4: Delete files to be merged/removed

| File | Reason |
|---|---|
| `cotton/dropdown/divider.html` | Merge into `divider.html` |
| `cotton/form/modal.html` | Merge into `modal.html` |
| `cotton/card/toggle/collapse.html` | Merge into `toggle.html` |
| `cotton/card/toggle/maximize.html` | Merge into `toggle.html` |
| `cotton/card/toggle/remove.html` | Merge into `toggle.html` |
| `cotton/app/sidebar/header.html` | Merge into `drawer/index.html` |
| `cotton/row.html` | Merge into `join.html` or remove |
| `cotton/col.html` | Merge into `join.html` or remove |
| `cotton/form/index.html` | Already mapped to select.html |

#### Step 1.5: Rename files (no move needed)

| From | To |
|---|---|
| `cotton/messages.html` | `cotton/alert/index.html` |
| `cotton/group.html` | `cotton/join.html` |
| `cotton/form/field.html` | `cotton/input.html` (+ extract label → `cotton/label.html`) |

---

### Phase 2 — Update Cotton Tags in Templates

**Scope**: Find and replace all `<c-...>` references across the codebase.

#### Step 2.1: Search for all current component references

```bash
# Find every <c- reference in templates
grep -rn '<c-' mvp/templates/ demo/ --include='*.html' | sort
```

#### Step 2.2: Apply tag renames

| Old Tag | New Tag |
|---|---|
| `<c-messages>` | `<c-alert>` |
| `<c-navigation.breadcrumbs>` | `<c-breadcrumbs>` |
| `<c-navigation.breadcrumbs.item>` | `<c-breadcrumbs.item>` |
| `<c-divider>` | `<c-divider>` |
| `<c-dropdown.divider>` | **removed** (merged) |
| `<c-app.footer>` | `<c-footer>` |
| `<c-mvp.hero>` | `<c-hero>` |
| `<c-app.sidebar.menu>` | `<c-menu>` |
| `<c-app.sidebar.menu.item>` | `<c-menu.item>` |
| `<c-app.sidebar.menu.group>` | `<c-menu.group>` |
| `<c-app.sidebar.menu.collapse>` | `<c-menu.collapse>` |
| `<c-app.header.navbar>` | `<c-navbar>` |
| `<c-navigation.pagination>` | `<c-pagination>` |
| `<c-navigation.pagination.link>` | `<c-pagination.link>` |
| `<c-navigation.pagination.wrapper>` | `<c-pagination.wrapper>` |
| `<c-widgets.stat_tile>` | `<c-stat>` |
| `<c-navigation.steps>` | `<c-steps>` |
| `<c-navigation.steps.item>` | `<c-steps.item>` |
| `<c-actions.theme_switcher>` | `<c-swap>` |
| `<c-addons.django_table>` | `<c-table>` |
| `<c-app.sidebar>` | `<c-drawer>` |
| `<c-app.sidebar.toggle>` | `<c-drawer.toggle>` |
| `<c-app.sidebar.header>` | **removed** (merged) |
| `<c-widgets.type_a>` | `<c-widget.type-a>` |
| `<c-widgets.type_b>` | `<c-widget.type-b>` |
| `<c-widgets.type_c>` | `<c-widget.type-c>` |
| `<c-widgets.type_d>` | `<c-widget.type-d>` |
| `<c-user.sidebar_menu>` | `<c-user.sidebar-menu>` |
| `<c-user.display.compact>` | `<c-user.display-compact>` |
| `<c-actions.search>` | `<c-action.search>` |
| `<c-actions.language_switcher>` | `<c-action.language-switcher>` |
| `<c-group>` | `<c-join>` |
| `` | **removed** (merged) |
| `` | **removed** (merged) |
| `<c-form.modal>` | **removed** (merged) |
| `<c-form.index>` | **removed** (merged) |
| `<c-card.toggle.collapse>` | **removed** (merged) |
| `<c-card.toggle.maximize>` | **removed** (merged) |
| `<c-card.toggle.remove>` | **removed** (merged) |

---

### Phase 3 — Update Python Code References

**Scope**: Any Python code that references component paths or names.

#### Step 3.1: Search for component path references in Python

```bash
grep -rn 'cotton/' mvp/ demo/ --include='*.py' | grep -v '__pycache__'
```

#### Step 3.2: Update renderers and menu configs

- `mvp/renderers.py` — update any hardcoded component path strings
- `demo/menus.py`, `dac/menus.py` — update menu renderer references
- Any `render_menu` calls with `renderer="adminlte"` → add `renderer="daisyui"` (deferred to 022)

---

### Phase 4 — Verify & Clean Up

#### Step 4.1: Remove empty directories

```bash
# After all moves are done, clean up empty dirs
rmdir cotton/navigation cotton/layout cotton/app/sidebar cotton/card/toggle cotton/actions cotton/widgets cotton/addons cotton/mvp 2>/dev/null
```

#### Step 4.2: Visual verification

Walk through the demo app pages and verify every component renders correctly with its new tag name.

---

## Complexity Tracking

> No violations — this is a structural reorganization only.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Broken references in templates | Phase 2 does a comprehensive grep → replace pass |
| Broken references in Python code | Phase 3 catches all `.py` references |
| Cotton component name conflicts | Verify no two components share the same tag name after rename |
| Third-party apps referencing old tags | Out of scope for this test run; document breaking changes |
