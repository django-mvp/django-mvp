# Feature Specification: The shell's hand-written daisyUI markup uses daisy-cotton's components

**Feature Branch**: `040-shell-markup-from-daisy-cotton`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G1 (a complete, responsive application shell that a project configures rather than builds), G5 (a polished, modern look and feel out of the box)

**Roadmap**: R29

**Issue**: #440

**Depends on**: #435 (the basic components come from daisy-cotton) and #438 (the sidebar and user menus are built from daisy-cotton's menu)

**Input**: The shell still writes some daisyUI markup by hand. Messages should become a toast of
alerts, and the footer, navbar, drawer, pagination and list filter badge should be composed from
daisy-cotton's footer, navbar, drawer, join and indicator. Fixes to those pieces then arrive in
the shell without being made twice.

## Summary

django-mvp's templates write a number of daisyUI components out as raw markup: the wrapper around
the messages, the footer, the header row, the drawer that holds the sidebar, the joined groups in
the pager and the search boxes, the count pinned to the filter button, the theme switch, the hint
on a data field's label and the hero banner. [daisy-cotton](https://github.com/django-mvp/daisy-cotton)
ships a component for each of these. This feature has the package's own templates call those
components and stop repeating the markup.

Nothing about how a project calls django-mvp changes. The package's components keep their names,
attributes and slots, and a person using a page sees and does what they did before. What changes
is where the markup comes from, so an accessibility fix or a daisyUI upgrade made in daisy-cotton
reaches the shell on its own.

Component names in this document are written as they will be once #434 has moved the package's
own components under the `mvp.` prefix. `<c-mvp.app.footer>` is today's `<c-app.footer>`. A bare
name such as `<c-footer>` always means daisy-cotton's component.

## Clarifications

### Session 2026-10-05

The coverage scan found six ambiguities. Each was resolved from the issue, its sibling issues
under R29, the roadmap and daisy-cotton's published components. Longer rationale is in
`decisions.md`.

- **Q: #438 and this feature both name the drawer. Which one moves it?**
  A: This feature moves the drawer itself: the element that holds the sidebar beside the page,
  with its toggle and its overlay (`<c-mvp.layout.sidebar>`). #438 moves what is drawn inside the
  sidebar: the menu, the icon rail and the user menu. #438 is delivered first. If it has already
  moved the drawer, this feature confirms the drawer scenarios below still hold and changes
  nothing there. Recorded as FR-005.

- **Q: Does any attribute or slot of the package's own components change?**
  A: No. `<c-mvp.messages>`, `<c-mvp.pagination>`, `<c-mvp.section.hero>` and the rest are called
  exactly as before. This feature changes what they are built from. Recorded as FR-010.

- **Q: What happens when a daisy-cotton component cannot carry something the shell needs?**
  A: The gap is raised as an issue on daisy-cotton, that one piece stays hand-written, and it is
  added to a short list of recorded exceptions with a link to the issue. The shell is never bent
  to fit, and no workaround is built here. Recorded as FR-012.

- **Q: The package has two search boxes. Which does this feature cover?**
  A: Both, but not the same parts. The navbar search (`<c-mvp.actions.search>`) moves whole. On
  the list page's search, this feature moves the joined group and its submit button, and the
  input stays with #439, which owns every field written by hand in a template. Recorded as FR-007.

- **Q: The issue names six pieces. What does "the shell's hand-written daisyUI markup" cover
  beyond them?**
  A: Every template the package ships. The pieces named in the issue and the five more found by
  reading the templates are listed under FR-001 and are the core of the feature. After those, a
  sweep of the remaining templates moves what daisy-cotton can draw and records the rest, so the
  job has a visible end. Recorded as FR-013 and FR-014.

- **Q: daisy-cotton's components do not render the same elements as the markup they replace. Is
  that accepted?**
  A: Yes, where behaviour is kept. daisy-cotton's navbar is a navigation landmark, its toggle
  announces itself as a switch, and its tooltip renders the hint as an element assistive
  technology can read. Those are the fixes this feature exists to pick up. Each difference a
  project's own CSS, override or test could notice goes in the CHANGELOG. Recorded as FR-011 and
  FR-016.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The frame of every page is drawn with daisy-cotton's components (Priority: P1)

A person opens any page of a django-mvp project. The sidebar sits in its drawer, the header row
carries the sidebar toggle, the breadcrumb trail and the configured widgets, and the footer closes
the page. All three are now drawn with daisy-cotton's drawer, navbar and footer. The person
notices nothing: the sidebar opens and closes, remembers its state, and gives way to an overlay on
a narrow screen exactly as before.

