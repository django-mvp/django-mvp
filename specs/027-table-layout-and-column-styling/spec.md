# Feature Specification: Full-screen tables and column styling helpers

**Feature Branch**: `027-table-layout-and-column-styling`

**Created**: 2026-08-17

**Status**: Draft

**Serves**: G10 (a consistent UI around the third-party packages projects already rely on), G1 (a complete, responsive application shell that a project configures rather than builds)

**Roadmap**: — (no item covers table presentation; R16 is the generic integrations item and is already marked delivered. Possible roadmap gap.)

**Issue**: #253

**Input**: A table rendered through the django-tables2 integration should behave like the main surface of an application rather than a card in a scrolling document, and the people writing tables should have documented classes for column behaviour plus sensible alignment they do not have to ask for.

## Clarifications

### Session 2026-08-17

Four ambiguities were found by the coverage scan and resolved from the intake discussion and the
project's constitution. Longer rationale is in `decisions.md`.

- **Q: Is the scrolling table area reachable and usable without a mouse, and how is it announced?**
  A: It is a labelled, keyboard-focusable scroll region. A `div` with overflow scrolling is not
  keyboard-scrollable in Firefox or Safari unless it is a tab stop, and Article XIII requires
  keyboard navigability plus an ARIA role where the markup alone does not convey one. Recorded as
  FR-025.

- **Q: How does the maximum-width behaviour carry its width — a fixed set of named classes, or a
  value the table author supplies?**
  A: A fixed set of named classes. An author-supplied value would have to be interpolated into an
  inline style attribute, which Article V rules out for author data and Article XI rules out as a
  raw-utility escape hatch, and the utility-class build cannot generate classes from values only
  known at runtime. This also settles what happens to the existing `min_height` attribute, which
  is the same pattern. Recorded in FR-012 and FR-026.

- **Q: Does the reusable table component change, or only the table view's page template?**
  A: Both, and they split cleanly. The component becomes the table area — the scroll container
  with its fixed heading and footer rows — because that is the part an embedder wants. The page
  template owns the bars around it. The component's `min_height` attribute is removed: a fixed
  height floor inside a container that now takes its height from its parent contradicts itself.
  That is a pre-1.0 public API change and is recorded in the changelog. Recorded as FR-026.

- **Q: What happens to a table wider than a phone screen?**
  A: It scrolls horizontally inside the table area, and the feature offers no alternative small-screen
  rendering. Article II asks for the simplest design that satisfies the spec, the list view already
  exists for card-style presentation of the same data, and turning a table into cards below a
  breakpoint is a separate feature with its own questions. Recorded in Assumptions and FR-011.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A table that fills the application shell (Priority: P1)

A developer has a model with more rows than fit on a screen and points a table view at it. The
page that comes back is the table: it occupies the space the shell gives it below the header,
and nothing else on the page competes for that space. Scrolling the rows does not scroll the
window. The column headings stay visible at the top of the table area no matter how far down the
rows the reader is, so the reader never loses track of which column they are looking at, and a
footer row of totals — where the table declares one — stays visible at the bottom for the same
reason. Above the rows is a bar carrying the page title on the left and the same actions a list
view offers on the right. Below them is a bar carrying the result count and the pagination
controls. Both bars stay put while the rows move.

**Why this priority**: It is the feature. Everything else here is a refinement of tables that
already render; this changes what a table view *is*. It also stands alone: the styling helpers
are useful with or without it, but the layout delivers on its own.

**Independent Test**: Load a table view with more rows than fit the viewport, scroll the rows to
the bottom, and confirm the window scroll position never moved, the column headings are still on
screen, and both bars are still in place. Repeat at a phone-sized viewport.

**Acceptance Scenarios**:

