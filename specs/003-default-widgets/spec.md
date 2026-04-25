# Feature Specification: AdminLTE 4 Widget Components

**Feature Branch**: `003-default-widgets`
**Created**: January 5, 2026
**Status**: Draft
**Input**: User description: "Support the default AdminLTE 4 widgets with all available variations in style and ability. Currently there is an info box widget, a small box widget, and a card widget. Despite the name widgets, these components should be stored at the top-level cotton dir so they can be called easily using c-card, c-info-box and c-small-box respectively."

## Clarifications

### Session 2026-01-05

- Q: How should icons be provided to widgets (attribute vs slot vs both)? → A: Icon attribute only (developers pass icon name to custom c-icon component with optional class and data attributes)
- Q: How should progress bar be implemented in info-box (attributes vs slot)? → A: Progress bar via attributes (progress, description)
- Q: What happens when no color attribute is specified? → A: Default color classes (no color attribute = default AdminLTE neutral styling)
- Q: How should card content be structured (title attribute vs slots)? → A: Title attribute plus named slots for all sections (footer, tools). The default slot will fill the body.
- Q: How should small-box heading and footer be structured? → A: Keep heading plain text, use attributes for footer like link and link_text
- Q: Should widgets provide shadow attribute? → A: No shadow attribute - users provide BS5 utility classes directly on component
- Q: What attribute name for color variants? → A: Use `variant="primary"` not `color=""`. Color-related attributes default to "default" in c-vars
- Q: How should small-box footer links work? → A: Attributes `link` and `link_text` (default="More info") create footer automatically. No custom footer slots
- Q: Should card support icons in header? → A: Yes, optional `icon` attribute inserts icon before header text (on left)
- Q: Should small-box use `bg` or `variant` for color attribute? → A: Changed to `variant` to maintain consistency with info-box and card components (2026-01-05 final decision)
- Q: How should card variant styling be controlled? → A: Use `fill` attribute with values "outline" (default, applies variant to border), "header" (applies to header), "card" (applies to entire card). Only relevant when variant is not "default"
- Q: How should info-box color styling be controlled? → A: Changed to `fill` attribute (2026-01-05 final). Values: "icon" (default, colors icon span only) or "box" (colors entire info-box). Removed separate `bg` and `gradient` attributes in favor of unified `fill` approach matching card component pattern
- Q: How should card tools be implemented? → A: (2026-01-05 refactor) Use dedicated sub-components (`<c-card.actions.collapse />`, `<c-card.actions.maximize />`, `<c-card.actions.remove />`) controlled by boolean flags (`collapsible`, `removable`, `maximizable`). This avoids deeply nested conditionals and makes the template maintainable. The `tools` slot allows custom tools to be added.
- Q: Should card component use named slots? → A: (2026-01-05 refactor) No. Use standard Cotton slot pattern - `{{ tools }}` for tools area and `{{ slot }}` for body content. Named slots add unnecessary complexity. Footer functionality removed to keep component focused.
- Q: How should card header always render? → A: (2026-01-05 refactor) Header always renders (even if empty) to provide consistent structure for tools. Icon and title are optional within the header.
- Q: Why add a `compact` attribute to the card component? → A: To support zero-padding for tables, maps, and full-width content (applies `p-0` class to card-body)
- Q: Why restore the footer slot in card v2.1 after removing it in v2.0? → A: Users needed a place for action buttons and card controls
- Q: How should card header icons be styled for proper visual hierarchy? → A: Flexbox layout (`d-flex align-items-center`) with icon in separate wrapper, default classes `me-2 fs-5 text-muted`, customizable via `icon_class`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Display Statistical Data with Info Boxes (Priority: P1)

Developers need to display key metrics and statistics in a dashboard using info boxes that show an icon, label, and value with optional progress indicators.

**Why this priority**: Info boxes are the most common widget for displaying KPIs and metrics in admin dashboards, making them essential for the MVP.

**Independent Test**: Can be fully tested by creating an info box with icon, text, and number, and verifying it renders correctly with proper styling and accessibility attributes.

**Acceptance Scenarios**:

1. **Given** a page template, **When** developer uses `<c-info-box icon="gear-fill" text="CPU Traffic" number="10%" />`, **Then** an info box displays with icon from c-icon component, label, and number
2. **Given** an info box, **When** developer adds `variant="primary"` attribute, **Then** the info box icon background displays in primary color (default fill="icon" behavior)
3. **Given** an info box, **When** developer adds `progress="70"` and `description="70% Increase in 30 Days"` attributes, **Then** the info box displays with progress bar at 70% and description text using c-progress component
4. **Given** an info box, **When** developer applies `variant="primary" fill="box"` attributes, **Then** entire info box displays with colored background
5. **Given** an info box, **When** developer applies `variant="primary" fill="icon"` attributes (default), **Then** only the icon span displays with colored background
6. **Given** an info box, **When** developer applies Bootstrap utility class like `class="shadow-sm"`, **Then** the shadow styling applies correctly

