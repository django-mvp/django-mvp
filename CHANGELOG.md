# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Settings-driven layout configuration** via `MVP_CONFIG["layout"]`:
  - `layout.sidebar.breakpoint` (`sm|md|lg|xl|2xl`) — when the sidebar becomes persistent.
  - `layout.sidebar.collapse` (`"offcanvas"` or `"icons"`) — slide fully away, or collapse
    to an icon rail with DaisyUI tooltips. Mark sidebar elements with `.mvp-rail-hide` /
    `.mvp-rail-only` to control their rail visibility.
  - `layout.navbar.end` — list of Cotton component names rendered at the navbar end via
    `<c-component :is="...">` (e.g. `"actions.theme-controller"`).
  - Resolution order everywhere: component attribute → `MVP_CONFIG` → package default.
  - The `mvp_config` context processor now exposes the merged config dict to all templates.
  - Sidebar open/closed state persists across navigation (Alpine `$persist`), defaulting by
    viewport width at the configured breakpoint.
- **`python manage.py mvp_tailwind`** — generates a Tailwind v4 entry stylesheet for projects
  that build their own CSS, scanning both their templates and django-mvp's packaged templates.
  The shared preset (`mvp/tailwind/base.css`) ships in the wheel. See `docs/styling.md`.
- **`mvp.integrations`** package for optional third-party integrations (see Changed).
- **CI stylesheet drift check** (`.github/workflows/stylesheet.yml`) — fails if the committed
  CSS is stale relative to the Tailwind sources.
- **Component render smoke tests** — every packaged Cotton template renders in CI.
- `c-page.list.actions.share` list action and a working `c-addons.share-dropdown`.

### Changed

- **BREAKING: optional-dependency views moved to `mvp.integrations`** — integrations are
  guarded modules, not extras; the dependency is only required when explicitly imported:
  - `mvp.views.table.MVPTableView(Mixin)` → `mvp.integrations.django_tables.views`
  - `mvp.views.MVPFilteredListView` → `mvp.integrations.django_filters.views`
    (the `applied_filters` context logic moved with it)
- **BREAKING: `c-button` size API** — `size="sm|md|lg"` replaces the boolean `small`/`large`
  attributes; `variant="default"` (which emitted a non-existent `btn-default` class) removed;
  `outline` is now implemented.
- **BREAKING: `c-dropdown`** — `halign="start|center|end"` implemented, `valign` options are
  now `top|bottom|left|right`; undeclared `position`/`trigger` attributes removed.
- `crispy-tailwind` and `crispy-bootstrap5` are no longer runtime dependencies. Install
  `django-crispy-forms` + `crispy-tailwind` yourself to enable crispy form rendering
  (auto-detected at runtime, unchanged).
- Navbar widgets in `mvp/base.html` now come from `MVP_CONFIG["layout"]["navbar"]["end"]`;
  the `{% block app.header.widgets %}` override still works.

- **`OrderMixin.order_by` format changed from two-tuple to three-tuple** (Feature 014):

  The `order_by` class attribute now requires a three-tuple `(public_key, label, orm_expression)`
  instead of the previous two-tuple `(orm_expression, label)`.

  **Upgrade instructions**:

  ```python
  # Before (two-tuple — no longer supported):
  order_by = [
      ("name", "Name (A-Z)"),
      ("-name", "Name (Z-A)"),
  ]

  # After (three-tuple — required):
  order_by = [
      ("name_asc",  "Name (A-Z)", "name"),
      ("name_desc", "Name (Z-A)", "-name"),
  ]
  ```

  The `public_key` (first element) is the value matched against `?o=` in the URL.
  It need not match the database column name — use opaque keys to avoid leaking
  schema information in URLs. The `orm_expression` (third element) is the value
  passed to `queryset.order_by()` and is never exposed in URLs.

  Templates that iterate over `order_by_choices` must be updated to unpack three
  values: `{% for key, label, _ in order_by_choices %}`.

### Fixed

