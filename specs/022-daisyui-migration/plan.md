# Implementation Plan: AdminLTE 4 → DaisyUI 5 Migration

**Branch**: `022-daisyui-migration` | **Date**: 2026-06-03
**Goal**: Methodically replace AdminLTE 4 + Bootstrap 5 with DaisyUI 5 + Tailwind CSS (CDN-first)

---

## Executive Summary

AdminLTE 4 is infrequently updated, couples layout and component CSS tightly to Bootstrap 5, and
requires a compiled SCSS build pipeline via `django-compressor`. DaisyUI 5 + Tailwind CSS browser
CDN is actively maintained, delivers 35+ built-in themes, requires zero build tooling for initial
adoption, and maps cleanly to the existing Cotton component hierarchy.

The migration is structured in **six sequential phases**. Each phase can be committed and reviewed
independently. Phases 1–2 are the critical path (layout shell). Phases 3–5 refine individual
components. Phase 6 cleans up dead code.

---

## CDN Snippet (replace AdminLTE CDN)

```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
```

> DaisyUI 5 uses Tailwind CSS v4. The `@tailwindcss/browser` script compiles Tailwind utilities
> from `class="..."` attributes at runtime — no `tailwind.config.js` needed in CDN mode.
> Alpine JS stays; Bootstrap 5 JS and AdminLTE JS are removed entirely.

---

## Dependency Map: What Goes, What Stays

| Dependency | Current role | Action |
|---|---|---|
| `adminlte.min.css` (compiled SCSS) | Layout + component styles | **REMOVE** — replaced by DaisyUI CDN |
| `adminlte.min.js` | Sidebar toggle, dropdowns | **REMOVE** — replaced by checkbox drawer + Alpine JS |
| `bootstrap@5.3.x` JS bundle (CDN) | Modals, dropdowns, alerts | **REMOVE** — DaisyUI uses `<dialog>`, no JS needed |
| `mvp.scss` / `mvp-layout.scss` | Custom overrides | **REMOVE** — rewrite as Tailwind utility classes |
| `django-compressor` CSS blocks | SCSS compilation | **REMOVE** blocks from `base.html` (keep dep if used elsewhere) |
| `overlayscrollbars` (CDN) | Sidebar scrollbars | **REMOVE** — `overflow-y-auto` from Tailwind is sufficient |
| `@fontsource/source-sans-3` (CDN) | Body font | **KEEP or SWAP** — DaisyUI sets `font-sans`; drop or swap to system font |
| `bootstrap-icons` (CDN) | Icons throughout | **KEEP** — DaisyUI is icon-agnostic |
| `alpinejs@3` (CDN) | Reactive state, sidebar collapse | **KEEP** — drives sidebar toggle state |
| `@alpinejs/persist` | Sidebar state across reloads | **KEEP** — store `data-theme` + sidebar state |
| `@alpinejs/sort` | Sortable lists | **KEEP** |
| `js/navbar/theme-switcher.js` | FOUC-free theme restore | **REWRITE** — switch from `data-bs-theme` to `data-theme` (DaisyUI) |
| `js/sidebar-toggle.js` | AdminLTE sidebar toggle | **REMOVE** — drawer checkbox handles toggle |
| `js/page-layout.js` | Page layout tweaks | **REMOVE** — no longer needed |
| `js/list_view.js` | List view JS | **REVIEW** — may have Bootstrap modal references |
| `django-flex-menus` / `AdminLTERenderer` | Menu rendering | **KEEP dep** — write new `DaisyUIRenderer` |

---

## Key AdminLTE → DaisyUI Class Mapping

### Layout shell

| AdminLTE / Bootstrap | DaisyUI / Tailwind |
|---|---|
| Body: `layout-fixed sidebar-mini sidebar-expand-lg` | `<div class="drawer lg:drawer-open">` |
| `app-wrapper` div | `drawer` root element |
| Sidebar: `app-sidebar bg-body-secondary sticky-top` | `drawer-side` → `<aside class="bg-base-200 min-h-screen w-64">` |
| Main area: `app-main` | `drawer-content flex flex-col min-h-screen` |
| Header: `app-header sticky-top` | `sticky top-0 z-50` on navbar |
| Footer: `app-footer` | `footer` with Tailwind spacing |
| Mobile overlay: `.sidebar-overlay` | `drawer-overlay` (`<label for="drawer-toggle">`) |
| Toggle: `data-lte-toggle="sidebar"` | `<label for="drawer-toggle">` |

