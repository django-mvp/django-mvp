# Feature Specification: A side panel beside a page's content

**Feature Branch**: `042-page-side-panel`

**Created**: 2026-10-21

**Status**: Draft

**Serves**: G1 (a complete, responsive application shell that a project configures rather than
builds), G7 (customization that never dead-ends, from view configuration through component
override to a project's own CSS), G3 (a short path from a Django model to a working set of pages,
configured declaratively rather than written by hand)

**Roadmap**: none. No roadmap item covers page layout; this may be a gap in the roadmap.

**Issue**: #569

**Input**: Many pages need a narrow column beside their content that stays in view while the reader
scrolls: an "On this page" list on a documentation page, filters beside a list of results, related
links beside a record. Every project that wants one writes the same styles, guesses the height of
the sticky header, and works out on its own what the column should do on a phone. This feature
makes it part of the page. A developer fills one block with one component, and the component
carries the configuration: width, which side, how it lines up with the title, from which screen
width it is a column, and whether it sticks. Below that width it becomes a drawer opened by a
button the developer places, or it stacks with the content. Every list page puts the filters that
are not in its toolbar into this panel, which replaces the filter modal.

## Clarifications

### Session 2026-10-21 (intake and sketch)

The design was settled on a working prototype over four rounds of review before this
specification was written. Sam's rulings:

- **Q: Is the whole page a drawer, so that a panel can be added anywhere?**
  A: No. The drawer is part of the panel, so a page with no panel has no drawer and no extra markup.
  Sam's point stands that a project must be able to nest a drawer of its own anywhere; the shell's
  styles that reach into nested drawers are a defect tracked separately.

- **Q: Does the column start level with the page title or with the content under it?**
  A: Either, chosen per panel. Level with the title by default. Recorded as FR-005.

- **Q: Is "not shown on a narrow screen" a third behaviour beside the drawer and stacking?**
  A: No. It is a drawer with no button on the page to open it. Recorded as FR-008.

- **Q: Does a list page choose between a filter panel and the filter modal?**
  A: No. A list page always puts its non-toolbar filters in the panel, and the modal goes. A panel
  that is never a column gives the drawer the modal used to be. Recorded as FR-013 and FR-016.

- **Q: How is "never a column" written?**
  A: As `breakpoint=False`, not a string such as `"never"`. Recorded as FR-004.

- **Q: Where does a list page's panel start?**
  A: At the end side, level with the content, so it lines up with the toolbar and stays clear of
  the app's sidebar, which sits at the start. A panel a developer moves to the start aligns with
  the title instead. Recorded as FR-014.

### Session 2026-10-21 (coverage scan)

The coverage scan found five further ambiguities, each answered from the intake discussion and the
prototype. Longer rationale is in `decisions.md`.

- **Q: What happens to an open drawer when the window is widened past the breakpoint?**
  A: The drawer closes and the panel is the column. Nothing is left locked or hidden behind it.
  Recorded as FR-010.

- **Q: Can a page have two panels?**
  A: No. A page has one side block and one panel in it. A second side is a page layout of the
  project's own. Recorded as FR-001.

- **Q: What does a list page show when every filter is in the toolbar?**
  A: No panel and no button to open one, as there is no Filter button and no modal today. Recorded
  as FR-015.

- **Q: What does a column taller than the screen do?**
  A: It scrolls on its own, inside the space under the header, and the page scrolls as usual. A
  keyboard user can reach it and scroll it. Recorded as FR-007.

- **Q: What does the panel do on a page that fills the screen's height?**
  A: It is a column the height of the page, with no sticking, because such a page does not scroll.
  Recorded as FR-011.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer puts a side panel beside a page's content (Priority: P1)

A developer writing a long help page wants an "On this page" list beside it. They fill the page's
side block with a side panel, labelled "On this page", holding a list of links to the page's
headings. On a wide screen the list now sits in a column beside the text and stays under the header
while the reader scrolls. They make it narrower, move it to the other side and start it under the
title, each by setting one attribute on the panel. Their other pages, which fill no side block, are
unchanged.

**Why this priority**: It is the feature. Every other story uses the panel this one adds.

**Independent Test**: Render a page that fills the side block with a panel, and one that does not.
Confirm the first draws the panel beside the content as a named region, in the order its position
implies, and the second renders exactly as it did before this feature.

**Acceptance Scenarios**:

1. **Given** a page whose side block holds a panel, **When** the page renders on a screen at or
   above the panel's breakpoint, **Then** the panel is drawn as a column beside the content, and
   is a landmark region named by its label.
2. **Given** a page whose side block is empty, **When** the page renders, **Then** its markup is
   the same as before this feature: no wrapper, no drawer, no button.
3. **Given** a panel at the end side, **When** the page renders, **Then** the panel comes after the
   content in the document. **Given** a panel at the start side, **Then** it comes before the
   content. In both cases the page title comes first.
4. **Given** a sticky panel and a page longer than the screen, **When** the reader scrolls, **Then**
   the column stays in view directly under the header, whatever height the header has.
5. **Given** a panel that is not sticky, **When** the reader scrolls, **Then** the column scrolls
   away with the page.
6. **Given** a panel aligned with the title, **When** the page renders as a column, **Then** the
   column starts level with the title. **Given** one aligned with the content, **Then** the title
   spans the page and the column starts level with the content.
7. **Given** each of the panel's widths, **When** the page renders as a column, **Then** the panel
   fills the whole column, at either side.
8. **Given** a panel taller than the space under the header, **When** the page renders, **Then** the
   column scrolls on its own, and a keyboard user can move focus to it and scroll it.
9. **Given** a page that fills the screen's height with a panel, **When** it renders as a column,
   **Then** the panel is a column the height of the page and does not stick.

---

### User Story 2 - A user opens the panel on a narrow screen (Priority: P1)

Someone reading the help page on a phone sees a "Contents" button in the title row. They tap it and
the list slides in from the side of the screen with the page dimmed behind it. Focus is on its close
button. They tab through the links and focus stays inside the panel. They press Escape and the
panel closes, with focus back on the "Contents" button. On another page, the developer chose to
stack the panel with the content, and the reader on the phone finds it under the title, in the
page's own reading order.

**Why this priority**: Without it the panel is unusable on a phone. It is half of what makes the
panel a built-in rather than a desktop-only style.

**Independent Test**: In a browser at a width below the panel's breakpoint, open the panel by its
button, confirm focus and its containment, close it by Escape, by its close button and by the dimmed
page, and confirm focus returns to the button each time and the button reports whether the panel
is open.

**Acceptance Scenarios**:

1. **Given** a page below its panel's breakpoint with the panel's button on it, **When** the page
   renders, **Then** the panel is not shown and the button is.
2. **Given** that page, **When** the reader activates the button, **Then** the panel opens from its
   own side of the screen, the rest of the page is dimmed and cannot be reached, focus moves into
   the panel, and the button reports that the panel is open.
3. **Given** the open panel, **When** the reader presses Escape, activates the close button or
   activates the dimmed page, **Then** the panel closes, focus returns to the button, and the
   button reports that the panel is closed.
4. **Given** the open panel, **When** the reader presses Tab past its last control, **Then** focus
   stays inside the panel.
5. **Given** a page at or above its panel's breakpoint, **When** the page renders, **Then** the
   panel's button is not shown.
6. **Given** a page whose panel collapses into a drawer and which has no button for it, **When** it
   renders below the breakpoint, **Then** the panel is not shown and nothing in it can be reached.
7. **Given** a panel set to stack, **When** the page renders below its breakpoint, **Then** the
   panel is drawn at full width, under the title, before the content for a start panel and after it
   for an end panel, and no button is needed.
8. **Given** a panel set never to be a column, **When** the page renders at any width, **Then** the
   panel is a drawer.
9. **Given** an open drawer, **When** the window is widened past the breakpoint, **Then** the drawer
   closes and the panel is the column, and the page can be scrolled and reached as usual.

---

### User Story 3 - A user filters a list from a side panel (Priority: P2)

Someone looking for a featured product on a wide screen finds the list's search and sort in the
toolbar and every other filter in a column at the end of the page, lined up with the toolbar. They pick
a status and a price range in the column and apply them, and the list narrows. The search they had
typed is kept. The column scrolls with the page, with no scrollbar of its own, and its Apply button
stays in reach at the foot of the screen however many filters it holds. On a phone the same filters are behind a
"Filters" button in the toolbar, which shows how many of them are applied. The column's clear
action removes the filters in it and keeps the search and the sort.

**Why this priority**: It is the list page this feature was asked for, and it replaces the filter
modal. It depends on Stories 1 and 2.