- Restored the DaisyUI plugin in the Tailwind build — v0.12.0 shipped a stylesheet with no
  DaisyUI classes. Defined the previously-missing `is-drawer-open:`/`is-drawer-close:`
  custom variants the sidebar depends on.
- Sidebar menu active-state highlight never rendered (`selected` vs `active` mismatch).
- `c-section` silently dropped its `title`/`icon`/`level` attributes.
- Collapsed sidebar content spilled over the page (missing overflow clipping).
- `c-placeholder.card` and `c-dock.item` crashed when their optional `icon` was omitted.
- Header `right`/`tray` slots were never forwarded into the navbar.
- Classes built from component attributes (`btn-{{ variant }}`, `grid-cols-{{ cols }}`, …)
  are now safelisted in the preset — they previously only compiled by accident.
- Removed remaining Bootstrap/AdminLTE leftovers from DaisyUI templates, two orphaned
  AdminLTE toggle templates, and assorted dead code.

### Added

- **List Search and Ordering Mixins** (Feature 014): Formalised `SearchMixin`,
  `OrderMixin`, and `SearchOrderMixin` with comprehensive test coverage and
  Constitution-XII-compliant docstrings.
  - **`SearchMixin`**: Django admin-style multi-word OR text search via `?q=`.
    `is_searchable` and `search_query` context sentinels always injected.
  - **`OrderMixin`**: Whitelist-only column ordering via `?o=`. Security guarantee:
    raw `?o=` values never reach the ORM.
  - **`SearchOrderMixin`**: Combined mixin with fixed MRO ensuring correct
    evaluation order (ordering before `distinct()`).
  - **`django_filters` composition**: `SearchOrderMixin` composes correctly with
    `FilterView` when placed left of it in the MRO.
  - **Test coverage**: 35 new unit tests covering all four user stories.

- **Form View Mixins** (Feature 009): Automatic form renderer detection with AdminLTE layout
  - **MVPFormView**: Drop-in replacement for Django's FormView with auto-detected rendering
    - Automatically detects django-crispy-forms, django-formset, or falls back to Django standard rendering
    - AdminLTE card-based layout with consistent styling
    - Configurable `page_title` attribute for card header
    - Optional `form_renderer` attribute for explicit override: `"crispy"`, `"formset"`, or `"django"`
  - **MVPCreateView**: Model form create views with auto-detected rendering
    - All FormView features plus Django CreateView functionality
    - Works with model `fields` list or custom `form_class`
  - **MVPUpdateView**: Model form edit views with auto-detected rendering
    - All FormView features plus Django UpdateView functionality
    - Pre-populates form with existing model data
  - **Demo Views**: Four comprehensive examples showing all features
    - Contact Form (auto-detection demo)
    - Product Create (model form demo)
    - Product Update (model form edit demo)
    - Explicit Renderer Override (shows renderer priority)
  - **Complete Test Coverage**: 40 passing tests covering all form view scenarios
    - Unit tests for renderer detection logic
    - Integration tests for form rendering and submission
    - Test coverage: 49% for mvp/views.py
  - **Documentation**: Usage examples added to README.md
  - **Feature Specification**: [specs/009-form-view-mixin/](specs/009-form-view-mixin/)

- **Django Tables2 Integration** (Feature 007): Optional django-tables2 support with Bootstrap 5 responsive tables
  - **Optional Dependency**: Install with `pip install django-mvp[datatables2]`
  - **Demo Page**: Interactive table examples at `/datatables/` demonstrating sorting, pagination, and responsive display
  - **Fill Mode Support**: Tables that fill viewport height using Bootstrap 5 flexbox utilities
  - **Template Overrides**: Custom `django_tables2/bootstrap5-responsive.html` with responsive container
  - **ProductTable**: Example table for demo purposes using existing Product model
  - **Documentation**: Complete usage guide at [specs/007-datatables-integration/quickstart.md](specs/007-datatables-integration/quickstart.md)
  - **Feature Specification**: [specs/007-datatables-integration/](specs/007-datatables-integration/)