### Navbar

| Bootstrap | DaisyUI |
|---|---|
| `navbar bg-{variant}` | `navbar bg-base-100 shadow` |
| `navbar-brand` | `navbar-start` → logo/brand link |
| `d-inline-flex` toolbar | `navbar-start`, `navbar-center`, `navbar-end` |

### Components

| Bootstrap / AdminLTE | DaisyUI |
|---|---|
| `card card-outline` | `card bg-base-100 shadow` |
| `card-body`, `card-title` | `card-body`, `card-title` (same names) |
| `text-bg-primary` | `bg-primary text-primary-content` |
| `alert alert-danger` | `alert alert-error` |
| `alert alert-success` | `alert alert-success` |
| Bootstrap modal (`data-bs-toggle`) | DaisyUI `<dialog class="modal">` + `showModal()` |
| `btn btn-primary` | `btn btn-primary` (same) |
| `btn btn-outline-secondary` | `btn btn-outline btn-secondary` |
| `form-control` | `input` (DaisyUI) or `input w-full` |
| `form-label` | `label` with `fieldset` or standalone |
| `form-check-input` | `checkbox` |
| `form-select` | `select` |
| `row` + `col-md-6` | `grid grid-cols-2 gap-4` (Tailwind) |
| `container-fluid` | `w-full px-4` or Tailwind `container` |
| `d-flex` | `flex` |
| `d-none` | `hidden` |
| `justify-content-between` | `justify-between` |
| `sticky-top` | `sticky top-0` |
| `text-muted` | `text-base-content/60` |
| `fw-bold` | `font-bold` |

### Theme switching

| AdminLTE / Bootstrap | DaisyUI |
|---|---|
| `data-bs-theme="dark"` on `<html>` | `data-theme="dark"` on `<html>` |
| `data-bs-theme="light"` | `data-theme="light"` |
| JS: `document.documentElement.setAttribute('data-bs-theme', ...)` | `document.documentElement.setAttribute('data-theme', ...)` |

---

## Phase 1 — `base.html` (Critical Path)

**Files**: `mvp/templates/mvp/base.html`, `mvp/static/js/navbar/theme-switcher.js`

### 1.1 Head section

- **Remove**: Source Sans 3 font CDN (use system font or keep — lowest priority)
- **Remove**: OverlayScrollbars CSS CDN
- **Remove**: `{% compress css %}` block with `mvp-layout.scss` + `mvp.scss`
- **Add**: DaisyUI CSS CDN link
- **Add**: Tailwind browser script tag
- **Keep**: Bootstrap Icons CDN link
- **Keep**: Alpine JS CDN links (all three: persist, sort, core)
- **Keep**: viewport meta, charset, title, favicon blocks

### 1.2 FOUC prevention / theme script

Rewrite the inline `<script>` at top of `<head>` and `theme-switcher.js`:

```js
// Restore DaisyUI theme from localStorage before first paint
(function () {
  const theme = localStorage.getItem('mvp.theme') || 'light';
  document.documentElement.setAttribute('data-theme', theme);
})();
```

`theme-switcher.js` rewrite — remove all `data-bs-theme` references, use `data-theme` instead.

### 1.3 Body / JS section

- **Remove**: `<script src="bootstrap.bundle.min.js">` CDN tag
- **Remove**: `<script src="{% static 'js/adminlte.min.js' %}">`
- **Remove**: `<script src="{% static 'js/page-layout.js' %}">`
- **Keep**: `{% block extra_js %}` (if present) or add it for downstream use
- **Keep**: Alpine JS (already in head as defer)

### 1.4 `<c-app>` props

The `fixed-footer` prop drives AdminLTE-specific body classes. After Phase 2 rewrites the
`c-app` component, this prop can be repurposed or removed.

---

## Phase 2 — `app/` Cotton Components (Layout Shell)

