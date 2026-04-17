# Feature Specification: AdminLTE Layout Configuration System

**Feature Branch**: `002-layout-configuration`
**Created**: January 5, 2026
**Status**: Draft
**Input**: User description: "We need to support the various layout options provided by AdminLTE. This includes default, fixed sidebar, fixed header, fixed footer, fixed complete. This spec will not handle sidebar mini (handled in a later spec)."

## Clarifications

### Session 2026-01-05

- Q: Which component receives layout attributes? → A: Layout attributes are placed on `<c-app>` component. There is no `c-mvp.wrapper` component - no components start with `mvp` prefix.
- Q: Layout attribute value format? → A: Separate boolean attributes for each element (e.g., `fixed_sidebar fixed_header fixed_footer`)
- Q: Is "fixed complete" a separate option? → A: No separate `fixed_complete` attribute. Fixed complete layout is achieved by specifying all individual fixed attributes together.
- Q: What does "fixed" mean for sidebar? → A: Fixed sidebar means `position: sticky` with 100vh height and scrollable content. The `sidebar_expand` breakpoint separately controls when sidebar is visible vs off-screen. These are independent layout concerns.
- Q: Should "layout + custom area" be included? → A: No. Custom area functionality is out of scope and will not be documented.

### Session 2026-01-06

- Q: Where should demo views for testing layout options be located? → A: In the `demo/` app within django-mvp as demo views with their own URLs
- Q: What content should demo pages display to demonstrate scrolling behavior? → A: Long-form content with multiple sections (headings, paragraphs, data tables) totaling 2-3 viewport heights. Sidebar must include several dummy menu items to test independent scrolling.
- Q: Which breakpoint transitions should be explicitly tested/demonstrated? → A: Demo page should include a dropdown at the top listing available breakpoints (sm, md, lg, xl, xxl). When dropdown changes, submit GET request to same page with breakpoint="value" query param. View or template inspects query params to modify layout behavior.
- Q: How should fixed properties demo view allow testing different combinations? → A: Use form with checkboxes for fixed_header, fixed_sidebar, and fixed_footer submitting via GET request with query params. No separate checkbox for "complete" - that's just the combination of all three.
- Q: Should demo views include visual indicators or helper text? → A: Include minimal helper text at top explaining what to test (e.g., "Scroll to test fixed elements" / "Resize window to test breakpoint") plus visual indicators showing current configuration state.

### Session 2026-01-20

- Q: How does `fill` attribute relate to other fixed attributes? → A: Fill can technically combine with fixed attributes but overrides their behavior as an all-in-one layout configuration for content requiring full visible screen without overlap.
- Q: What scrolling behavior change does `fill` introduce? → A: Fill makes app-header/footer always visible (fixed) while app-main scrolls between them, changing scroll container from body/html to app-wrapper (with hidden scrollbars).
- Q: What is the primary use case for `fill` layout? → A: Full-screen data-intensive UIs - especially data tables and maps (e.g., maplibre) that look better when tightly fit into available space.
- Q: Should layout demo page include `fill` option? → A: Yes, add fill as a checkbox option in the layout demo form alongside fixed attributes.
- Q: How does `fill` affect the inner page-layout grid system? → A: Enables app-header/footer to be fixed while app-main scrolls, allowing page-layout's internal toolbar-fixed/footer-fixed to work correctly (which doesn't function properly without fill on app-wrapper).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply Basic Layout Variations (Priority: P1)

A Django developer building an admin dashboard wants to configure whether the sidebar, header, or footer should be fixed (remain visible during scrolling) or default (scroll with content). They want to set this once and have it apply consistently across all pages.

**Why this priority**: This is the foundational capability - without basic layout control, the feature has no value. This delivers immediate visual and UX benefits to end users.

**Independent Test**: Can be fully tested by configuring a single layout option (e.g., fixed sidebar) and verifying that the sidebar stays fixed when scrolling page content. Delivers standalone value by improving navigation accessibility.