- **Inner Layout System** (Feature 006): Complete grid-based layout system for inner page content
  - **CSS Grid Architecture**: Modern grid-based layout with toolbar, main content, footer, and sidebar areas
  - **Sticky Positioning**: Optional sticky toolbar, footer, and sidebar with `toolbar_fixed`, `footer_fixed`, `sidebar_fixed` attributes
  - **Sidebar Toggle Functionality**: Built-in collapse/expand with sessionStorage persistence
    - Smooth animations with hardware acceleration
    - No-transition on page load fix for FOUC prevention
    - ARIA-compliant with full keyboard accessibility
    - Icon updates to match collapsed/expanded state
  - **Responsive Sidebar**: Configurable breakpoints (`sm`, `md`, `lg`, `xl`, `xxl`) for mobile-friendly overlay behavior
  - **Template-Driven Configuration**: All settings controlled via component attributes
  - **Slot-Based Composition**: Toolbar, footer, and sidebar render only when their slots are provided
  - **Components**:
    - `<c-page>` - Main container with grid layout
    - `<c-page.toolbar>` - Top action bar with start/end slots
    - `<c-page.footer>` - Bottom bar with start/end slots
    - `<c-page.sidebar>` - Right-side panel with toggle support
  - **Demo Page**: Interactive demo at `/page-layout/` with configuration presets
  - **Documentation**: Complete component guide at [docs/page-layout.md](docs/page-layout.md)
  - **Feature Specification**: [specs/006-page-layout/](specs/006-page-layout/)
  - **Test Coverage**: Unit tests + E2E tests + browser verification

- **Layout Configuration System**: Complete support for AdminLTE 4 fixed positioning via `<c-app>` component attributes
  - **CRITICAL Architecture Fix**: Layout classes now correctly applied to `<body>` tag for AdminLTE CSS compatibility
  - **Fixed Sidebar** (`fixed_sidebar`): Makes sidebar sticky during vertical scrolling - ideal for admin dashboards
  - **Fixed Header** (`fixed_header`): Keeps top navigation bar fixed at the top - ideal for important navigation
  - **Fixed Footer** (`fixed_footer`): Keeps footer visible at the bottom - ideal for copyright notices or action buttons
  - **Fill Layout** (`fill`): NEW - Viewport-constrained layout mode for data-intensive UIs
    - Restricts app-wrapper to 100vh height with hidden scrollbars
    - Changes scroll container from body to app-wrapper
    - Keeps app-header/footer visible while app-main scrolls
    - Perfect for data tables, maps, dashboards, and fixed toolbar layouts
    - Combines with fixed attributes for sophisticated layouts
    - Interactive demo available at `/layout/?fill=on`
  - **Combined Fixed Layouts**: All attributes can be used simultaneously for complete fixed layout
  - **Responsive Sidebar Control** (`sidebar_expand`): Control sidebar expansion breakpoint (sm, md, lg, xl, xxl)
  - **Per-Page Layout Override**: Different pages can use different layout configurations
  - **Interactive Layout Demo Page**: Single unified demo page at `/layout/` for testing all layout configurations
    - Query parameter-based state management (bookmarkable URLs)
    - Split layout: main content area (col-lg-8) + configuration sidebar (col-lg-4)
    - Form controls for toggling fixed properties, responsive breakpoints, and fill mode
    - Real-time layout updates via GET requests
    - Visual indicators showing active CSS classes and configuration state
    - Extensible design allowing other features to add configuration options
  - CSS Classes: `.layout-fixed`, `.fixed-header`, `.fixed-footer`, `.fill`, `.sidebar-expand-{breakpoint}`
  - Component Documentation: [docs/components/app.md](docs/components/app.md)
  - Feature Specification: [specs/002-layout-configuration/](specs/002-layout-configuration/)
  - Test Coverage: Architecture tests + component attribute tests + layout demo integration tests