**Why this priority**: The frame is on every page, so it is where a daisy-cotton fix reaches the
most people, and where a regression would be seen first. It is also the largest piece of
hand-written markup in the shell.

**Independent Test**: Render a shell page and exercise the sidebar at a wide and a narrow viewport.
The drawer, header row and footer come from daisy-cotton's components and every existing
behaviour of the frame still holds.

**Acceptance Scenarios**:

1. **Given** a shell page at or above the sidebar breakpoint, **When** the person uses the sidebar
   toggle, **Then** the sidebar closes or opens and the page content takes up the space.
2. **Given** a person closed the sidebar on a wide screen, **When** they load another page,
   **Then** the sidebar is already closed when the page first paints, with no visible opening or
   closing movement.
3. **Given** a shell page below the sidebar breakpoint, **When** the person opens the sidebar,
   **Then** it appears over the page, and activating the area outside it closes it again.
4. **Given** a person opened the sidebar on a narrow screen, **When** they return to a wide
   screen, **Then** the open state remembered for the wide screen is unchanged.
5. **Given** a project sets the sidebar breakpoint and collapse mode in `MVP_CONFIG`, or a page
   overrides them by attribute, **When** the page renders, **Then** the drawer follows the
   resolved values and the layout store reports the same values.
6. **Given** a page with a breadcrumb trail and configured navbar widgets, **When** it renders,
   **Then** the header row shows the trail and the widget list for the current width, and a page
   with no trail renders no breadcrumb navigation at all.
7. **Given** a request made through htmx is in flight, **When** the person looks at the header
   row, **Then** the loading indicator is shown, and it is hidden again when the request ends.
8. **Given** a project passes footer content and extra classes to `<c-mvp.app.footer>`, **When**
   the page renders, **Then** the content appears inside a footer landmark that carries those
   classes.
9. **Given** a page defines a variable whose name matches an attribute of daisy-cotton's drawer,
   navbar or footer, **When** the page renders, **Then** the frame is unaffected by it.

---

### User Story 2 - Messages appear as a toast of alerts (Priority: P1)

A person saves a record and the page tells them it worked. Django's messages are shown as alerts
stacked in daisy-cotton's toast. Each alert matches its message's level, can be dismissed when the
project asks for that, and goes away on its own after the configured delay.

**Why this priority**: The issue names it first, and messages are the shell's main way of
answering a person's action. An alert that is announced twice or not at all is a real defect, and
daisy-cotton's toast is written to avoid exactly that.

**Independent Test**: Queue one message of each level, render a shell page and check that each
message appears once, as an alert of the matching kind, inside the toast.

**Acceptance Scenarios**:

1. **Given** messages of several levels are queued, **When** a shell page renders, **Then** each
   message appears exactly once as an alert whose kind matches its level.
2. **Given** a message at the debug level, **When** the page renders, **Then** it appears as an
   informational alert.
3. **Given** `<c-mvp.messages>` is called with `dismissible`, **When** the person dismisses an
   alert, **Then** that alert is removed and the others stay.
4. **Given** a delay is set, **When** that time passes, **Then** the alert removes itself.
5. **Given** several alerts are showing, **When** assistive technology reads the page, **Then**
   each alert is announced once, by the alert itself and not a second time by its container.
6. **Given** the page context holds a variable named like one of the toast's or the alert's
   attributes, **When** the page renders, **Then** the messages are unaffected by it.

---

### User Story 3 - List pages keep their pager, search and filter count (Priority: P2)

A person works through a long list. The pager at the foot of the list, the search box above it and
the count pinned to the filter button are drawn with daisy-cotton's join, button and indicator.
The person pages, searches and filters as before.

**Why this priority**: List pages are the most used pages in a data-centric application, but the
markup here is smaller and already sits behind the package's own components, so the risk and the
gain are both lower than for the frame.

**Independent Test**: Render a list view with more than one page of results, a search term and an
applied filter, and check each control works and is drawn through daisy-cotton's components.

**Acceptance Scenarios**:

1. **Given** a list with more than one page, **When** the pager renders, **Then** it is a named
   navigation landmark holding a link for each page in the window, and each link keeps the current
   query string while changing only the page.
2. **Given** the person is on a page in the middle of the list, **When** the pager renders,
   **Then** the current page is marked as current for assistive technology and the others are not.