1. **Given** a table view whose rows exceed the viewport height, **When** the page loads, **Then** the table area spans from below the application header to the bottom of the viewport and the document itself does not scroll.
2. **Given** that page, **When** the reader scrolls to the last visible row, **Then** the column headings remain fixed at the top of the table area and the row beneath them is the one that has scrolled.
3. **Given** a table declaring column footers, **When** the reader scrolls, **Then** the footer row remains fixed at the bottom of the table area.
4. **Given** a table wider than the viewport, **When** the reader scrolls horizontally, **Then** the horizontal scrollbar belongs to the table area and the window gains no horizontal scrollbar.
5. **Given** a vertically scrollable table, **When** the reader looks at the scrollbar, **Then** it spans the full height of the table area rather than stopping at the fixed heading row.
6. **Given** a paginated table view, **When** the page loads, **Then** the result count and pagination controls are visible without scrolling.
7. **Given** a table view class, **When** it declares an ordering of its own, **Then** the developer is told that ordering belongs to the table rather than the view, instead of the declaration being silently ignored.
8. **Given** the same table view at a phone-sized viewport, **When** the page loads, **Then** the table area still fills the space below the header and the window still does not scroll.

---

### User Story 2 - Column behaviour a table author can choose (Priority: P2)

A developer writing a table has one column of long descriptive text, one of short codes, and one
of dates. Without the descriptive column, the table would lay out sensibly on its own; with it,
the text wraps to four lines and pushes every other row apart. They want to say, on the column
itself, that it should take up whatever slack is going and stay on one line, that the code column
should shrink to its content, and that the description should never exceed a stated width. They
say it the way django-tables2 already asks them to say things about a column — by naming classes
in the column's attributes — and they find those class names in the documentation rather than by
reading the package's stylesheet. A project that would rather have wrapping text everywhere sets
that once as a project-wide default instead of repeating it per column.

**Why this priority**: Useful on any table, including the ones that already render today, and
independent of the layout. It is second because a table that reads badly in a card also reads
badly full-screen — the layout is the bigger correction.

**Independent Test**: Build a table applying each class to a column, render it, and confirm the
rendered cells carry the behaviour. Set the project-wide wrap default both ways and confirm
columns follow it, and that a column-level class overrides it.

**Acceptance Scenarios**:

1. **Given** a column marked to grow, **When** the table renders in a container wider than its content, **Then** that column absorbs the spare width and the others keep their content width.
2. **Given** a column marked to shrink, **When** the table renders, **Then** the column is no wider than its widest cell needs.
3. **Given** a column marked not to wrap, **When** a cell's text exceeds the column width, **Then** the text stays on one line rather than wrapping the row taller.
4. **Given** a column marked with a maximum width, **When** a cell's content is wider, **Then** the column stops at the stated width.
5. **Given** the project-wide wrap default set to off, **When** a table renders with no column-level wrap class, **Then** its text columns stay on one line.
6. **Given** the project-wide wrap default set to off and a column marked to wrap, **When** the table renders, **Then** that column wraps and the rest do not.
7. **Given** a developer reading the documentation, **When** they look for column styling, **Then** every class this feature ships is listed with what it does and an example of it in a column's attributes.

---

### User Story 3 - Alignment nobody had to ask for (Priority: P3)

A developer builds a table from a model without saying anything about alignment. Text columns come
out left-aligned, numeric columns right-aligned so the digits line up down the column, and boolean
and action columns centred. Where the shipped table template cannot tell what a column holds, it
leaves the column alone rather than guessing. A developer who disagrees with the choice says so in
the column's attributes and their choice wins.

**Why this priority**: It is polish on top of stories 1 and 2 and the only part of this feature
whose feasibility depends on what can be learned about a column at render time. If it does not
hold up, the other two stories ship without it and a table author sets alignment by hand using the
same mechanism story 2 documents.

**Independent Test**: Render a table over a model with text, numeric, boolean and action columns,
and assert the alignment each cell carries. Add an explicit alignment class to one column and
confirm it wins.

**Acceptance Scenarios**:

