# Feature Specification: AdminLTE Layout Component Separation

**Feature Branch**: `001-layout-components`
**Created**: January 5, 2026
**Status**: Draft
**Input**: User description: "MVP maintains the 5 major layout components of AdminLTE in separate cotton components in the cotton/app/ dir. There will be a component for app (top-level wrapper), header, sidebar, main and footer. These component must reflect the individual configuration provided by adminlte for each component."

## Clarifications

### Session 2026-01-05

- Q: Should component configuration be sourced from MVP settings dictionary or passed directly to components? → A: Configuration should be passed directly to components via Cotton vars (c-vars), making components more reusable and self-contained. MVP settings-based configuration will be deferred to future iterations.
- Q: Should additional example templates be created to demonstrate composition flexibility beyond the existing demo/dashboard.html? → A: No additional templates or views are required. User Story 2 composition flexibility can be validated using only the existing DashboardView and demo/dashboard.html template.
- Q: Should the sidebar component be split into sub-components for branding and navigation menu sections? → A: Split sidebar into subdirectory with sub-components: sidebar/index.html (orchestrator), sidebar/branding.html (logo/text), sidebar/menu.html (nav element). This improves reusability and allows independent customization of branding and menu structures.
- Q: Should the main component be split into sub-components for content header and main content sections? → A: Split main into subdirectory with sub-components: main/index.html (orchestrator), main/content_header.html (page title/breadcrumbs wrapper), main/content.html (main content wrapper). This allows independent styling of header and content areas.
- Q: Should app and footer components be split into subdirectories? → A: App component uses subdirectory structure (app/index.html) for consistency with other layout components. Footer remains as single flat file (footer.html) as it serves a single, cohesive purpose without distinct sub-sections that warrant extraction.
- Q: Which naming convention should be used for sub-component files? → A: Use descriptive snake_case names following django-cotton conventions: sidebar/branding.html, sidebar/menu.html, main/content_header.html, main/content.html. Never use kebab-case for django-cotton components.
- Q: Should the header component be split into sub-components to support custom navbar widgets? → A: Split header into subdirectory with 2 components: header/index.html (orchestrator with navbar built in), header/toggle.html (sidebar toggle button). This provides extension points for navbar widgets while keeping navbar structure integrated.

### Session 2026-01-06

- Q: Should the wrapper component be renamed to "app" to align with spec 003 changes? → A: Update all references from "wrapper" to "app" (component is now app/index.html, callable as <c-app>). This aligns with the implementation that emerged from spec 003 where the top-level layout orchestrator is the app component.
- Q: Should mvp/base.html provide extensive template blocks for customization (page_title, breadcrumbs, sidebar_menu, etc.) or use a simplified approach? → A: Simplified approach. mvp/base.html extends base.html and provides only essential blocks: `app` block (wraps entire <c-app> component) and `content` block (for page content within <c-app.main>). Component-level customization happens by overriding the `app` block and composing components directly.
- Q: Should django-mvp provide both base.html and mvp/base.html, or consolidate into a single base.html with the default app layout? → A: Consolidate into single base.html. Define the default app layout (5 components) directly in base.html's `app` block. This follows Django convention where developers extend base.html. For custom layouts, developers create their own base.html that extends django-mvp's base.html and override the `app` block. This provides better out-of-the-box experience and aligns with Django best practices.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Component Isolation and Reusability (Priority: P1)

As a Django developer using django-mvp, I want the AdminLTE layout components split into separate Cotton components so that I can selectively customize, extend, or replace individual layout sections without modifying the entire layout structure.

**Why this priority**: This is the core architectural change that enables all other benefits. Without separating the components, developers cannot achieve granular control over layout sections.

**Independent Test**: Can be fully tested by extending mvp/base.html and overriding individual component blocks (e.g., only the header block) while keeping other components intact. Success is demonstrated when only the targeted section changes.

**Acceptance Scenarios**:

1. **Given** a Django project using django-mvp, **When** a developer extends base.html and overrides the `app` block to compose <c-app> with a custom header component while keeping other components, **Then** only the header section is replaced while app wrapper, sidebar, main, and footer remain unchanged.

2. **Given** a Django project using django-mvp, **When** a developer inspects the cotton/app/ directory, **Then** they see five component directories/files: app/index.html (top-level orchestrator), header/ (with subdirectory), sidebar/ (with subdirectory), main/ (with subdirectory), and footer.html.

3. **Given** a project template extending base.html, **When** the developer overrides the `app` block and composes <c-app> without the sidebar component, **Then** the page renders without a sidebar while maintaining all other layout sections.

---

### User Story 2 - Component Composition Flexibility (Priority: P2)

As a Django developer, I want to be able to compose custom layouts using the separated components so that I can create different page layouts for different sections of my application (e.g., full-width pages without sidebars, minimal layouts without headers).

**Why this priority**: While important for advanced use cases, this builds on the foundation of P1 and P2. Basic layout functionality works without this capability.

**Independent Test**: Can be tested by creating a custom template that includes only specific components (e.g., wrapper + header + main, skipping sidebar and footer) and verifying the page renders correctly without errors.

**Acceptance Scenarios**:

1. **Given** a custom page template, **When** the template includes only app, header, and main components (excluding sidebar and footer), **Then** the page renders a simplified layout without sidebar navigation or footer.

2. **Given** a dashboard template, **When** the template uses all five components with different configurations, **Then** each component respects its individual configuration without interference.

3. **Given** a login page template, **When** the template uses only the app component with custom content, **Then** the page renders a minimal layout suitable for authentication screens.