3. **Given** the person is on the first or last page, **When** the pager renders, **Then** the
   controls that would lead nowhere are disabled, cannot be reached with the keyboard and are not
   links.
4. **Given** a list with a single page, **When** it renders, **Then** no pager is drawn.
5. **Given** a project builds its own pager from `<c-mvp.pagination.wrapper>` and
   `<c-mvp.pagination.link>`, **When** it renders, **Then** it works with the same attributes and
   slots as before.
6. **Given** a searchable list, **When** the person submits the search box, **Then** the list is
   filtered by their term, the term is still in the box and any applied filters are kept.
7. **Given** filters are applied, **When** the list renders, **Then** the filter button shows how
   many are applied, and with none applied it shows no count.
8. **Given** the navbar search widget is configured, **When** the header row renders, **Then** the
   search input carries an accessible name.

---

### User Story 4 - The theme switch, data field hints and hero banner come from daisy-cotton (Priority: P3)

Three smaller pieces move the same way. The light and dark switch is daisy-cotton's toggle, the
hint on a data field's label is daisy-cotton's tooltip, and the hero banner is daisy-cotton's hero
container holding the package's own heading, subtitle and actions.

**Why this priority**: These are three small pieces. Each gains something from daisy-cotton's
version, the tooltip most of all, but none is on every page.

**Independent Test**: Render each of the three and check it behaves as before and is drawn through
daisy-cotton's component.

**Acceptance Scenarios**:

1. **Given** a project with the default pair of themes, **When** the person uses the theme switch,
   **Then** the page changes theme and the choice is still in effect on the next page.
2. **Given** the theme switch renders, **When** assistive technology reads it, **Then** it is
   announced as a switch with an accessible name.
3. **Given** a data field with help text, **When** it renders, **Then** the help text is present
   as a hint tied to the label and readable by assistive technology, and a data field without help
   text renders no hint.
4. **Given** a hero section with a background image, a dimming strength and a minimum height,
   **When** it renders, **Then** the image, the dimming at that strength and the height are all
   applied.
5. **Given** a hero section with no background image, **When** it renders, **Then** no dimming
   layer is drawn.
6. **Given** a hero section is given the `top`, `actions` and `bottom` slots, **When** it renders,
   **Then** each appears in its place around the heading.

---

### User Story 5 - Nothing hand-written is left behind without a reason (Priority: P3)

A maintainer wants to know the job is finished and will stay finished. After the named pieces have
moved, the rest of the package's templates are checked. Anything daisy-cotton can draw is moved,
and anything it cannot is written down with the reason. From then on, a template that starts
writing one of daisy-cotton's components by hand is caught before it merges.

**Why this priority**: The point of the feature is that a fix is made once. That only stays true
if new hand-written markup cannot slip back in, but the earlier stories deliver their value
without this one.

**Independent Test**: Add a template that writes a daisy-cotton component out by hand and run the
test suite. It fails and names the template. Remove the template and it passes.

**Acceptance Scenarios**:

1. **Given** the package's templates after this feature, **When** they are checked for daisyUI
   components written by hand, **Then** every one found is on the recorded list of exceptions.
2. **Given** a contributor adds a template that writes out by hand a component daisy-cotton
   provides, **When** the test suite runs, **Then** it fails and names the template and the
   component.
3. **Given** an entry on the list of exceptions, **When** a reader looks it up, **Then** it states
   why the markup is hand-written, and where the reason is a gap in daisy-cotton it links to the
   issue raised there.
4. **Given** an exception whose markup has since been moved, **When** the test suite runs,
   **Then** it reports the entry as no longer needed.

---

### Edge Cases

- A project overrides one of the package's shell templates, for example its own
  `cotton/mvp/app/footer.html`. The override keeps working and keeps its own markup. Only the
  package's version changes.
- A project overrides daisy-cotton's component instead, for example its own `cotton/footer/index.html`.
  The shell then draws the project's version, which is what an override is for.
- The page context holds a variable named `class`, `items`, `side`, `start`, `end` or `open`.
  daisy-cotton's components declare attributes with those names, so the shell must not let the
  page's variable through.
- No messages are queued. The page renders with no alert, and nothing is announced.
- A message carries extra tags as well as its level. The alert's kind still follows the level.
- daisy-cotton's drawer places the page before the sidebar in the document, and the package's
  markup today places the sidebar first. A person moving through the page with the keyboard must
  still reach the sidebar's links, and the order they are reached in is recorded as a change if it
  differs.