**Independent Test**: On a list page whose filterset has toolbar fields and other fields, confirm
the other fields are in the side panel and not in a modal, apply values from the panel and confirm
the list is narrowed with the toolbar's values kept, confirm the button's count, and confirm the
clear action keeps the toolbar's values.

**Acceptance Scenarios**:

1. **Given** a list view whose filterset has fields not named for the toolbar, **When** the page
   renders, **Then** those fields are drawn in the side panel, at the end side, aligned with the
   content, and there is no filter modal.
2. **Given** that page, **When** the reader applies values from the panel, **Then** the list is
   narrowed by them, the toolbar's search and sort are kept, and the list returns to its first
   page.
3. **Given** a value changed in the toolbar, **When** the list updates, **Then** the values in the
   panel are kept.
4. **Given** filters applied from the panel, **When** the page renders, **Then** the panel's button
   shows how many of the panel's filters are applied, as the Filter button does today.
5. **Given** filters applied from both places, **When** the reader uses the panel's clear action,
   **Then** the panel's filters are removed and the toolbar's values and the sort are kept.
6. **Given** a list view whose filterset's fields are all named for the toolbar, **When** the page
   renders, **Then** there is no side panel and no button for one.
7. **Given** a developer who wants the filters always in a drawer, **When** they set the list's
   panel never to be a column, **Then** the filters are behind the button at every width.
8. **Given** a developer who sets the list panel's width, side or breakpoint on the view, **When**
   the page renders, **Then** the panel follows those settings.
9. **Given** a panel holding more filters than fit on the screen, **When** the reader scrolls the
   panel, **Then** its apply and clear actions stay in view at its foot.
10. **Given** a table page with a filterset, **When** the page renders, **Then** its non-toolbar
    filters are in the side panel in the same way.

---

### User Story 4 - A user is never left looking at content under the header (Priority: P3)

Someone follows a link from the "On this page" list to a heading halfway down, and the heading is
in view under the header rather than behind it. Someone tabbing through a long form never has the
focused field hidden under the sticky header. A developer writing a sticky element of their own can
place it under the header using the header's height, which the package publishes.

**Why this priority**: The panel's sticking needs the header's height, and the same value fixes
two problems readers already have on every page with a sticky header. It is small and depends on
nothing else.

**Independent Test**: In a browser, follow a link to an anchor below the fold and confirm the
target's top is below the header's bottom edge. Change the header's height and confirm the
published value follows it.

**Acceptance Scenarios**:

1. **Given** a page with a sticky header, **When** the reader follows a link to an element on the
   page, **Then** the element is scrolled to just under the header, not behind it.
2. **Given** the same page, **When** focus moves by keyboard to a control near the top of the
   screen, **Then** the control is not hidden under the header.
3. **Given** a header that changes height, for example when a tray opens, **When** it changes,
   **Then** the published height follows it.
4. **Given** a header that does not stick, **When** the page renders, **Then** the published height
   is zero.

---

### User Story 5 - A developer adds a side panel to a template of their own (Priority: P3)

A developer has a documentation page that does not extend the package's page template. They wrap
its title and content in the package's page layout and pass the panel to it, and the panel behaves
as it does on any other page.

**Why this priority**: The panel would otherwise be out of reach of any page with a layout of its
own, which is where Article XI says a developer goes when the defaults do not fit. It reuses
everything the first two stories build.

**Independent Test**: Render a template that uses the page layout directly with a panel and with
none, and confirm the same results as Story 1's first two scenarios.

**Acceptance Scenarios**:

1. **Given** a template that uses the page layout with a title, content and a panel, **When** it
   renders, **Then** the result is the same as a page built on the package's page template with the
   same panel.
2. **Given** a template that uses the page layout with no panel, **When** it renders, **Then** it
   draws the title and content and nothing else.

### Edge Cases

- A page whose title block a project has emptied still lays out the panel, beside the content.
- A page that overrides the whole content area of the package's page template replaces the layout
  with it; such a page gets a panel by using the page layout itself (Story 5).
- A panel with nothing in it but whitespace counts as empty, and the page renders as if the block
  were empty.
- A drawer panel's button on a page whose panel is set to stack is not shown.
- A field in the list panel whose widget is the developer's own, such as a Tom Select control, is
  submitted with the list's filter form like any other.