---

### Edge Cases

- How does the system handle invalid or conflicting configuration options passed to components via Cotton vars?
- How are default configuration values applied when component attributes are not provided?
- What happens when a component slot is left empty (no content provided)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST split the current monolithic layout template into five Cotton component groups: app/index.html (top-level orchestrator in subdirectory), header/ (subdirectory with index.html and toggle.html), sidebar/ (subdirectory with index.html and sub-components), main/ (subdirectory with index.html and sub-components), and footer.html (flat file), located in templates/cotton/app/ directory. Note: This expands to 11 total template files when including subdirectory structure.

- **FR-002**: Each component MUST accept configuration parameters via Cotton vars (c-vars) that correspond to AdminLTE's configuration options for that component.

- **FR-003**: The app component MUST render the top-level `.app-wrapper` grid container and accept component attributes for layout-level configuration (fixed_sidebar, fixed_header, fixed_footer for fixed positioning; sidebar_expand for responsive breakpoints; class for custom CSS classes).

- **FR-004**: The header component MUST render the `.app-header` section and accept component attributes for navbar content and header-specific classes. The header is organized as a subdirectory with header/index.html (orchestrator with navbar structure) and header/toggle.html (sidebar toggle button).

- **FR-005**: The sidebar component MUST render the `.app-sidebar` navigation section and accept component attributes for visibility, width, and sidebar-specific behavior.

- **FR-006**: The main component MUST render the `.app-main` content area including `.app-content-header` (breadcrumbs) and `.app-content` (main content) sections, accepting component attributes for content area styling.

- **FR-007**: The footer component MUST render the `.app-footer` section and accept component attributes for visibility and footer text.

- **FR-008**: Components MUST use Cotton's slot system to allow content injection (e.g., sidebar menu items, main content, breadcrumbs).

- **FR-009**: Components MUST preserve AdminLTE's grid-based layout structure and CSS class conventions exactly as specified in AdminLTE 4 documentation.

- **FR-010**: The base.html template MUST define the default app layout directly in the `app` block, composing all 5 components (<c-app> with header, sidebar, main, footer). Developers extend base.html following standard Django convention. The `app` block allows complete layout override, and the `content` block (within <c-app.main>) allows page content injection. This eliminates the need for a separate mvp/base.html intermediate template.

- **FR-011**: Each component MUST handle missing or undefined component attributes gracefully by applying reasonable defaults that match AdminLTE's standard behavior.

- **FR-012**: Component attributes MUST be declared using Cotton's c-vars system with appropriate default values for optional configuration.

- **FR-013**: Components MUST be independently testable as Cotton components, allowing unit tests to verify rendering with various configuration combinations.

### Key Entities

- **App Component**: Represents the top-level `.app-wrapper` grid container. Organized as a subdirectory with app/index.html serving as the layout orchestrator. Callable as `<c-app>`. Accepts component attributes for layout-wide configuration (fixed_sidebar, fixed_header, fixed_footer for fixed positioning; sidebar_expand for responsive breakpoints; class for custom CSS classes). Contains default slot for all other layout components (header, sidebar, main, footer).

- **Header Component**: Represents the `.app-header` navbar section. Organized as a subdirectory with two files: header/index.html (main orchestrator with integrated navbar structure including left and right content areas), and header/toggle.html (sidebar toggle button component). Accepts component attributes for header-specific styling options. Contains named slots for left and right navbar content, providing extension points for custom navbar widgets.

- **Sidebar Component**: Represents the `.app-sidebar` navigation section. Organized as a subdirectory with three files: sidebar/index.html (main orchestrator), sidebar/branding.html (logo and brand text), and sidebar/menu.html (navigation menu wrapper). Accepts component attributes for visibility, width settings, theme, and sidebar behavior options. Contains slots for sidebar menu content.

- **Main Component**: Represents the `.app-main` content area. Organized as a subdirectory with three files: main/index.html (main orchestrator), main/content_header.html (page title and breadcrumbs wrapper), and main/content.html (main content wrapper). Accepts component attributes for content area styling and visibility of header section. Contains slots for header content and main page content.

- **Footer Component**: Represents the `.app-footer` section. Single flat file (footer.html) with simple left/right content division. Accepts component attributes for visibility toggle and footer text. Contains default slot for custom footer content and named right slot for right-aligned content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can customize any single layout section independently without affecting other sections (100% isolation between layout sections).

- **SC-002**: All AdminLTE layout features remain accessible through component attributes after the refactor (0% feature loss).

- **SC-003**: Each of the 5 layout sections can be validated independently with various configuration combinations, achieving comprehensive coverage of configuration scenarios.

- **SC-004**: Developers can compose custom page layouts using any combination of the 5 layout sections with minimal effort (target: 10 or fewer declarations).

- **SC-005**: The refactored structure reduces the size of individual layout section files by at least 50% compared to the current monolithic structure, improving maintainability and comprehension.

## Dependencies and Assumptions

### Dependencies

- AdminLTE 4 layout structure and CSS class conventions must remain stable
- Django Cotton component system for template composition and c-vars
- Django template system for block overriding and inheritance

### Assumptions

- Developers are familiar with Django template inheritance and block overriding
- Developers are familiar with Cotton component usage and attribute passing
- AdminLTE's grid-based layout (.app-wrapper container with child sections) is the architectural foundation
- Component isolation does not require changes to AdminLTE's CSS or JavaScript
- Default configuration values can be derived from AdminLTE's standard behavior
- Component configuration is more flexible and reusable when passed as component attributes rather than global settings