1. **Given** a column over a text-bearing model field, **When** the table renders, **Then** its cells are left-aligned.
2. **Given** a column over a numeric model field, **When** the table renders, **Then** its cells are right-aligned.
3. **Given** a boolean column, **When** the table renders, **Then** its cells are centred.
4. **Given** a column with no model field behind it, such as one rendering buttons, **When** the table renders, **Then** its cells are centred.
5. **Given** a table built over data with no model behind it at all, **When** it renders, **Then** no alignment is imposed and the table renders as it does today.
6. **Given** a column carrying an explicit alignment class in its attributes, **When** the table renders, **Then** the explicit class is what applies.
7. **Given** a column heading, **When** the table renders, **Then** the heading carries the same alignment as the cells beneath it.

---

### Edge Cases

- A table with no rows: the empty state occupies the table area, and both bars still render.
- A table view with pagination turned off: no pagination controls are rendered and no empty bar is left behind.
- A table with fewer rows than fit the viewport: the table area still fills the shell, the rows sit at the top of it, and nothing scrolls.
- A table declaring no column footers: no footer bar is rendered and the rows extend to the bottom of the table area.
- A table both taller and wider than its container: both scrollbars belong to the table area, and the fixed heading row moves horizontally with the columns it labels.
- A very narrow viewport where the action bar's title and actions cannot share a line: the bar stays fixed and its contents reflow within it rather than the bar growing without limit.
- A column carrying two contradictory behaviour classes, such as grow and shrink together: the outcome is stated in the documentation rather than left to stylesheet ordering.

## Requirements *(mandatory)*

### Functional Requirements

**Layout (US1)**

- **FR-001**: The table view MUST render as a page that fills the application shell, using the shell's existing opt-in for full-height content rather than a new mechanism.
- **FR-002**: The table area MUST own its own vertical and horizontal scrolling, and the browser window MUST NOT scroll on a table view page at any supported viewport.
- **FR-003**: The column heading row MUST remain visible at the top of the scrolling table area while rows scroll beneath it.
- **FR-004**: Where a table declares column footers, the footer row MUST remain visible at the bottom of the scrolling table area.
- **FR-005**: The table area's vertical scrollbar MUST span the full height of that area, including alongside the fixed heading and footer rows.
- **FR-006**: An action bar MUST sit above the table area, MUST NOT scroll with the rows, and MUST carry the page title on the leading side and the view's actions on the trailing side.
- **FR-007**: The table view's default action set MUST be the list view's action set minus sorting: search, filter and create.
- **FR-008**: A bar below the table area MUST carry the result count and pagination controls, and MUST NOT scroll with the rows. It MUST NOT render when the view is not paginated.
- **FR-009**: The table view class MUST NOT accept a declared ordering. A view that declares one MUST fail with a message naming the table as the place ordering belongs.
- **FR-010**: The table view MUST NOT wrap its table in a card, and the table area MUST extend to the edges of the space the shell gives it.
- **FR-011**: Every requirement above MUST hold at both desktop and phone viewport widths. A table wider than the viewport scrolls horizontally within the table area at every width; no alternative small-screen rendering is offered.
- **FR-025**: The scrolling table area MUST be reachable and scrollable by keyboard alone, and MUST carry an accessible name and a region role so that assistive technology announces it as a scrollable table region.
- **FR-026**: The reusable table component MUST become the table area itself — the scroll container with its fixed heading and footer rows — so that a page embedding it directly gets the same scrolling behaviour. Its existing minimum-height attribute MUST be removed, and its removal recorded in the changelog as a public API change.

**Column behaviour (US2)**

- **FR-012**: The package MUST ship classes that make a column grow to absorb spare width, shrink to its content, wrap its text, keep its text on one line, and stop at a maximum width. Maximum width MUST come from a fixed set of named classes, not from a value the table author supplies at runtime.
- **FR-013**: These classes MUST be applied through django-tables2's own column attributes. The feature MUST NOT introduce a column class, a registry entry, or any other surface a table author has to import or subclass.
- **FR-014**: `MVP_CONFIG` MUST carry a project-wide default for whether table text wraps, defaulting to not wrapping.
- **FR-015**: Resolution order MUST be column class, then `MVP_CONFIG`, then the package default.
- **FR-016**: Each shipped class MUST be documented with its effect and a usage example, and the documented set MUST match the shipped set.