- The header row holds the breadcrumb trail, which is a navigation landmark of its own. With the
  header row now a navigation landmark too, each must carry a name that tells them apart.
- The sidebar is collapsed to icons and a rail entry shows a tooltip. The tooltip must not be cut
  off by the drawer.
- A page uses `<c-mvp.page fill>`. The drawer's content region still lays out as the full-height
  column that page needs.
- The loading indicator in the header row is always in the document and only shown during a
  request. It must not be announced as loading while nothing is loading.
- The hero's dimming strength is set to zero. No dimming layer is drawn.
- A pager is given `use_icons` or `show_first_and_last`. The controls keep their accessible names
  either way.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package's templates MUST draw each piece below with the daisy-cotton component
  beside it, unless FR-012 applies to that piece.

  | Piece of the shell | Package component | daisy-cotton component |
  |---|---|---|
  | Wrapper around the messages | `<c-mvp.messages>` | toast, holding alerts |
  | Footer | `<c-mvp.app.footer>` | footer |
  | Header row | `<c-mvp.app.header.navbar>` | navbar |
  | Loading indicator in the header row | `<c-mvp.app.header.navbar>` | loading |
  | Sidebar toggle in the header row | `<c-mvp.app.header.navbar>` | drawer button |
  | Drawer holding the sidebar | `<c-mvp.layout.sidebar>` | drawer |
  | Pager | `<c-mvp.pagination>` and its `wrapper` and `link` | join, holding buttons |
  | Navbar search | `<c-mvp.actions.search>` | join, holding an input |
  | Group around the list search | `<c-mvp.page.list.actions.search>` | join, holding a button |
  | Count on the filter button | `<c-mvp.page.list.actions.filter>` | indicator, holding a badge |
  | Light and dark switch | `<c-mvp.actions.theme-controller>` | toggle |
  | Hint on a data field's label | `<c-mvp.data-field>` | tooltip |
  | Hero banner | `<c-mvp.section.hero>` | hero |

  *(Stories 1 to 4)*
- **FR-002**: The messages MUST each appear once, as an alert whose kind follows the message's
  level, with the debug level shown as informational. The `dismissible` and `delay` attributes
  MUST keep working. *(Story 2)*
- **FR-003**: The container around the messages MUST NOT announce them itself. Each alert is
  announced once, by the alert. *(Story 2)*
- **FR-004**: The drawer MUST keep every behaviour it has today: opening and closing from the
  header row, the sidebar header and the dock, the overlay below the sidebar breakpoint, the open
  state remembered at or above the breakpoint and applied before the page first paints, the
  breakpoint and collapse mode resolved from attribute then `MVP_CONFIG` then default, the values
  it publishes to the layout store, and navigation through htmx when `boost` is set. *(Story 1)*
- **FR-005**: The drawer itself belongs to this feature and the content of the sidebar belongs to
  #438. Where #438 has already moved the drawer to daisy-cotton's component, this feature MUST
  leave it as it is and confirm FR-004 against it. *(Story 1)*
- **FR-006**: The header row MUST keep showing the sidebar toggle, the site icon, the breadcrumb
  trail, the loading indicator and the widget lists under the same conditions as today, and the
  `right` slot MUST keep its place. Where the header row becomes a navigation landmark, it and the
  breadcrumb trail MUST carry different accessible names. *(Story 1)*
- **FR-007**: This feature MUST NOT change the input of the list search box, which #439 owns. It
  moves the group around it and its submit button. The navbar search moves whole. *(Story 3)*
- **FR-008**: The pager MUST keep its navigation landmark and accessible name, its page window,
  the marking of the current page, its disabled controls and the query string on each link.
  *(Story 3)*
- **FR-009**: The theme switch, the data field hint and the hero banner MUST keep the behaviour
  described in Story 4, including the hero's background image, dimming strength, minimum height
  and three slots. *(Story 4)*
- **FR-010**: The attributes and slots of the package's own components named in FR-001 MUST NOT
  change. No caller in the package, the demo or the documentation needs editing because of this
  feature. *(Stories 1 to 4)*
- **FR-011**: Accessible names, roles and states the shell provides today MUST still be provided.
  Where daisy-cotton's component adds one, such as the switch role on the toggle or a readable
  tooltip, the shell takes it. *(Stories 1 to 4)*