- **AdminLTE 4 Widget Components**: Complete implementation of three dashboard widget components
  - **Info Box Component** (`<c-info-box>`): Display metrics with icons and optional progress bars
    - Two fill modes: `fill="icon"` (default, colors icon only) and `fill="box"` (colors entire box)
    - Progress bar support using `<c-progress>` component with ARIA attributes
    - Bootstrap 5 color variants (primary, success, warning, danger, info, secondary)
    - Custom CSS class passthrough
    - Full accessibility support with proper ARIA attributes
    - Documentation: [docs/components/info-box.md](docs/components/info-box.md)
  - **Small Box Component** (`<c-small-box>`): Prominent dashboard summary widgets
    - Large metric display with colored background
    - Decorative background icons
    - Optional footer with action links (default text: "More info")
    - Custom link icon support
    - Bootstrap 5 color variants via `variant` attribute
    - Documentation: [docs/components/small-box.md](docs/components/small-box.md)
  - **Card Component** (`<c-card>`): Flexible content containers with collapsible sections
    - Three fill modes: `fill="outline"` (default, border only), `fill="header"` (header colored), `fill="card"` (entire card colored)
    - Optional icon in header
    - Named slots for `tools` and `footer`

- **Site Navigation System**: Complete implementation of AdminLTE 4 sidebar navigation
  - **Django Flex-Menus Integration**: Full support for hierarchical menu definitions
    - Menu groups with icons, badges, and expandable sub-items
    - Support for dividers and section headers
    - Active state detection with URL pattern matching
    - Accessibility-compliant ARIA attributes and keyboard navigation
  - **AdminLTE 4 Renderer**: Custom `AdminLteRenderer` for sidebar menu styling
    - Proper CSS classes: `.sidebar-menu`, `.nav-item`, `.nav-treeview`, `.menu-open`
    - Bootstrap Icons integration with proper spacing and alignment
    - Badge rendering with color variants (primary, success, warning, danger, info)
    - Hierarchical tree-view structure with proper indentation
  - **Cotton Components**: Optional manual menu construction
    - `<c-menu>`: Root menu container
    - `<c-menu-item>`: Individual menu items with optional icons and badges
    - `<c-menu-group>`: Expandable menu groups with sub-items
    - Full component customization with c-vars and slot system
  - **Active Class Management**: Smart active state detection
    - URL-based matching for current page highlighting
    - Parent menu expansion when child items are active
    - Visual indicators with AdminLTE `.active` and `.menu-open` classes
  - Documentation: [docs/navigation.md](docs/navigation.md)
  - Feature Specification: [specs/004-site-navigation/](specs/004-site-navigation/)
  - Test Coverage: Menu rendering tests + active state tests + Cotton component tests
    - AdminLTE card tools integration (collapse, maximize, remove buttons)
    - Collapsible state support via `collapsed` attribute
    - Documentation: [docs/components/card.md](docs/components/card.md)
- Comprehensive test suite with 30 tests covering all widget components (97% passing, 1 known Cotton limitation)
- Component documentation with complete API references, examples, and accessibility guidelines
- Documentation index at [docs/index.md](docs/index.md) with architecture overview and usage patterns

### Changed

- Updated README.md with accurate component examples matching actual implementations
- Component examples now use correct attribute names and values (`variant`, `fill`, etc.)

### Technical Details

- **Components Location**: `mvp/templates/cotton/`
- **Test Coverage**: 29/30 tests passing (info-box: 8/8, small-box: 9/9, card: 12/13)
- **Known Limitation**: One card test fails due to Cotton `_children` behavior (documented)
- **Dependencies**: Requires `django-cotton`, `django-cotton-bs5`, `django-easy-icons`
- **Accessibility**: All components follow WCAG 2.1 AA guidelines with proper ARIA attributes
- **Files Added**:
  - `mvp/templates/cotton/info_box.html`
  - `mvp/templates/cotton/small_box.html`
  - `mvp/templates/cotton/card.html`
  - `tests/test_info_box.py` (8 tests)
  - `tests/test_small_box.py` (9 tests)
  - `tests/test_card.py` (13 tests)
  - `docs/components/info-box.md`
  - `docs/components/small-box.md`
  - `docs/components/card.md`
  - `docs/index.md`
- **Specification**: `specs/003-default-widgets/`

---

