# Feature Specification: The dropdown decided on evidence

**Feature Branch**: `037-dropdown-on-evidence`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G5 (a polished, modern look and feel out of the box), G6 (no front-end build tooling required to use the package)

**Roadmap**: R29 (the basic daisyUI components come from daisy-cotton)

**Issue**: #437

**Input**: daisy-cotton's dropdown positions itself with the browser's built-in popover and CSS
anchoring, and has no script. This package's adds Floating UI to flip and shift the panel. The
existing placement tests should be run against daisy-cotton's version. If they pass, adopt it and
drop the script. If they don't, keep this package's dropdown under its own name. Either way, the
five custom triggers are updated.

## Clarifications

### Session 2026-10-05

The coverage scan found five ambiguities. Each was resolved from issue #437, roadmap item R29, the
constitution and the two dropdowns' source. Longer rationale is in `decisions.md`.

- **Q: Which tests are "the existing placement tests", and what does running them against
  daisy-cotton's dropdown mean when they select elements by this package's markup?**
  A: They are the browser tests in `tests/test_components/test_dropdown_placement_e2e.py`. They
  protect two behaviours: a panel whose declared side has no room still opens fully inside the
  window, and the trigger tells assistive technology whether its panel is open. The scenario and
  what is asserted stay the same. Only the way the test finds the trigger and the panel may change,
  because daisy-cotton's markup differs. Recorded as FR-001 and FR-002.

- **Q: The current tests read the open state from an attribute this package's script writes.
  daisy-cotton's trigger uses the browser's own popover wiring, which can report the state without
  that attribute. Does that count as a failure?**
  A: No. What is measured is the state a screen reader is given, read from the browser's
  accessibility tree. An attribute is one way of supplying it and is not required. Recorded as
  FR-002.

- **Q: What if one behaviour passes and the other fails?**
  A: The dropdown is adopted only if both pass. Any failure keeps this package's dropdown.
  Recorded as FR-003.

- **Q: This package's dropdown can open on hover and can stretch its panel to the trigger's width.
  daisy-cotton's has neither. Do those count against adopting it?**
  A: No. The issue names the placement tests as the evidence and nothing else. If daisy-cotton's
  dropdown is adopted, both attributes are removed and recorded as breaking. Recorded as FR-008.

- **Q: The issue says five custom triggers. Which five?**
  A: The five dropdowns the package ships: the theme chooser, the language switcher, the list
  page's sort action, the share menu and the sidebar's user menu. Four pass their own trigger and
  the language switcher uses the default one. All five are in scope. Recorded as FR-012.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The choice between the two dropdowns is made by the placement tests (Priority: P1)

A maintainer has two dropdowns to choose from. This package's own moves its panel with a script
when the declared side has no room. daisy-cotton's leaves that to the browser and ships no script.
Rather than argue it, the maintainer points the placement scenarios the package already has at
daisy-cotton's dropdown on the demo's dropdown page and reads the result. Both behaviours pass and
daisy-cotton's is adopted, or one fails and this package's stays. The result is written down where
a later contributor will find it, with which behaviour passed and which did not.

**Why this priority**: Everything else in this feature follows from this result. Until it exists
there is nothing to build.

**Independent Test**: On the demo's dropdown page, render daisy-cotton's dropdown in the "open
direction" scenario, scroll its trigger to the foot of the window and open it. Read where the panel
landed and what state the trigger reports. The recorded outcome matches what the run showed.

**Acceptance Scenarios**:

1. **Given** daisy-cotton's dropdown declared to open below its trigger, **When** the trigger sits
   at the foot of the window with less room below it than the panel needs and is opened, **Then**
   the run records whether the panel opened with all four edges inside the window.
2. **Given** the same dropdown, **When** it is closed, opened and dismissed with the Escape key,
   **Then** the run records whether the trigger reported closed, open and closed again to assistive
   technology.
3. **Given** both behaviours passed, **When** the outcome is recorded, **Then** it says
   daisy-cotton's dropdown is adopted.
4. **Given** either behaviour failed, **When** the outcome is recorded, **Then** it says this
   package's dropdown is kept and names the behaviour that failed.
5. **Given** the outcome is recorded, **When** a contributor looks for why the package has the
   dropdown it has, **Then** they find a decision record in the repository stating the outcome and
   the evidence.

---

### User Story 2 - If the tests pass, the package uses daisy-cotton's dropdown and ships no dropdown script (Priority: P1)

The tests passed. A developer writing `<c-dropdown>` in a project now gets daisy-cotton's
component, with its attributes. This package no longer has a dropdown of its own, and the script
that positioned it and the positioning library it loaded are gone from the bundle the package
ships. Someone using a page opens a dropdown near the bottom of the window and it still opens
where they can read it.