These five components define the entire page chrome. Rewrite them together as a unit since
they are tightly coupled.

### 2.1 `cotton/app/index.html` (`c-app`)

**Current**: Sets AdminLTE body classes (`layout-fixed`, `sidebar-mini`, etc.) on `<body>`.

**New structure**:

```html
<body data-theme="{{ theme|default:'light' }}" {{ attrs }}>
  <div class="drawer lg:drawer-open">
    <input id="drawer-toggle" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col min-h-screen">
      {{ slot }}  {# header, main, footer #}
    </div>
    <div class="drawer-side z-50">
      <label for="drawer-toggle" aria-label="close sidebar" class="drawer-overlay"></label>
      {{ sidebar_slot }}  {# rendered by c-app.sidebar #}
    </div>
  </div>
  {{ modals }}
</body>
```

**Key design decisions**:

- `lg:drawer-open` keeps the sidebar always-visible on large screens (mirrors `sidebar-expand-lg`)
- The `drawer-toggle` checkbox replaces `data-lte-toggle="sidebar"` JS hook
- Sidebar state persistence (collapsed/expanded) on desktop handled via Alpine `$persist`

### 2.2 `cotton/app/header.html` (`c-app.header`)

**Current**: Bootstrap `navbar bg-{variant}` inside `.app-header.sticky-top`.

**New structure**:

```html
<div class="sticky top-0 z-40 w-full">
  <div class="navbar bg-base-100 shadow-sm">
    <div class="navbar-start">
      {# Hamburger — only visible on mobile (lg:hidden) #}
      <label for="drawer-toggle" class="btn btn-ghost btn-square lg:hidden">
        <i class="bi bi-list text-xl"></i>
      </label>
      {# Brand logo — shown on mobile only (hidden on lg where sidebar has it) #}
      <a class="navbar-brand lg:hidden" href="/"><c-brand.logo max-height="1.5rem" /></a>
    </div>
    <div class="navbar-end gap-1">
      {{ right }}
    </div>
  </div>
  {% if tray %}<div class="bg-base-200 px-4 py-1">{{ tray }}</div>{% endif %}
</div>
```

### 2.3 `cotton/app/sidebar/index.html` (`c-app.sidebar`)

**Current**: `<aside class="app-sidebar bg-body-secondary shadow ...">` with AdminLTE structure.

**New structure**:

```html
<aside class="bg-base-200 min-h-screen w-64 {{ class }}">
  {# Brand header #}
  <div class="sticky top-0 bg-base-200 px-4 py-3 border-b border-base-300">
    <a href="{{ brand_url }}" class="flex items-center gap-2">
      <c-brand.logo max-height="1.5rem" />
      {% if brand_text %}<span class="font-semibold text-base-content">{{ brand_text }}</span>{% endif %}
    </a>
  </div>
  {# Navigation #}
  <nav class="p-2">
    {% render_menu menu renderer="daisyui" %}
  </nav>
  {# User footer #}
  {% if request.user.is_authenticated %}
    <div class="sticky bottom-0 bg-base-200 border-t border-base-300 p-2 mt-auto">
      <c-user.sidebar-menu />
    </div>
  {% endif %}
</aside>
```

**Note**: `renderer="daisyui"` — requires Phase 4 (new menu renderer).

### 2.4 `cotton/app/main.html` (`c-app.main`)

**Current**: `<main class="app-main pb-0">{{ slot }}</main>`

**New**:

```html
<main class="flex-1 p-4 bg-base-200">{{ slot }}</main>
```

### 2.5 `cotton/app/footer.html` (`c-app.footer`)

Replace AdminLTE `.app-footer` with:

```html
<footer class="footer footer-center bg-base-100 border-t border-base-300 py-3 text-base-content/60 text-sm">
  {{ slot }}
</footer>
```

---

## Phase 3 — UI Cotton Components

Work through these in dependency order (most-used first). Each component gets its own commit.

### 3.1 `cotton/card/` — `c-card`