**Inferred alignment (US3)**

- **FR-017**: The shipped table template MUST align a column according to the kind of data it holds: text leading, numeric trailing, boolean and action columns centred.
- **FR-018**: Where the kind of data cannot be determined, the template MUST impose no alignment.
- **FR-019**: An alignment class named in a column's attributes MUST override the inferred one.
- **FR-020**: A column heading MUST carry the same alignment as the cells beneath it.
- **FR-021**: Inference MUST NOT require a table author to declare anything, and MUST NOT change how a table renders when it cannot determine a column's kind.

**Across the feature**

- **FR-022**: The demo application MUST show the full-screen table, the column behaviour classes, and inferred alignment.
- **FR-023**: Changes to the default appearance of an existing table view MUST be recorded in the changelog as a behaviour change.
- **FR-024**: Any class this feature introduces MUST be present in the stylesheet the package ships, built from its source on the branch that introduces it.

### Key Entities

- **Table area**: the scrolling region holding the table, bounded above by the action bar and below by the pagination bar. It owns the scrolling that the window owns today.
- **Action bar**: the non-scrolling row above the table area, carrying the page title and the view's actions. Not the application header's tray, which stays empty and unclaimed.
- **Column behaviour class**: a named class a table author puts in a column's attributes to state how that column sizes itself and treats its text.
- **Column kind**: what a column holds — text, number, boolean, or an action — as far as the shipped table template can determine it at render time. Undeterminable is a valid answer with a defined outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a table view whose rows exceed the viewport, the window's scroll position is unchanged after the reader scrolls the rows from the first to the last, at both a desktop and a phone viewport.
- **SC-002**: The column heading row is within the visible table area at every scroll position, including the last, at both viewports.
- **SC-003**: A reader reaches the pagination controls of a table of any length without scrolling.
- **SC-004**: A table view class declaring an ordering fails with a message that names where ordering belongs, rather than rendering with the declaration ignored.
- **SC-005**: Every column behaviour class the package ships appears in the documentation with an example, and every class in the documentation exists in the shipped stylesheet — checked in both directions.
- **SC-006**: A table built over a model with text, numeric, boolean and action columns renders each with its stated alignment, with no alignment declared by the author.
- **SC-007**: A table built over data with no model behind it renders byte-identically to how it renders before this feature.
- **SC-008**: Existing table views require no change to their view class or table class to gain the new layout, apart from removing any ordering they declare.

## Assumptions

- The shell's full-height content mechanism shipped in #251 is the mechanism this feature builds on. No new shell-level height plumbing is introduced.
- The application header's tray stays empty and unclaimed. The action bar belongs to the table's own layout, so a project's own use of the tray is unaffected.
- Sorting stays entirely with django-tables2's column headings. This feature adds no sorting interface of its own.
- django-tables2 remains an optional integration behind its existing guard, and is not promoted to a runtime dependency.
- Filtering behaves as it does for list views today; this feature changes where the control sits, not what it does.
- The table markup this feature changes is the package's own table template. A project that has replaced it keeps its own markup and gets the surrounding layout only.
- Column kind is determined from the model field behind a column where one exists. Numeric fields are not distinguishable from text by django-tables2's own column classes, so the model field is the source.
- A table too wide for a small screen scrolls horizontally. Turning a table into cards below a breakpoint is a separate feature; the list view already covers card-style presentation of the same data.
- Removing the reusable table component's minimum-height attribute is acceptable without a deprecation period. The package is pre-1.0, the attribute contradicts the container's new sizing, and Article XVI allows component API changes between minor versions with a changelog entry.