This story is built only when the outcome of User Story 1 is to adopt.

**Why this priority**: It is one of the two possible deliverables, and exactly one of them is
built.

**Independent Test**: Render every page of the demo and the package's shell. No template calls a
dropdown component owned by this package, the shipped script bundle carries no dropdown
positioning code, and the placement tests pass against the dropdowns on the page.

**Acceptance Scenarios**:

1. **Given** the outcome is to adopt, **When** a template calls `<c-dropdown>`, **Then** the
   component rendered is daisy-cotton's.
2. **Given** the outcome is to adopt, **When** the package's templates are searched, **Then** no
   dropdown component owned by this package exists.
3. **Given** the outcome is to adopt, **When** the shipped script bundle is inspected, **Then** it
   contains neither the dropdown script nor the positioning library, and the package's front-end
   dependencies no longer list that library.
4. **Given** the outcome is to adopt, **When** a dropdown whose declared side has no room is
   opened, **Then** the panel opens fully inside the window.
5. **Given** the outcome is to adopt, **When** a caller passes an attribute the old dropdown
   accepted and daisy-cotton's does not, **Then** nothing in the package translates it, and the
   changelog names the attribute as removed.
6. **Given** the outcome is to adopt, **When** this package calls daisy-cotton's dropdown,
   **Then** a page variable that shares a name with one of the dropdown's attributes does not
   change what is rendered.

---

### User Story 3 - If the tests fail, the package keeps its dropdown under its own name (Priority: P1)

A test failed. This package's dropdown stays, with its script and its behaviour unchanged, and it
is called `<c-mvp.dropdown>`. The plain `<c-dropdown>` name now belongs to daisy-cotton, so a
developer who writes it gets daisy-cotton's component and one who wants the panel that moves out
of the way writes the prefixed name. The shortfall that decided it is reported to daisy-cotton so
it can be closed there.

This story is built only when the outcome of User Story 1 is to keep.

**Why this priority**: It is the other possible deliverable, and exactly one of them is built.

**Independent Test**: Render `<c-mvp.dropdown>` and `<c-dropdown>` side by side. The first is this
package's component and passes the placement tests. The second is daisy-cotton's. An issue on
daisy-cotton describes the failing behaviour.

**Acceptance Scenarios**:

1. **Given** the outcome is to keep, **When** a template calls `<c-mvp.dropdown>`, **Then** this
   package's dropdown is rendered with the attributes and slots it has today.
2. **Given** the outcome is to keep, **When** a template calls `<c-dropdown>`, **Then**
   daisy-cotton's dropdown is rendered, whatever the order of the installed apps.
3. **Given** the outcome is to keep, **When** the placement tests run against
   `<c-mvp.dropdown>`, **Then** they pass as they do today.
4. **Given** the outcome is to keep, **When** daisy-cotton's issue tracker is read, **Then** an
   issue describes the behaviour that failed and how to reproduce it.
5. **Given** the outcome is to keep, **When** the changelog is read, **Then** it records the
   dropdown's new name as a breaking change.

---

### User Story 4 - The package's own five dropdowns work with whichever dropdown survives (Priority: P2)

Someone using a project built on this package changes the theme, switches language, sorts a list,
shares a page and opens their user menu in the sidebar. Each of those is a dropdown the package
ships. After this feature each one still opens from its trigger by mouse and by keyboard, shows
the same choices, closes when dismissed, and stays inside the window. A developer reading those
five templates sees them call the surviving dropdown by its current name and attributes, with
nothing left over from the other one.

**Why this priority**: The decision is only finished when the package's own callers have moved.
It comes after the decision and the component because it depends on both.

**Independent Test**: On a shell page and a list page, open each of the five dropdowns with a
click and again with the keyboard. Each panel opens, holds its entries and closes on Escape. No
template in the package or the demo calls a dropdown name or attribute that no longer exists.

**Acceptance Scenarios**:

1. **Given** either outcome, **When** each of the five shipped dropdowns is opened by clicking its
   trigger, **Then** its panel opens and holds the same entries it held before this feature.
2. **Given** either outcome, **When** a trigger is focused and activated from the keyboard,
   **Then** its panel opens, and Escape closes it.
3. **Given** either outcome, **When** a panel is open, **Then** its trigger reports the open state
   to assistive technology.
4. **Given** either outcome, **When** the package's and the demo's templates are searched,
   **Then** every dropdown call uses a component name and attributes that exist after this
   feature.
5. **Given** the list page's sort action, **When** a sort order is chosen from its dropdown,
   **Then** the list is reordered as it is today.