| File | Change |
|---|---|
| `card/index.html` | Replace `card card-outline card-{{ variant }}` → `card bg-base-100 shadow-sm` |
| `card/header.html` | Replace `card-header` Bootstrap pattern → `card-title` inside body or custom header div |
| `card/body.html` | Replace Bootstrap padding classes → `card-body` (DaisyUI already uses this name) |
| `card/footer.html` | Replace Bootstrap `card-footer` → plain `div` with `border-t border-base-300 p-4` |

**Variant mapping**:

- `variant="primary"` → add `bg-primary text-primary-content` to card
- `variant="default"` → `bg-base-100` (default)
- `fill="outline"` → `card-border` (DaisyUI 5) or `border border-base-300`

### 3.2 `cotton/messages.html` — `c-messages`

**Current**: Bootstrap `.alert.alert-{variant}` with Bootstrap JS auto-dismiss.

**New**: DaisyUI `alert` classes + Alpine JS for dismiss/animate:

```html
<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80" ...>
  {% for message in messages %}
    <div role="alert" class="alert alert-{{ message.tags|daisyui_alert_class }} shadow-lg"
         x-data="{ show: true }" x-show="show" x-transition ...>
      <span>{{ message }}</span>
      {% if dismissible %}
        <button @click="show = false" class="btn btn-ghost btn-xs btn-circle">✕</button>
      {% endif %}
    </div>
  {% endfor %}
</div>
```

**Tag mapping** (needs template filter or inline mapping):

- `error` → `alert-error`
- `success` → `alert-success`
- `warning` → `alert-warning`
- `info` → `alert-info`
- `debug` → `alert-info`

**Auto-dismiss**: replace Bootstrap `Alert.getOrCreateInstance(el).close()` with Alpine
`setTimeout(() => show = false, {{ delay }})`.

### 3.3 `cotton/toolbar.html` — `c-toolbar`

Replace Bootstrap spacing/flex utilities with Tailwind equivalents:

- `w-100` → `w-full`
- `justify-content-between` → `justify-between`
- `d-flex` → `flex`
- `mb-2` → `mb-2` (same — Tailwind and Bootstrap use identical names for common spacing)
- Remove `.toolbar-row-{breakpoint}` custom classes → use `flex-col sm:flex-row` pattern

### 3.4 `cotton/form/field.html` — form fields

Replace Bootstrap form classes with DaisyUI equivalents:

- `form-control` (input) → `input w-full` (DaisyUI input)
- `form-label` → `label` inside `fieldset` or standalone
- `form-check-input` → `checkbox`
- `form-select` → `select`
- `form-text` (help text) → `<p class="text-base-content/60 text-sm">`
- `is-invalid` → `input-error` / `select-error`
- Error feedback `invalid-feedback` → `<p class="text-error text-sm">`

### 3.5 Modals — `cotton/addons/modal.html` (if exists) or inline `<c-modal>`

**Current**: Bootstrap 5 `<div class="modal fade ...">` with `data-bs-toggle="modal"`.

**New**: DaisyUI `<dialog class="modal">` method (recommended — native, accessible, Esc key):

```html
{# Trigger #}
<button onclick="my_modal.showModal()" class="btn btn-primary">Open</button>

{# Modal #}
<dialog id="my_modal" class="modal">
  <div class="modal-box">
    <h3 class="text-lg font-bold">{{ title }}</h3>
    {{ slot }}
    <div class="modal-action">
      <form method="dialog"><button class="btn">Close</button></form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
```

**Impact on `021-list-inline-create`**: The inline create modal uses Bootstrap JS. After this
phase, `list_view.html` must be updated to use the DaisyUI `<dialog>` approach. The `showModal()`
call can be triggered via Alpine JS or a plain `onclick`.

### 3.6 `cotton/container.html`, `cotton/row.html`, `cotton/col.html`

Bootstrap grid → Tailwind CSS grid/flex. These are used for page layout only.

- `container` → `container mx-auto px-4`
- `container-fluid` → `w-full px-4`
- `row` + `col-md-6` → `grid grid-cols-1 md:grid-cols-2 gap-4`
- `row-cols-3` → `grid grid-cols-3`

Consider simplifying: the existing `row`/`col` components have many Bootstrap-specific props
(`row-cols-{n}`, `g-{n}`, `col-{breakpoint}-{n}`). Replace with a simpler Tailwind-native
`<c-grid cols="2" gap="4">` interface backed by Tailwind classes.