- Right-to-left documents: start and end follow the document's direction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package's page template MUST offer one side block. A page fills it with one side
  panel component. A page whose side block is empty MUST render as it did before this feature.
- **FR-002**: The side panel MUST be a landmark region named by a label the developer gives it, and
  MUST show that label as its heading.
- **FR-003**: The side panel MUST offer a width from a small fixed set, and a side, start or end.
  At or above its breakpoint it MUST be drawn as a column of that width on that side, filling the
  column.
- **FR-004**: The side panel's breakpoint MUST be one of the package's named screen widths from
  large upwards, defaulting to extra large, or `False` for a panel that is never a column.
- **FR-005**: The side panel MUST offer an alignment, title or content, defaulting to title, that
  decides whether the column starts level with the page title or with the content.
- **FR-006**: The page title MUST come first in the document. A start panel MUST come before the
  content and an end panel after it, so the reading and focus order follow the visual order.
- **FR-007**: A sticky panel MUST stay in view under the header while the page scrolls, and MUST
  scroll on its own when it is taller than the space under the header. That scrolling region MUST
  be reachable and named for a keyboard user. Sticky MUST be the default and MUST be possible to
  turn off.
- **FR-008**: Below its breakpoint, the side panel MUST either collapse into a drawer, the default,
  or stack with the content at full width in document order. A drawer MUST be shown only when the
  reader opens it, by a button the developer places anywhere on the page. A drawer with no button
  on the page MUST NOT be shown or reachable.
- **FR-009**: The open drawer MUST dim the rest of the page and make it unreachable, move focus into
  itself, keep focus inside itself, and close on Escape, on its close button and on the dimmed page,
  returning focus to the button that opened it. The button MUST report whether the drawer is open.
- **FR-010**: The button MUST NOT be shown when the panel is a column or stacks. An open drawer MUST
  close when the window is widened past the breakpoint.
- **FR-011**: On a page that fills the screen's height, the panel MUST be a column the height of the
  page and MUST NOT stick.
- **FR-012**: The package MUST offer the page layout as a component of its own, taking a title,
  content and a side panel, so a template that does not extend the page template can use it.
- **FR-013**: Every list page and table page with a filterset MUST draw the fields not named for the
  toolbar in a side panel. The filter modal MUST be removed.
- **FR-014**: A list page's side panel MUST default to the end side, with the extra large
  breakpoint, collapsing into a drawer, and scrolling with the page rather than sticking. Unless
  the developer sets its alignment, a panel at the end
  side MUST align with the content and a panel at the start side with the title. Its button MUST be
  in the toolbar where the Filter button is today, and MUST show the count of applied panel filters
  as the Filter button does.
- **FR-015**: A list page whose filterset has no field outside the toolbar MUST draw no side panel
  and no button for one.
- **FR-016**: A developer MUST be able to set a list page's side panel width, side, alignment and
  breakpoint, including `False`, from the view.
- **FR-017**: The fields in a list page's side panel and the fields in its toolbar MUST be submitted
  as one form. A value set in one place MUST be kept when the reader applies a change in the other.
  The panel's apply and clear actions MUST stay in view at the panel's foot. Its clear action MUST
  remove the panel's filters and keep the toolbar's values and the sort.
- **FR-018**: The package MUST publish the sticky header's current height as a CSS custom property,
  follow changes to it, and publish zero when the header does not stick.
- **FR-019**: A link to an element on the page, and keyboard focus moving to a control, MUST bring
  it into view under the sticky header rather than behind it.

### Key Entities

- **Side block**: The block of the package's page template that holds a page's side panel.
- **Side panel**: The component a page puts in its side block: a column on a wide screen, a drawer
  or a stacked block on a narrow one.
- **Panel button**: The button that opens a side panel's drawer, placed by the developer.
- **Page layout**: The component that lays a page's title, content and side panel out together.
- **Header height**: The sticky header's current height, published for anything that has to clear
  it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer adds an "On this page" panel to a page by filling one block with one
  component and writes no CSS of their own.
- **SC-002**: Every page that fills no side block renders the same markup as before the feature.
- **SC-003**: At every supported screen width a reader can reach everything in the panel, and a
  keyboard user can open, use and close it without a pointer.
- **SC-004**: On every list page with filters outside its toolbar, those filters are reachable in
  one action at every screen width, and in no actions at the panel's breakpoint and above.
- **SC-005**: No element reached by link or by keyboard is hidden behind the sticky header.