---

### User Story 2 - Create Summary Cards with Small Boxes (Priority: P1)

Developers need to create prominent summary cards that display key metrics with icons, values, and action links for dashboard overviews.

**Why this priority**: Small boxes are the signature AdminLTE widget for displaying high-level metrics prominently, essential for effective dashboard design.

**Independent Test**: Can be fully tested by creating a small box with heading, description, icon, and footer link, verifying all elements render and are clickable.

**Acceptance Scenarios**:

1. **Given** a page template, **When** developer uses `<c-small-box heading="150" text="New Orders" icon="cart" />`, **Then** a small box displays with large heading, text, and icon from c-icon component
2. **Given** a small box, **When** developer adds `variant="primary"` attribute, **Then** the box displays with colored background
3. **Given** a small box, **When** developer adds `link="#"` and `link_text="More info"` attributes, **Then** the footer displays as clickable link with specified text at bottom
4. **Given** a small box with link, **When** no `link_text` is provided, **Then** the footer displays default text "More info"
5. **Given** a small box with icon attribute, **When** the icon name is provided (e.g., icon="cart"), **Then** the icon renders as decorative background using c-icon component

---

### User Story 3 - Build Flexible Content Cards (Priority: P2)

Developers need to create cards for organizing content sections with headers, bodies, and interactive tools like collapse/expand/maximize.

**Why this priority**: Cards provide flexible content containers but are secondary to metric-focused widgets for initial dashboard functionality.

**Independent Test**: Can be fully tested by creating a card with header and body, and verifying sections render with proper layout and optional tools work.

**Acceptance Scenarios**:

1. **Given** a page template, **When** developer uses `<c-card title="Card Title">Body content</c-card>`, **Then** a card displays with title in header and body content in default slot
2. **Given** a card, **When** developer adds `variant="primary"` attribute without fill, **Then** the card displays with primary colored outline (default fill="outline")
3. **Given** a card, **When** developer adds `variant="primary" fill="card"`, **Then** the entire card displays with primary background color
4. **Given** a card, **When** developer adds `icon="gear-fill"` attribute, **Then** the icon displays to the left of the header text
5. **Given** a card, **When** developer adds `collapsed` and `collapsible` attributes, **Then** the card renders in collapsed state with collapse tool button
6. **Given** a card, **When** developer adds `collapsible` attribute, **Then** `<c-card.actions.collapse />` component renders in tools area with proper AdminLTE collapse behavior
7. **Given** a card, **When** developer adds `removable` attribute, **Then** `<c-card.actions.remove />` component renders in tools area with proper AdminLTE remove behavior
8. **Given** a card, **When** developer adds `maximizable` attribute, **Then** `<c-card.actions.maximize />` component renders in tools area with proper AdminLTE maximize behavior
9. **Given** a card, **When** developer provides custom tools via `<c-slot name="tools">`, **Then** custom tools render alongside any automatic tool components
10. **Given** a card, **When** no title or icon provided, **Then** header still renders to maintain consistent structure for tools
11. **Given** a card with table content, **When** developer adds `compact` attribute, **Then** card-body has zero padding (`p-0` class) allowing table to extend to edges
12. **Given** a card, **When** developer provides footer content via `<c-slot name="footer">`, **Then** footer renders with optional `footer_class` for custom styling

---

### User Story 4 - Apply Consistent Styling Across Widgets (Priority: P3)

Developers need to apply consistent Bootstrap 5 color schemes and utility classes across all widgets for brand consistency.

**Why this priority**: Styling consistency is important but can be refined after core widget functionality is established.

**Independent Test**: Can be fully tested by applying Bootstrap color classes to each widget type and verifying consistent rendering.

**Acceptance Scenarios**:

1. **Given** any widget, **When** developer applies color attributes (`fill` for info-box and card, `variant` for small-box), **Then** the widget displays with corresponding Bootstrap background color (primary, success, warning, danger, info, secondary)
2. **Given** any widget with background color, **When** widget supports gradients (currently none do), **Then** the background displays with gradient effect
3. **Given** any widget, **When** developer applies Bootstrap utility classes like `class="shadow-sm"`, `class="shadow"`, `class="shadow-lg"`, **Then** the classes apply correctly to widget styling
4. **Given** any widget, **When** developer specifies icon name for c-icon component, **Then** the icon displays correctly

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an `info-box` component that displays an icon, text label, and numeric value
- **FR-002**: Info box MUST support optional icon-only colored background via `variant` attribute (primary, success, warning, danger, info, secondary); defaults to "default" in c-vars when omitted
- **FR-003**: Info box MUST support full-width colored background via `bg` attribute (primary, success, warning, danger, info, secondary)
- **FR-004**: Info box MUST support optional progress bar via `progress` attribute (percentage value) and `description` attribute (description text)
- **FR-005**: Info box MUST support gradient effect when `gradient` attribute is present with background color
- **FR-006**: Info box MUST accept icon via `icon` attribute passed to custom c-icon component with optional icon_class and data attributes
- **FR-007**: System MUST provide a `small-box` component that displays heading, descriptive text, and decorative icon
- **FR-008**: Small box MUST support optional colored backgrounds via `bg` attribute (primary, success, warning, danger, info, secondary); defaults to "default" in c-vars when omitted
- **FR-009**: Small box MUST support optional footer link via `link` and `link_text` attributes; `link_text` defaults to "More info" when omitted
- **FR-010**: Small box MUST accept icon via `icon` attribute passed to custom c-icon component with optional icon_class and data attributes
- **FR-011**: System MUST provide a `card` component with `title` attribute for header text, optional `icon` attribute for header icon, default slot for body content, and named slots for `footer` and `tools`
- **FR-012**: Card MUST support optional colored styling via `variant` attribute (primary, success, warning, danger, info, secondary); defaults to "default" in c-vars when omitted
- **FR-013**: Card MUST support `fill` attribute with values "outline" (default, applies variant to border), "header" (applies variant to header background), "card" (applies variant to entire card background); only applies when variant is not "default"
- **FR-014**: Card MUST display icon before header text when `icon` attribute is provided
- **FR-015**: Card MUST support collapsed state via `collapsed` attribute
- **FR-016**: Card MUST provide `tools` named slot for action buttons in header (collapse, remove, maximize)
- **FR-017**: Card tools MUST integrate with AdminLTE's JavaScript for collapse/expand functionality
- **FR-018**: Card tools MUST integrate with AdminLTE's JavaScript for remove functionality
- **FR-019**: Card tools MUST integrate with AdminLTE's JavaScript for maximize/minimize functionality
- **FR-020**: All widgets MUST use snake_case naming convention for Cotton components (c-info-box, c-small-box, c-card)
- **FR-021**: All widgets MUST support Bootstrap 5 color utilities and theme colors
- **FR-022**: All widgets MUST render semantic HTML with proper ARIA attributes for accessibility
- **FR-023**: All widgets MUST accept additional CSS classes via `class` attribute for applying Bootstrap utility classes
- **FR-024**: All widgets MUST declare all configurable attributes in `<c-vars>` to prevent attribute leakage to HTML
- **FR-025**: All color-related attributes MUST default to "default" value in `<c-vars>` when not provided

### Key Entities

- **Info Box Widget**: Displays statistical information with icon, text label, and numeric value. Supports optional progress indicators and various styling options including colored backgrounds via `variant` and `bg` attributes. Bootstrap utility classes can be applied directly for shadows and other styling.

- **Small Box Widget**: Displays prominent summary metrics with large heading, descriptive text, decorative background icon, and automatic footer link (via `link` and `link_text` attributes with "More info" default). Typically used for dashboard KPIs.

- **Card Widget**: Flexible container component with header (supporting optional icon), body, and optional footer sections. Supports interactive tools like collapse, remove, and maximize via named slots. Can be styled with colored outlines, headers, or full card backgrounds using `variant` and `fill` attributes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can create info boxes with under 5 lines of template code for common use cases
- **SC-002**: Developers can create small boxes with under 5 lines of template code for common use cases
- **SC-003**: Developers can create cards with under 8 lines of template code including tools for common use cases
- **SC-004**: All three widget types support all AdminLTE 4 color variations (minimum 6 theme colors)
- **SC-005**: Widgets match AdminLTE 4 reference implementation visual appearance exactly (Reference: <https://adminlte.io/themes/v3/pages/widgets.html>)
- **SC-006**: All widgets pass WCAG 2.1 AA accessibility compliance (matching AdminLTE 4 standards)
- **SC-007**: Widget components work correctly with AdminLTE JavaScript for interactive features (collapse, remove, maximize)
- **SC-008**: Components render correctly on all modern browsers (Chrome, Firefox, Safari, Edge)
- **SC-009**: Widget components are responsive and adapt to mobile, tablet, and desktop screen sizes
- **SC-010**: Documentation includes examples for all major widget variations