### 3.7 `cotton/adminlte/` specific components

| Component | Action |
|---|---|
| `adminlte/small_box.html` | Rewrite with DaisyUI `stat` component |
| `adminlte/callout.html` | Rewrite with DaisyUI `alert` |
| `adminlte/direct_chat.html` | Rewrite with DaisyUI `chat` component |
| `adminlte/timeline.html` | Rewrite with DaisyUI `timeline` component |

These are lower priority and can be deferred to a separate sub-phase or feature branch.

### 3.8 `cotton/widgets/` — `stat_tile`, `type_a`–`type_d`

Rewrite using DaisyUI `stat` + `card` components. Lower priority.

---

## Phase 4 — DaisyUI Menu Renderer

**Files**: `mvp/renderers.py`, new renderer class `DaisyUIRenderer`

The current `AdminLTERenderer` generates AdminLTE-specific HTML for `django-flex-menus`.
A new `DaisyUIRenderer` must generate DaisyUI `menu` markup:

```html
<ul class="menu menu-vertical gap-0.5">
  <li class="menu-title">{{ group.label }}</li>
  <li>
    <a href="{{ item.url }}" class="{% if item.active %}active{% endif %}">
      {% if item.icon %}<i class="bi bi-{{ item.icon }}"></i>{% endif %}
      {{ item.label }}
    </a>
  </li>
  <li>
    <details {% if item.open %}open{% endif %}>
      <summary>{{ collapse.label }}</summary>
      <ul>...</ul>
    </details>
  </li>
</ul>
```

**DaisyUI menu classes**:

- `menu menu-vertical` — vertical navigation list
- `menu-title` — section header (replaces `MenuGroup`)
- `active` modifier on `<a>` — active/current page
- `details`/`summary` pattern — collapsible groups (replaces `MenuCollapse`)
- `menu-xs`, `menu-sm`, `menu-lg` — size variants

**Steps**:

1. Create `DaisyUIRenderer` class in `renderers.py`
2. Register renderer in `render_menu` call: `renderer="daisyui"`
3. Update `app/sidebar/index.html` renderer reference (done in Phase 2.3)
4. Verify `MobileFooterNavRenderer` — update or replace for DaisyUI

---

## Phase 5 — Static Files & Build Pipeline Cleanup

After all component rewrites are complete and visually verified:

### 5.1 Remove AdminLTE static files

```text
mvp/static/
├── css/adminlte.min.css    → DELETE
├── js/adminlte.min.js      → DELETE
├── js/page-layout.js       → DELETE
├── js/sidebar-toggle.js    → DELETE
└── scss/                   → DELETE entire directory (AdminLTE + Bootstrap SCSS)
```

### 5.2 Simplify `django-compressor` usage

Remove `{% compress css %}` block from `base.html` (already done in Phase 1).
Evaluate whether `django-compressor` is still needed for anything else; if not, remove from
`INSTALLED_APPS` and `pyproject.toml`.

### 5.3 Update `pyproject.toml` optional dependencies

Remove `libsass` / `django-compressor` from requirements if no longer used.

---

## Phase 6 — Testing & Visual Verification

### 6.1 Playwright visual verification (per phase)

After each phase, run the Playwright CLI to verify the layout:

- Sidebar opens/closes on mobile (drawer checkbox)
- Sidebar is always visible on desktop (`lg:drawer-open`)
- Theme switch persists across page reloads
- Navbar renders correctly at all breakpoints
- Cards, forms, modals render correctly

### 6.2 Unit test updates

Files likely affected by class name changes:

- Any test asserting `card`, `modal`, `navbar` HTML structure
- Tests checking for `btn-outline-secondary` → `btn-outline btn-secondary`
- Tests checking for `alert-danger` → `alert-error`

Run full test suite after each phase: `poetry run pytest`

### 6.3 Demo app visual review

The `demo/` app exercises most components. After Phase 3, walk through all demo pages:

- Dashboard
- List views (with inline create modal)
- Form views
- Detail views
- Error pages (404, 500)

---

## Phase Execution Order & Commit Strategy