**Acceptance Scenarios**:

1. **Given** a Django project using django-mvp, **When** developer configures fixed sidebar layout, **Then** sidebar remains visible when user scrolls page content
2. **Given** fixed header is enabled, **When** user scrolls down a long page, **Then** navigation header stays at top of viewport
3. **Given** fixed footer is enabled, **When** user scrolls content, **Then** footer remains visible at bottom of viewport
4. **Given** default (non-fixed) layout is used, **When** user scrolls, **Then** all layout elements scroll naturally with content

---

### User Story 2 - Combine Multiple Fixed Elements (Priority: P2)

A developer needs to create a data-heavy dashboard where users need constant access to navigation (header + sidebar) while viewing long data tables. They want to enable multiple fixed elements simultaneously.

**Why this priority**: Builds on P1 by enabling complex layouts. Common in data-centric applications but depends on basic fixed-element functionality working first.

**Independent Test**: Can be tested by enabling fixed header + fixed sidebar together, then verifying both remain visible during scroll. Delivers enhanced navigation for complex interfaces.

**Acceptance Scenarios**:

1. **Given** both fixed header and fixed sidebar are enabled (e.g., `<c-app fixed_header fixed_sidebar>`), **When** user scrolls page content, **Then** both header and sidebar remain fixed in their positions
2. **Given** fixed header + fixed footer are enabled (e.g., `<c-app fixed_header fixed_footer>`), **When** user scrolls, **Then** only the main content area scrolls between fixed header and footer
3. **Given** all fixed attributes are specified (e.g., `<c-app fixed_sidebar fixed_header fixed_footer>`), **When** user scrolls, **Then** only the app-content area scrolls while all surrounding elements stay fixed

---

### User Story 3 - Configure Layout Per-Page or Globally (Priority: P3)

A developer wants flexibility to either set layout options globally for the entire application or override them on specific pages (e.g., a full-screen report page that needs different layout than standard admin pages).

**Why this priority**: Adds flexibility for advanced use cases but isn't required for basic functionality. Most applications use consistent layout throughout.

**Independent Test**: Can be tested by setting a global fixed sidebar, then overriding it on one specific page to be non-fixed, and verifying both pages render correctly. Delivers advanced customization capability.

**Acceptance Scenarios**:

1. **Given** a base template with layout configuration on `<c-app>` component (e.g., `<c-app fixed_sidebar>`), **When** developer extends that base template, **Then** all child pages inherit that layout by default
2. **Given** a base template with layout configuration, **When** developer overrides the `<c-app>` component's layout attributes on a specific page, **Then** that page uses the override while others use base template settings
3. **Given** no explicit layout attributes on `<c-app>` component, **When** page renders, **Then** system uses AdminLTE default layout (non-fixed elements)

---

### User Story 3.5 - Full-Screen Fill Layout for Data-Intensive UIs (Priority: P2)

A developer building a data dashboard with tables, charts, or interactive maps (e.g., maplibre) needs the interface to fill the entire viewport height (100vh) without body scrolling, with app-header and app-footer always visible while the main content area scrolls independently.

**Why this priority**: Addresses a distinct layout pattern critical for data-intensive applications where content needs tight viewport constraints. Builds on fixed layout understanding but introduces viewport-filling scroll container change.

**Independent Test**: Can be tested by adding `fill` attribute to `<c-app>` component and verifying: (1) app height is constrained to 100vh, (2) app-header/footer remain visible, (3) scrolling happens within app-main instead of body, (4) page-layout's internal fixed toolbar/footer work correctly. Delivers essential layout mode for full-screen data views.

**Acceptance Scenarios**:

1. **Given** a Django project using django-mvp, **When** developer adds `fill` attribute to `<c-app>` component (e.g., `<c-app fill>`), **Then** the app-wrapper is constrained to 100vh height with hidden scrollbars and scrolling moves from body to app-main
2. **Given** fill layout is enabled, **When** user scrolls page content, **Then** app-header remains fixed at top and app-footer (if present) remains fixed at bottom while only app-main content scrolls between them
3. **Given** fill layout with page-layout grid inside app-main, **When** developer adds toolbar-fixed or footer-fixed classes to page-layout elements, **Then** those internal sticky elements work correctly within the scrolling app-main container
4. **Given** fill layout is used for a data table or map interface, **When** content is rendered, **Then** the interface tightly fits available viewport space without body-level scrolling or layout overflow
5. **Given** fill attribute is combined with fixed attributes (e.g., `<c-app fill fixed_sidebar>`), **When** page renders, **Then** fill behavior takes precedence as an all-in-one layout configuration, making app-header/footer implicitly fixed regardless of individual fixed attributes

---

### User Story 4 - Interactive Layout Configuration Demo Page (Priority: P2)

A developer or QA tester wants to explore and validate different layout configurations interactively without modifying code. They need a single, reusable demo page that allows toggling layout options via a form and seeing the results immediately.

**Why this priority**: Provides essential testing and demonstration capability. Accelerates development workflow and serves as live documentation. Can be extended by future feature specs for other layout options.

**Independent Test**: Can be tested by navigating to /layout/, toggling layout options via the form, and verifying that the page updates with the selected configuration via query parameters. Delivers immediate value for testing and showcasing layout capabilities.

**Acceptance Scenarios**:

1. **Given** a user navigates to `/layout/` in the Demo App, **When** the page loads, **Then** they see a layout demo page with main content on the left and a configuration form sidebar on the right
2. **Given** the layout demo page is displayed, **When** user toggles layout options (fixed_header, fixed_sidebar, fixed_footer) via checkboxes and submits the form, **Then** the page reloads with query parameters reflecting the selected options and the layout updates accordingly
3. **Given** the sidebar navigation menu, **When** viewing any page in the Demo App, **Then** a "Layout Demo" menu link appears just below the Dashboard link
4. **Given** other feature specs need to demonstrate additional layout options, **When** they extend the layout demo page, **Then** the single `/layout/` page accommodates their additional configuration controls without creating duplicate demo pages
5. **Given** the layout demo form, **When** no options are selected, **Then** the page displays with default (non-fixed) layout and the form reflects this state

---

### Edge Cases