6. **Given** the outcome is to adopt, **When** the trigger of any of the five is inspected,
   **Then** it is an element the browser's popover wiring can open a panel from.

---

### Edge Cases

- The demo's dropdown page stops declaring a side for the dropdown under test. The placement test
  must fail instead of passing on a panel that was never asked to open where there is no room.
- The declared side has room. The panel opens on that side under either outcome, and the placement
  test reports that its scenario did not exercise placement.
- A page holds two dropdowns with no identifier given. Under adoption each trigger opens its own
  panel and not the other's.
- A project overrides one of the five shipped templates with a copy that calls the old name or
  attributes. This is a breaking change the changelog must describe well enough for the project to
  fix its copy.
- Under adoption, a browser that has the popover but no CSS anchoring opens the panel without
  placing it beside its trigger. The documentation states which browsers place the panel.
- Under adoption, a dropdown inside a region that clips its overflow, such as a card or a
  scrolling table, still shows its whole panel.
- The demo page shows hover opening and a panel stretched to its trigger. Under adoption both
  demonstrations are removed along with the attributes.

## Requirements *(mandatory)*

### Functional Requirements

**Taking the decision**

- **FR-001**: The browser tests in `tests/test_components/test_dropdown_placement_e2e.py` MUST be
  run against daisy-cotton's dropdown, in the same scenario and asserting the same behaviour. The
  way the test locates the trigger and the panel MAY change to suit daisy-cotton's markup. What is
  asserted MUST NOT be weakened.
- **FR-002**: The evidence MUST cover two behaviours. First, a panel whose declared side has less
  room than it needs opens with all four edges inside the window and with an area a person can
  read. Second, the trigger reports closed, open and closed again to assistive technology as the
  panel is opened and dismissed. The second MUST be read from the state the browser gives
  assistive technology, so a trigger that reports it without a written attribute passes.
- **FR-003**: daisy-cotton's dropdown MUST be adopted if both behaviours pass, and this package's
  dropdown MUST be kept if either fails. No third outcome exists, and no behaviour outside those
  tests changes the outcome.
- **FR-004**: The outcome MUST be recorded in a decision record under `docs/adr/`, stating which
  dropdown the package uses, which behaviours passed and failed, and the versions of daisy-cotton
  and the browser the tests ran on.
- **FR-005**: Exactly one of the two outcomes MUST be built. The requirements for the other MUST
  NOT be built.

**If daisy-cotton's dropdown is adopted**

- **FR-006**: This package's dropdown component MUST be removed, and `<c-dropdown>` MUST resolve
  to daisy-cotton's.
- **FR-007**: The dropdown positioning script MUST be removed from the package's scripts, the
  positioning library MUST be removed from the package's front-end dependencies, and the shipped
  script bundle MUST be rebuilt without either (Article XV).
- **FR-008**: The attributes daisy-cotton's dropdown does not have (`valign`, `halign`, `hover`,
  `full`) MUST NOT be accepted or translated anywhere in the package. Callers state placement in
  daisy-cotton's own vocabulary.
- **FR-009**: Every call this package makes to daisy-cotton's dropdown MUST be isolated from the
  page's variables, so that a page variable sharing a name with one of the dropdown's attributes
  does not reach it. Content placed inside the dropdown MUST still see the page's variables.
- **FR-010**: The placement tests MUST remain in the suite, pointed at daisy-cotton's dropdown on
  the demo page, so a later daisy-cotton or daisyUI release that loses the behaviour is caught.
  The rendered-markup tests that pinned this package's dropdown MUST be removed, because the
  markup is no longer this package's contract.
- **FR-011**: The shipped stylesheet MUST carry every class the adopted dropdown and the five
  shipped dropdowns render, including each placement the package's templates use.

**If this package's dropdown is kept**

- **FR-013**: This package's dropdown MUST be reachable as `<c-mvp.dropdown>` and MUST NOT be
  reachable as `<c-dropdown>`, so that `<c-dropdown>` is daisy-cotton's in every project whatever
  the order of its installed apps. No alias for the old name is provided.
- **FR-014**: The kept dropdown MUST keep the attributes, slots, placement behaviour and reported
  state it has today, and its script and positioning library MUST stay in the shipped bundle.
- **FR-015**: Its rendered-markup tests and its placement tests MUST keep passing, pointed at the
  new name.
- **FR-016**: An issue MUST be raised on daisy-cotton describing the behaviour that failed, with
  the scenario that reproduces it, and the decision record MUST link to it.

**The package's own dropdowns**

- **FR-012**: The theme chooser, the language switcher, the list page's sort action, the share
  menu and the sidebar's user menu MUST each call the surviving dropdown by the name and
  attributes it has after this feature.