| # | Phase | Commits | Risk |
|---|---|---|---|
| 1 | `base.html` + `theme-switcher.js` | 1 | Medium — FOUC risk if script order wrong |
| 2 | `app/` Cotton components (layout shell) | 1–2 | High — whole page layout changes |
| 3 | UI components (card, messages, form, modal, grid) | 1 per sub-component | Medium — component by component |
| 4 | DaisyUI menu renderer | 1 | Medium — menu rendering logic |
| 5 | Static file cleanup + build pipeline | 1 | Low — just deletes |
| 6 | Tests + Playwright verification | Per phase | Low |

**Recommended**: Complete Phases 1–2 as a single PR (the layout must work end-to-end before
individual components can be meaningfully tested). Then land Phases 3–5 as a series of
focused PRs, one per component group.

---

## File Change Inventory

```text
mvp/templates/mvp/
└── base.html                              # Phase 1 — CDN swap, theme script

mvp/static/js/navbar/
└── theme-switcher.js                      # Phase 1 — rewrite for data-theme

mvp/templates/cotton/app/
├── index.html                             # Phase 2 — drawer layout
├── header.html                            # Phase 2 — DaisyUI navbar
├── sidebar/index.html                     # Phase 2 — drawer-side
├── sidebar/header.html                    # Phase 2 — brand header
├── main.html                              # Phase 2 — drawer-content
└── footer.html                            # Phase 2 — footer update

mvp/templates/cotton/
├── card/index.html                        # Phase 3.1
├── card/header.html                       # Phase 3.1
├── card/body.html                         # Phase 3.1
├── card/footer.html                       # Phase 3.1
├── messages.html                          # Phase 3.2
├── toolbar.html                           # Phase 3.3
├── form/field.html                        # Phase 3.4
├── addons/modal.html (if exists)          # Phase 3.5
├── container.html                         # Phase 3.6
├── row.html                               # Phase 3.6
├── col.html                               # Phase 3.6
├── adminlte/small_box.html                # Phase 3.7
├── adminlte/callout.html                  # Phase 3.7
├── adminlte/direct_chat.html             # Phase 3.7
└── adminlte/timeline.html                 # Phase 3.7

mvp/renderers.py                           # Phase 4 — new DaisyUIRenderer

mvp/static/css/adminlte.min.css            # Phase 5 — DELETE
mvp/static/js/adminlte.min.js             # Phase 5 — DELETE
mvp/static/js/page-layout.js              # Phase 5 — DELETE
mvp/static/js/sidebar-toggle.js           # Phase 5 — DELETE
mvp/static/scss/                           # Phase 5 — DELETE directory

mvp/templates/list_view.html               # Phase 3.5 — modal update (021 feature compat)
```

---

## Open Questions / Risks

1. **`django-compressor` removal**: Verify no other apps in the project use SCSS compilation
   via compressor before removing it.

2. **Bootstrap Icons**: DaisyUI is icon-agnostic. Bootstrap Icons CSS CDN can stay as-is.
   No action needed unless switching icon set.

3. **`021-list-inline-create` compatibility**: That feature's inline create modal uses Bootstrap
   JS (`bootstrap.Modal`). Once Bootstrap JS is removed in Phase 1, the modal will stop working
   until Phase 3.5 rewrites it. Either:
   - Do Phase 3.5 (modal rewrite) before removing Bootstrap JS, OR
   - Keep Bootstrap JS temporarily until Phase 3.5 is complete

4. **`django-cotton-bs5`**: The project currently depends on `django-cotton-bs5 ≥ 0.10.0` (per
   plan.md of feature 021). This package provides Bootstrap 5-specific Cotton components. Once
   DaisyUI replaces Bootstrap, this dependency should be removed.

5. **Theme system**: DaisyUI supports `data-theme` on any element, not just `<html>`. This means
   per-component theme overrides are possible (e.g. dark sidebar, light content area) — a
   significant UX improvement over the current `data-bs-theme` approach.

6. **Sidebar collapse on desktop**: DaisyUI drawer is open/closed — no "collapsed to icons only"
   (mini mode) built in. If icon-only sidebar collapse is required, it needs custom CSS or a
   third-party solution. Consider deferring this to a follow-up feature.