- **FR-012**: Where a daisy-cotton component cannot carry something a piece needs, that piece
  MUST stay hand-written, an issue describing the gap MUST be raised on daisy-cotton, and the
  piece MUST be added to the list of exceptions with a link to that issue. No workaround is built
  in this package, and no behaviour is given up to make a component fit. *(Stories 1 to 5)*
- **FR-013**: After the pieces in FR-001, every other template the package ships MUST be checked
  for daisyUI components written by hand. Each one found MUST be moved to daisy-cotton's
  component, left to the sibling feature that owns it (#436 for the card, modal and avatar, #437
  for dropdowns, #438 for the sidebar's content, #439 for fields), or added to the list of
  exceptions with its reason. Forms and row sets rendered from a Django form stay with
  django-crispy-forms and django-mvp-forms and are exceptions by rule. *(Story 5)*
- **FR-014**: The test suite MUST fail when a template the package ships writes out by hand a
  component daisy-cotton provides and is not on the list of exceptions, and MUST report an entry
  on the list that no longer matches any template. *(Story 5)*
- **FR-015**: A variable in the page context whose name matches an attribute of a daisy-cotton
  component the shell calls MUST NOT change what the shell renders, while content the shell places
  inside that component MUST still be able to read the page context. *(Stories 1 to 4)*
- **FR-016**: Every difference in rendered markup that a project's own stylesheet, template
  override or test could notice MUST be listed in the CHANGELOG under the unreleased breaking
  release that carries the rest of R29. This feature cuts no release of its own. *(Stories 1 to 5)*
- **FR-017**: Every page MUST render fully styled from the prebuilt stylesheet the package ships,
  with no build step in the project, including any class a daisy-cotton component the shell now
  calls writes at render time. *(Stories 1 to 4)*
- **FR-018**: The documentation that describes the pieces in FR-001 MUST describe what they are
  built from after this feature, and the demo MUST still show each of them. *(Stories 1 to 5)*

### Key Entities

- **List of exceptions**: the recorded set of places where a template the package ships still
  writes a daisyUI component by hand. Each entry names the template, the component and the reason,
  and links to an issue on daisy-cotton where the reason is a gap there.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All thirteen pieces listed in FR-001 are drawn with daisy-cotton's components, or
  appear on the list of exceptions with a linked issue on daisy-cotton. None is in neither state.
- **SC-002**: The six pieces the issue names (messages, footer, navbar, drawer, pagination, filter
  count) are drawn with daisy-cotton's components. If one cannot be, the issue blocking it is
  linked from #440 before this feature merges.
- **SC-003**: Every behaviour of the frame, the messages, the pager, the search boxes, the filter
  count, the theme switch, the data field and the hero that the test suite asserted before this
  feature is still asserted and still passes. No such assertion is removed without a CHANGELOG
  line explaining the difference.
- **SC-004**: No call to one of the package's own components in the package, the demo or the
  documentation changes its attributes or slots because of this feature.
- **SC-005**: A template that hand-writes a component daisy-cotton provides, outside the list of
  exceptions, fails the test suite. The number of such templates on the main branch is zero.
- **SC-006**: A fix released in one of the daisy-cotton components the shell now calls reaches the
  shell by upgrading daisy-cotton, with no template change in this package.
- **SC-007**: Every shell page in the demo renders styled from the prebuilt stylesheet alone.

## Assumptions

- #433, #434, #435 and #438 are delivered before this feature is built. daisy-cotton is
  installed, the prebuilt stylesheet covers its components, the package's own components are under
  the `mvp.` prefix, and a bare `<c-button>`, `<c-alert>` or `<c-badge>` already means
  daisy-cotton's.
- The messages already use an alert for each message. #435 makes that alert daisy-cotton's, so
  this feature only has the wrapper to move.
- daisy-cotton stays within the 0.1 series while R29 is delivered. A component it adds later is
  picked up through the check in FR-014 failing, not by reopening this feature.
- Reading daisy-cotton 0.1.2 suggests four places where FR-012 may apply: its drawer writes the
  toggle checkbox itself and gives a caller no way to put attributes on it, which the layout store
  and the remembered open state rely on. Its navbar's start and end sections take no classes of
  their own. Its hero's dimming layer takes no strength. Its drawer writes the page before the
  sidebar. Planning confirms each one. These are the likeliest issues to be raised on daisy-cotton.
- The sketch stage is not needed. This is a like-for-like change of where markup comes from, and
  its outcome is checked by tests.
- The packages built on django-mvp are not touched here. They call the package's own components,
  whose attributes do not change in this feature.