- What if sidebar_expand breakpoint conflicts with fixed sidebar positioning?
- How does the system handle custom layout classes that developers may add alongside MVP layout classes?
- What happens when a developer sets contradictory boolean values (e.g., `fixed_sidebar fixed_sidebar="false"`)?
- How does fill layout interact with browsers that don't support CSS `scrollbar-width: none` or `::-webkit-scrollbar`?
- What happens when fill is used on a page with very little content (less than viewport height)?
- How should nested scrollable containers (e.g., page-layout within fill layout) handle touch scrolling on mobile devices?
- What happens if a developer applies both fill and tries to use body-level scroll-based JavaScript libraries?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support AdminLTE's standard layout variations: default (non-fixed), fixed sidebar, fixed header, and fixed footer, with "fixed complete" achieved by combining all fixed attributes
- **FR-002**: System MUST allow developers to configure layout options via separate boolean Cotton component attributes on the `<c-app>` component (e.g., `<c-app fixed_sidebar fixed_header sidebar_expand="lg">`)
- **FR-003**: System MUST generate appropriate CSS classes for the body element based on configured layout attributes (`layout-fixed` for fixed_sidebar, `fixed-header` for fixed_header, `fixed-footer` for fixed_footer)
- **FR-004**: System MUST handle combinations of fixed elements correctly (e.g., fixed header + fixed sidebar should work together)
- **FR-005**: System MUST provide clear documentation on which layout options can be combined and their visual effects
- **FR-006**: System MUST maintain consistency with AdminLTE 4's CSS class naming conventions
- **FR-007**: System MUST support responsive sidebar expansion breakpoints (sm, md, lg, xl, xxl) as specified in AdminLTE
- **FR-008**: System MUST provide sensible defaults when no layout configuration is specified (default to AdminLTE's standard non-fixed layout)
- **FR-009**: System MUST NOT implement sidebar mini functionality (out of scope - covered in future spec)
- **FR-010**: System MUST provide demo views in the `demo/` app for testing fixed properties and responsive sidebar behavior
- **FR-011**: Demo views MUST include long-form content (2-3 viewport heights) with multiple sections and several dummy sidebar menu items to demonstrate independent scrolling behavior
- **FR-012**: Responsive behavior demo view MUST include a dropdown selector at the top of the page listing all available breakpoints (sm, md, lg, xl, xxl), which submits GET request with `breakpoint` query parameter to dynamically change sidebar expansion behavior
- **FR-013**: Fixed properties demo view MUST include a form with checkboxes (fixed_header, fixed_sidebar, fixed_footer, fill) that submits via GET request with query parameters, allowing any combination to be tested dynamically without requiring a separate "complete" checkbox
- **FR-014**: Demo views MUST include minimal helper text at the top explaining what to test and visual indicators showing current configuration state (active checkboxes, selected breakpoint, applied CSS classes)
- **FR-015**: System MUST provide a SINGLE layout demo page at `/layout/` in the Demo App that consolidates all layout testing functionality
- **FR-016**: Layout demo page MUST use a two-column layout with main content on the left and configuration form sidebar on the right
- **FR-017**: Layout demo page configuration form MUST submit via GET request with query parameters to allow bookmarkable/shareable layout configurations
- **FR-018**: System MUST provide a "Layout Demo" navigation menu item in the sidebar positioned immediately below the Dashboard link
- **FR-019**: Layout demo page MUST be designed to accommodate additional layout configuration options from future feature specs without requiring separate demo pages
- **FR-020**: System MUST support `fill` attribute on `<c-app>` component to enable full-screen viewport-constrained layout (e.g., `<c-app fill>`)
- **FR-021**: When `fill` is applied, system MUST constrain app-wrapper to 100vh height, hide wrapper scrollbars, and change scroll container from body to app-wrapper
- **FR-022**: Fill layout MUST make app-header always visible at top and app-footer (if present) always visible at bottom while app-main scrolls independently between them
- **FR-023**: Fill layout MUST enable page-layout's internal toolbar-fixed and footer-fixed positioning to work correctly within the scrolling app-main container
- **FR-024**: System MUST document that `fill` overrides individual fixed attributes as an all-in-one layout configuration designed for data-intensive interfaces (tables, maps, charts) requiring tight viewport fitting
- **FR-025**: Fill layout documentation MUST specify use cases: full-screen data tables, interactive maps (maplibre), dashboards, and any interface requiring viewport-constrained scrolling without body-level scroll

### Key Entities

- **Layout Configuration**: Represents the set of layout options that control fixed vs scrolling behavior for major layout sections (sidebar, header, footer, complete, fill)
- **Layout Section**: Represents major areas of the AdminLTE layout structure (app-sidebar, app-header, app-footer, app-wrapper) that can have fixed positioning
- **Fill Layout**: A specialized viewport-constrained layout mode where app-wrapper is restricted to 100vh, scroll container changes from body to app-wrapper, and app-header/footer remain always visible while app-main scrolls independently

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can configure any AdminLTE layout option (fixed sidebar/header/footer/fill) in under 2 minutes by changing a single configuration point
- **SC-002**: Layout changes render correctly across all modern browsers (Chrome, Firefox, Safari, Edge) without visual glitches
- **SC-003**: Fixed layout elements maintain their position during scrolling on pages with 10,000+ lines of content
- **SC-004**: Configuration method is documented with working examples for all supported layout variations including fill layout
- **SC-005**: Page load time increases by less than 50ms when using fixed or fill layout compared to default layout
- **SC-006**: Fill layout successfully constrains data-intensive interfaces (tables, maps) to viewport height with smooth scrolling performance on 60fps displays