- **FR-017**: Each of the five MUST open from its trigger by pointer and by keyboard, hold the
  entries it held before this feature, close when dismissed, and report its open state to
  assistive technology.
- **FR-018**: Each of the five MUST keep its declared placement relative to its trigger: the side
  it opens on and the edge it aligns to are the ones it declares today.
- **FR-019**: Choosing an entry in each of the five MUST do what it does today: the theme changes,
  the language changes, the list is reordered, the share target opens and the user menu's links
  are followed.
- **FR-020**: Under adoption, each custom trigger MUST be an element the browser's popover wiring
  can open a panel from, and MUST be tied to its own panel so two dropdowns on one page never open
  each other's.
- **FR-021**: The entries inside the five panels are out of scope. This feature changes how each
  dropdown is called and what its trigger is. What the panels contain and which menu components
  draw them stay as they are.

**Shipping it**

- **FR-022**: The component reference and the placement note in the documentation MUST describe
  the surviving dropdown: its name, its attributes, how a custom trigger is written and what
  happens when the declared side has no room. Under adoption the note MUST also state which
  browsers place the panel beside its trigger.
- **FR-023**: The demo's dropdown page MUST show the surviving dropdown only, and every example on
  it and on any other demo page MUST render with the attributes that dropdown accepts.
- **FR-024**: The changelog MUST record the change as breaking: under adoption, the removed
  component, the removed attributes with what replaces each, and the trigger contract. If the
  dropdown is kept, its new name.
- **FR-025**: The component list in `CONTEXT.md` MUST name the dropdown the package has after this
  feature, or drop it from the list when the package no longer owns one.
- **FR-026**: The shipped skill for coding assistants MUST describe the surviving dropdown
  wherever it describes the dropdown today.
- **FR-027**: This feature MUST NOT cut a release. Its changes ship with the rest of R29 in one
  breaking minor release.

### Requirement coverage

| Story | Requirements |
|---|---|
| US1, the decision | FR-001, FR-002, FR-003, FR-004, FR-005 |
| US2, adopted | FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027 |
| US3, kept | FR-013, FR-014, FR-015, FR-016, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027 |
| US4, the five dropdowns | FR-012, FR-017, FR-018, FR-019, FR-020, FR-021 |

### Key Entities

- **Dropdown**: a trigger and a panel. The panel opens beside the trigger on a declared side and
  alignment, and closes when dismissed.
- **Declared placement**: the side of the trigger a dropdown prefers and the edge it aligns to, as
  written by the template that calls it.
- **Custom trigger**: a trigger the calling template supplies in place of the default button.
- **Placement tests**: the browser tests that open a dropdown whose declared side has no room and
  read where the panel landed and what state the trigger reported.
- **Decision record**: the document under `docs/adr/` that states which dropdown the package uses
  and the evidence for it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The package has one answer to "which dropdown do I use", written in a decision
  record with the test evidence, and a contributor can find it without reading the history.
- **SC-002**: After this feature `<c-dropdown>` renders daisy-cotton's dropdown in every project
  that installs the package, whatever order its apps are listed in.
- **SC-003**: If daisy-cotton's dropdown is adopted, the package ships zero lines of dropdown
  script and one fewer front-end dependency, and the placement tests pass.
- **SC-004**: If this package's dropdown is kept, its behaviour is unchanged under its new name,
  and the gap that decided it is on daisy-cotton's tracker.
- **SC-005**: All five dropdowns the package ships open by pointer and keyboard, stay inside the
  window and report their state, on every page that carries them.
- **SC-006**: No template in the package, the demo or the documentation calls a dropdown name or
  attribute that does not exist after this feature.
- **SC-007**: Every acceptance scenario for the outcome that is built is proved by a test that
  fails if the behaviour is removed.

## Assumptions

- daisy-cotton is installed and its components are covered by the shipped stylesheet before this
  feature is built (#433).
- The evidence is taken in the browser the package's browser tests already run in. A browser
  without CSS anchoring is a documented limit under adoption, not part of the evidence.
- The sidebar's user menu is rebuilt on daisy-cotton's menu components by #438. This feature
  changes only the dropdown that wraps it and its trigger.
- The buttons used as triggers and the menus inside the panels move to daisy-cotton's components
  under #435. This feature writes its triggers against whichever button exists when it is built.
- If the prefix move of the package's remaining components (#434) has already given the dropdown
  its `mvp.` name, the kept outcome needs no further rename and the adopted outcome removes the
  component from where it then lives.
- Packages built on this one that call `<c-dropdown>` with the old attributes are updated in their
  own repositories around the R29 release.
- No continuous integration workflow changes are needed. The placement tests already run where the
  package's browser tests run.