- **Outer Layout Configuration System** (`PAGE_CONFIG`): Centralized configuration-driven layout system with per-region settings for sidebar, navbar, brand, and actions
  - **Per-region configuration**: `sidebar.*`, `navbar.*`, `brand`, `actions` keys (no top-level `navigation.*`)
  - **Smart defaults**: Navbar-only mode by default (`sidebar.show_at=False`, `breakpoint="sm"`)
  - **Single-source navigation**: Primary navigation renders in one region only (sidebar when in-flow, navbar otherwise) - prevents duplication
  - **Actions placement**: Actions automatically render in the active navigation region based on viewport and configuration
  - **Brand fallback**: Automatic fallback to text when theme-appropriate images are missing
  - **Breakpoint validation**: Validates Bootstrap 5 breakpoints (`sm`, `md`, `lg`, `xl`, `xxl`) with warning logs for invalid values
  - **Context processor integration**: `mvp.context_processors.page_config` exposes validated configuration to all templates
  - **Dynamic attr passthrough**: Uses Cotton's `:attrs` syntax for clean configuration flow to components
- Comprehensive test suite for layout configuration system covering navigation placement, brand/actions, responsive behavior, and edge cases
- Updated documentation in `docs/LAYOUT_CONFIGURATION.md` with complete schema reference, examples, and migration guide
- Example templates demonstrating configuration flow with explanatory comments

### Changed

- Context processor now enforces navbar-only mode by default (breaking change from previous implicit sidebar mode)
- Configuration validation now enforces single-source navigation rule: `navbar.breakpoint` is automatically ignored when `sidebar.show_at` is a breakpoint
- Brand and actions rendering now conditional based on configuration state rather than always present

### Fixed

- Eliminated duplicate navigation rendering when both sidebar and navbar were visible
- Proper responsive behavior for actions widgets (follow active navigation region)
- Brand image fallback now properly preserves accessibility

### Technical Details

- **Constitution Gates Validated**:
  - ✅ Gate A: No duplicate navigation (single-source rendering enforced)
  - ✅ Gate B: Framework-independent layout (works without Bootstrap)
  - ✅ Gate C: Template-only inner layout (no code dependencies)
  - ✅ Gate D: Accessibility (ARIA landmarks, focus order, keyboard navigation)
  - ✅ Gate E: Theming (Sass/CSS variables for customization)
  - ✅ Gate F: Progressive enhancement (JS optional, core functional without)
- **JSON Schema**: Complete configuration contract in `specs/001-outer-layout-config/contracts/page_config.schema.json`
- **Files Modified**:
  - `mvp/context_processors.py`: Added validation, defaults, enforcement rules
  - `mvp/templates/cotton/structure/sidebar/index.html`: Conditional actions rendering
  - `mvp/templates/cotton/structure/navbar/index.html`: Conditional actions rendering
  - `mvp/templates/cotton/structure/sidebar/widgets.html`: Actions visibility parameter
  - `tests/settings.py`: Updated example configuration
  - `tests/test_outer_layout_config.py`: New comprehensive test suite
  - `docs/LAYOUT_CONFIGURATION.md`: Complete rewrite for new system
  - `demo/templates/layouts/base.html`: Added configuration flow comments

### Migration Notes

If upgrading from earlier versions:

1. Remove any `layout` key from `PAGE_CONFIG` (no longer used)
2. Set `sidebar.show_at=False` for navbar-only mode (new default)
3. Set `sidebar.show_at="lg"` (or preferred breakpoint) for sidebar mode
4. Add `navbar.breakpoint="sm"` for navbar-only mode
5. Ensure `actions` is a list at top level (not nested under navigation)
6. Review configuration schema in documentation for all available keys

### Added

- Initial project structure
- Basic app configuration
- Test suite setup
- CI/CD workflows

## [0.1.0] - 2025-12-09

### Added

- Initial alpha release
- Project scaffolding
- Poetry configuration
- GitHub Actions workflows
- Issue templates
- Copilot instructions

[Unreleased]: https://github.com/SamuelJennings/django-cotton-layouts/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SamuelJennings/django-cotton-layouts/releases/tag/v0.1.0
