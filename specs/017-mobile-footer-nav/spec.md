# Feature Specification: Mobile Footer Navigation

**Feature Branch**: `017-mobile-footer-nav`
**Created**: 2026-05-26
**Status**: Draft
**Input**: User description: "It is a common design pattern on mobile screensizes to have a footer navigation that sticks to the bottom of the viewport. The mobile navigation will be shown in mobile only mode using the .show-on-mobile class which syncs to the app's sidebar-expand-{bp} syntax. The nav items will be populated using a new django-flex-menus object specifically for this purpose (independent of the "AppMenu" menu). It will come prepopulated with a single menu item - a toggle to open the sidebar menu. We will also need a custom renderer to render links in a consistent manner. The link will follow standard bs5 nav items styling."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Adds Items to Mobile Footer Menu (Priority: P1)

A developer wants to populate the mobile footer navigation with links and actions relevant to their application. They register items with a dedicated mobile footer menu object — separate from the main AppMenu — so that the footer nav is independently configurable.

**Why this priority**: This is the core extension point of the feature. Without the ability to add items, the footer nav serves no purpose beyond the pre-populated sidebar toggle.

**Independent Test**: Can be fully tested by registering a new menu item on the `MobileFooterMenu` object, rendering the mobile footer nav template, and confirming the item appears in the rendered HTML with correct BS5 nav-item markup.

**Acceptance Scenarios**:

1. **Given** a developer registers a `MenuItem` on the `MobileFooterMenu`, **When** the mobile footer nav is rendered, **Then** the item appears as a BS5 nav-item link within the footer nav bar.
2. **Given** the `MobileFooterMenu` has multiple items registered, **When** the footer nav is rendered, **Then** all items appear in registration order.
3. **Given** a developer removes an item from the `MobileFooterMenu`, **When** the footer nav is rendered, **Then** the removed item no longer appears.

---

### User Story 2 - End User Sees Footer Nav on Mobile Only (Priority: P1)

An end user visiting the app on a small screen (mobile) sees a sticky footer navigation bar fixed to the bottom of the viewport. When the same user views the app on a tablet or desktop screen, the footer nav is hidden.

**Why this priority**: The visibility behavior is fundamental — without it the component either clutters larger screens or is invisible everywhere.

**Independent Test**: Can be fully tested by inspecting the rendered page: on a viewport narrower than the configured breakpoint the footer nav is visible; on a wider viewport it is hidden.

**Acceptance Scenarios**:

1. **Given** a user is on a mobile-sized viewport, **When** any page is loaded, **Then** the footer nav is visible and pinned to the bottom of the viewport.
2. **Given** a user is on a desktop-sized viewport, **When** any page is loaded, **Then** the footer nav is not visible.
3. **Given** a user resizes the browser from desktop to mobile width, **When** the breakpoint is crossed, **Then** the footer nav becomes visible without a page reload.
4. **Given** the footer nav is visible, **When** the user scrolls the page content, **Then** the footer nav remains fixed at the bottom of the viewport.

---

### User Story 3 - End User Taps Sidebar Toggle in Footer Nav (Priority: P2)

An end user on mobile taps the pre-populated sidebar toggle item in the footer nav, which opens (or closes) the application sidebar menu.

**Why this priority**: The sidebar toggle is the only default item and the primary use case that justifies adding this nav at all; however the footer nav is independently useful once developers add their own items.

**Independent Test**: Can be fully tested by tapping the sidebar toggle item and confirming the sidebar opens/closes as expected, independently of any custom items.

**Acceptance Scenarios**:

1. **Given** the sidebar is closed, **When** the user taps the sidebar toggle in the footer nav, **Then** the sidebar opens.
2. **Given** the sidebar is open, **When** the user taps the sidebar toggle in the footer nav, **Then** the sidebar closes.
3. **Given** the `MobileFooterMenu` has not been customised by the developer, **When** the footer nav is rendered, **Then** exactly one item (the sidebar toggle) is present.

---

### User Story 4 - Developer Uses Custom Renderer for Consistent Link Styling (Priority: P2)

A developer rendering mobile footer nav links relies on a custom renderer that automatically applies the correct BS5 nav-item structure and styling, so individual items don't need per-link template customisation.

**Why this priority**: Consistency and developer experience depend on the renderer, but the nav can still display items without it if links are styled manually.

**Independent Test**: Can be fully tested by confirming that every item rendered by the custom renderer produces valid BS5 `.nav-item > .nav-link` markup with the correct active state and icon support.

**Acceptance Scenarios**:

1. **Given** a menu item is rendered via the custom renderer, **When** the output HTML is inspected, **Then** the link wraps in a `.nav-item` element with a child `.nav-link` anchor.
2. **Given** the current page URL matches a menu item's URL, **When** the item is rendered, **Then** the `.nav-link` receives the `active` class.
3. **Given** a menu item defines an icon, **When** the item is rendered, **Then** the icon appears alongside the link label.
4. **Given** a menu item is rendered, **When** a developer inspects the output, **Then** styling is consistent regardless of which item or position it occupies.

---

### Edge Cases

- What happens when the `MobileFooterMenu` has no items registered (empty menu)?
- How does the footer nav behave when the sidebar toggle item is removed by the developer?
- What happens when a menu item URL is `None` or blank?
- How does the footer nav interact with browsers that do not support CSS `position: fixed` correctly (e.g., older iOS Safari)?
- What happens when a very large number of items are registered — does the footer overflow or scroll horizontally?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a `MobileFooterMenu` object that is independent of the existing `AppMenu` and can be populated with `MenuItem` instances using the same django-flex-menus API.
- **FR-002**: The `MobileFooterMenu` MUST come pre-populated with a single sidebar-toggle `MenuItem` out of the box, so no developer configuration is required to get a working default.
- **FR-003**: The footer nav component MUST be rendered using a Cotton (or equivalent template) component that applies the `.show-on-mobile` CSS class to synchronise its visibility with the app's `sidebar-expand-{bp}` breakpoint system.
- **FR-004**: The footer nav MUST be visually fixed to the bottom of the viewport on mobile screen sizes and MUST NOT be visible on screen sizes at or above the configured sidebar expand breakpoint.
- **FR-005**: The system MUST provide a custom renderer (compatible with django-flex-menus' renderer interface) that renders each `MenuItem` as a standard BS5 `.nav-item > .nav-link` structure.
- **FR-006**: The custom renderer MUST mark the active `.nav-link` with the BS5 `active` class when the item's URL matches the current request path.
- **FR-007**: The custom renderer MUST support optional icons on menu items, rendering the icon alongside the link label when present.
- **FR-008**: The sidebar toggle item pre-populated in `MobileFooterMenu` MUST trigger the app's existing sidebar open/close mechanism when activated.
- **FR-009**: Developers MUST be able to add, remove, or reorder items on `MobileFooterMenu` using standard django-flex-menus registration patterns.
- **FR-010**: The footer nav MUST render correctly when `MobileFooterMenu` is empty (no items), displaying nothing or a zero-height container rather than broken markup.

### Key Entities

- **MobileFooterMenu**: A django-flex-menus menu registry object scoped exclusively to the mobile footer navigation. Holds an ordered list of `MenuItem` instances. Independent of `AppMenu`.
- **MobileFooterMenuItem / MenuItem**: A single navigation entry in the footer nav. Has a label, URL (or action trigger), optional icon, and active-state logic.
- **MobileFooterNavRenderer**: A custom django-flex-menus renderer that produces BS5-compliant `.nav-item > .nav-link` HTML for each registered `MenuItem`.
- **Mobile Footer Nav Component**: A Cotton (or equivalent) template component that wraps the rendered menu items in the sticky footer markup and applies `.show-on-mobile` for responsive visibility.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The footer nav is visible on viewports narrower than the app's sidebar-expand breakpoint and hidden on viewports at or above it — verifiable by automated visual regression or browser resize test.
- **SC-002**: The sidebar toggle opens and closes the sidebar in 100% of test cases across supported mobile browsers.
- **SC-003**: Every item rendered by the custom renderer produces structurally valid BS5 nav-item markup, verifiable via automated HTML assertion in the test suite.
- **SC-004**: Developers can add a custom item to `MobileFooterMenu` and see it appear in the rendered footer nav with zero additional template changes.
- **SC-005**: The footer nav remains pinned to the bottom of the viewport during page scroll on all tested mobile device profiles.
- **SC-006**: An empty `MobileFooterMenu` produces no visible broken UI — the footer nav area either collapses completely or is hidden.

## Assumptions

- The app already has a `sidebar-expand-{bp}` CSS class convention and the `.show-on-mobile` utility class will be defined (or already exists) to toggle visibility at that breakpoint.
- django-flex-menus is already installed and integrated into the project; the `MobileFooterMenu` will follow the same registration and rendering API as existing menus.
- Bootstrap 5 is the CSS framework in use; nav-item link styling follows standard BS5 `.nav-item > .nav-link` conventions.
- The sidebar open/close mechanism (triggered by the pre-populated toggle item) already exists in the application and can be triggered via a CSS class toggle, data attribute, or equivalent JS mechanism.
- Icons, if used on menu items, are from the icon library already available in the project (e.g., Font Awesome or Bootstrap Icons).
- The feature is targeted at the django-mvp project's base layout; integration into other layouts is out of scope for this specification.
- Server-side rendering is the primary delivery mechanism; no client-side-only dynamic menu loading is required.
