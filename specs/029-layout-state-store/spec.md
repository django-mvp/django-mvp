# Feature Specification: Layout state store and static responsive visibility

**Feature Branch**: `029-layout-state-store`

**Created**: 2026-09-14

**Status**: Draft

**Goals**: G1 (a complete, responsive application shell that a project configures rather than builds), G7 (customization that never dead-ends), G6 (no front-end build tooling required)

**Roadmap**: R1 — A configurable application shell. The visibility work also serves R10, which asks that every class the library builds at render time reach the stylesheet.

**Issues**: #346, #345

**Input**: The shell keeps its layout state in three disconnected places and publishes none of it, so a project's own markup cannot react to the shell it sits inside. Separately, three template tags build responsive visibility classes from the configured breakpoint at render time, which the stylesheet build cannot see and a safelist has to compensate for.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project's markup reacts to the shell's layout state (Priority: P1)

A project builds a page inside the packaged shell and wants one of its own elements to respond to
the shell around it: a floating action button that steps aside when the sidebar is open, a
secondary panel that yields to the expanded navigation, a toolbar that changes shape once the
header has stuck to the top of the viewport.

Today none of this is reachable. The sidebar's open state lives in a local expression on the
drawer element, the header's stuck flag lives in a second one on the header, and a third copy of
the sidebar's persisted default lives in a script that runs before either. A project can only
reach any of it by reimplementing the same logic against the package's internal markup, which
breaks the moment that markup changes.

This story publishes the shell's live layout state as one store the page can read.

**Why this priority**: This is the capability the feature exists for, and the other two stories
build on the surface it introduces. On its own it turns the shell from a black box into something
a project can compose against, which is what G7 asks for.

**Independent Test**: Put an element carrying a visibility expression against the store on a demo
page, drive the sidebar and the scroll position in a real browser, and watch the element follow.
No other story needs to land first.

**Acceptance Scenarios**:

1. **Given** a page rendered in the shell, **When** the page loads, **Then** the layout store
   exists and reports the sidebar's open state, its collapse mode and whether the header is
   currently stuck.
2. **Given** an element whose visibility is expressed against the store's sidebar open state,
   **When** the sidebar is opened and closed by any of the controls the shell already ships,
   **Then** the element follows each change.
3. **Given** a persistent sidebar that was left open on the previous visit, **When** the page is
   loaded again, **Then** the sidebar is open at first paint with no width animation, and the
   store agrees with what is on screen.
4. **Given** a page whose links navigate without a full page load, **When** a navigation replaces
   the page body, **Then** the store still reports the layout state correctly and elements bound
   to it keep working.
5. **Given** a browser with JavaScript disabled, **When** the page loads, **Then** the shell
   renders and the sidebar can still be opened and closed.

---

### User Story 2 - A project reads the shell's resolved configuration instead of re-deriving it (Priority: P2)

The same project now wants behaviour that depends on configuration rather than on live state:
something that only applies at or above the width where the sidebar becomes persistent, or that
changes according to which collapse mode the project chose.

The settings that decide all of this are resolved on the server, where per-page overrides have
already been applied. On the client nothing knows them. A project that needs the breakpoint has
to hard-code a pixel width that its own settings can change underneath it, and a project that
needs the collapse mode has to infer it from the package's class names.

This story puts the shell's resolved layout configuration on the same store, alongside a flag
saying whether the viewport is currently at or above the configured breakpoint.

**Why this priority**: It completes the store as an extension point, but the live state in US-1
is what makes the store worth having. A project can hard-code a breakpoint today and be wrong
only when the setting changes.

**Independent Test**: Render a page with a per-page breakpoint override, read the configuration
off the store in a browser, and confirm it reports the override and not the project default.
Resize across the breakpoint and confirm the viewport flag flips.

**Acceptance Scenarios**:

1. **Given** a project with layout settings of its own, **When** a page renders, **Then** the
   store reports the breakpoint, its width in pixels, the collapse mode, whether the header is
   sticky, and whether sidebar navigation is boosted.
2. **Given** a page that overrides the breakpoint for itself, **When** that page renders, **Then**
   the store reports the page's breakpoint, not the project-wide default.
3. **Given** a viewport below the configured breakpoint, **When** it is widened past that
   breakpoint, **Then** the store's viewport flag becomes true without a page reload, and false
   again when narrowed back.
4. **Given** the breakpoint is configured so the sidebar never becomes persistent, **When** a page
   renders, **Then** the store says so rather than reporting a pixel width that means nothing.

---

### User Story 3 - Responsive visibility comes from the stylesheet, not from classes built at render time (Priority: P3)

Four regions of the shell are shown at some viewport widths and hidden at others: the header's
two trailing regions, the sidebar toggle and site icon that the sidebar header duplicates, and
the Account Center's two copies of its navigation. Which width divides them is a project setting,
so the classes that express it are assembled at render time by three template tags.

A class assembled at render time is invisible to the stylesheet build. The package compensates
with safelist entries and a test that checks the entries still cover what the tags can produce.
That is three tags, four safelist entries and a test standing in for a rule that could simply be
written down once, and it is an instance of the failure R10 names as the sharpest threat to the
promise that the package needs no build tooling.

This story writes the rules into the stylesheet, keyed off the configured breakpoint as a
server-rendered attribute on the shell, and removes the tags.

**Why this priority**: It changes nothing a user sees and nothing a project can call — it lowers
the cost of the shell's existing behaviour. That makes it the slice worth deferring if the feature
has to be cut short, not the one worth leading with.

**Independent Test**: Render the shell at each supported breakpoint setting and each collapse
mode, with and without JavaScript, and confirm every region's visibility matches what the package
does today. Independent of the store: the rules are CSS, and the store is not consulted.

**Acceptance Scenarios**:

1. **Given** any of the supported breakpoint settings, **When** a page renders at a width below it
   and again at a width at or above it, **Then** each of the four regions is visible exactly where
   it is visible in the current package.
2. **Given** a browser with JavaScript disabled, **When** a page renders at any width, **Then**
   every region's visibility is the same as with JavaScript enabled.
3. **Given** the breakpoint is configured so the sidebar never becomes persistent, **When** a page
   renders at any width, **Then** the header's trailing actions are shown and the mobile copy is
   not, matching the current behaviour.
4. **Given** the sidebar collapses to an icon rail rather than sliding away, **When** the sidebar
   is open and again when it is collapsed at a width at or above the breakpoint, **Then** the
   navbar's toggle and site icon are hidden in both, as they are today.
5. **Given** a project that imports the package's stylesheet preset and builds its own CSS,
   **When** it builds, **Then** the rules are present without any safelist entry naming them.

---

### Edge Cases

- **A breakpoint value the package does not recognise.** Today every tag falls back to the `lg`
  behaviour rather than raising or emitting nothing. The replacement rules must do the same, or a
  typo in a project's settings silently hides part of its header.
- **The breakpoint set to `never` or `none`.** There is no width to key off, and the two header
  regions resolve asymmetrically today: the trailing actions are shown unconditionally and the
  mobile copy is hidden, so a project reads one set of actions rather than two stacked copies.
  Both the store's report and the stylesheet rules must preserve that asymmetry.
- **A page-level override that differs from the project default.** Both the store and the
  stylesheet rules must reflect the value the page resolved, not the project-wide setting.
- **JavaScript unavailable or still loading.** Nothing about the shell's first paint may depend on
  the store existing. The store reports state; it does not decide appearance.
- **A navigation that replaces the page body without a document load.** The store is reconstructed
  along with the markup, and must come back reporting the same state the user was looking at.
- **A project that overrides the shell's base template.** The attribute the stylesheet rules key
  off must be rendered by a component the project keeps, not by a template it is likely to replace,
  or an override silently loses the rules.
- **Two shells on one page.** The store is global and the drawer is not. Whichever element the
  store tracks has to be the one the packaged shell renders.

## Requirements *(mandatory)*

### Functional Requirements

**The store and the state it carries**

- **FR-001**: The package MUST register exactly one client-side layout store, under a documented
  name, available to every expression in a page rendered by the shell.
- **FR-002**: The store MUST report whether the sidebar is currently open.
- **FR-003**: The store MUST report the sidebar's collapse mode and whether the header is
  currently stuck to the top of the viewport.
- **FR-004**: The sidebar's open state MUST stay in agreement with the control the shell already
  uses to drive the drawer, in both directions: a change made through that control is reflected in
  the store, and a change written to the store drives the drawer.
- **FR-005**: The shell's appearance at first paint MUST NOT depend on the store having been
  created. Every value that decides what the first paint looks like MUST be resolved before it.
- **FR-006**: The persisted open state of a persistent sidebar MUST be defined in exactly one
  place, read by both the pre-paint resolution and the store.
- **FR-007**: The store MUST be restored to correct values after a navigation that replaces the
  page body without a document load.
- **FR-008**: A page with no JavaScript MUST still render the shell and allow the sidebar to be
  opened and closed.

**The configuration the store carries**

- **FR-009**: The store MUST report the shell's resolved layout configuration: the breakpoint at
  which the sidebar becomes persistent, that breakpoint's width in pixels, the collapse mode,
  whether the header is sticky, and whether sidebar navigation is boosted.
- **FR-010**: The reported configuration MUST be the value the page resolved, so that a per-page
  override is what the store reports.
- **FR-011**: The configuration MUST reach the client as data the server emits, not as values
  re-derived in script or read back off the package's class names.
- **FR-012**: Configuration values MUST be emitted through Django's escaping, never by hand-built
  string interpolation into a script.
- **FR-013**: The store MUST report whether the viewport is currently at or above the configured
  breakpoint, and MUST keep that report current as the viewport is resized.
- **FR-014**: Where the sidebar is configured never to become persistent, the store MUST report
  that rather than a pixel width.

**Responsive visibility**

- **FR-015**: The template tags `navbar_wide_only_class`, `navbar_narrow_only_class` and
  `sidebar_navbar_toggle_class` MUST be removed from the package.
- **FR-016**: The four regions those tags governed MUST take their visibility from rules in the
  package's stylesheet preset, selected by the configured breakpoint and collapse mode.
- **FR-017**: The configured breakpoint and collapse mode MUST reach those rules as attributes
  rendered by the shell, placed on an element that contains all four regions and that survives a
  project overriding the shell's base template.
- **FR-018**: The resulting visibility MUST match the current package exactly, for every supported
  breakpoint setting including `never`/`none`, for an unrecognised setting, and for both collapse
  modes.
- **FR-019**: None of the classes involved MUST be assembled at render time, and the safelist
  entries and safelist test covering the removed tags MUST be removed with them.
- **FR-020**: Visibility MUST be resolved by the browser without JavaScript.

**Public surface**

- **FR-021**: The store MUST be documented as a supported extension point, with at least one
  working example of a project reacting to the shell.
- **FR-022**: The removal of the three template tags MUST be recorded as a breaking change, with
  the replacement stated.
- **FR-023**: The demo application MUST show a project reacting to the shell through the store.

### Requirement coverage

Every requirement belongs to exactly one story, so a story that lands is a story that is finished,
documentation included.

| Story | Requirements |
|---|---|
| Foundational work every story reads | FR-011, FR-012 |
| US-1 — layout state on the store | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-021, FR-023 |
| US-2 — resolved configuration on the store | FR-009, FR-010, FR-013, FR-014 |
| US-3 — visibility from the stylesheet | FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-022 |

FR-011 and FR-012 govern how the configuration reaches the client at all. The payload they describe
has to exist before the store can read it and is built from the same resolver the stylesheet
attributes use, so it is delivered as shared groundwork rather than inside one story. Nothing was
added or dropped in the correction.

### Key Entities

- **Layout store**: the single client-side object carrying the shell's layout state and resolved
  layout configuration. Read by the shell's own regions and by a project's markup; a new part of
  the package's public surface.
- **Shell attributes**: the configured breakpoint and collapse mode, rendered onto the shell's
  root element so the stylesheet can select on them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project can make one of its own elements respond to the sidebar's open state by
  writing a single attribute, without reading package internals, duplicating a setting, or
  hard-coding a pixel width.
- **SC-002**: Every fact about layout state is declared in exactly one place. No value that
  decides the sidebar's open state or the header's stuck state is written down twice.
- **SC-003**: With JavaScript disabled, every region of the shell is visible at exactly the widths
  it is visible with JavaScript enabled, at all six breakpoint settings and both collapse modes.
- **SC-004**: The shell's first paint is unchanged from the current package at every breakpoint
  setting and both collapse modes, including no width animation on a load that restores a
  persisted sidebar.
- **SC-005**: The number of shell classes assembled at render time falls from four constructions
  to one, and the stylesheet preset carries no safelist entry for the removed three.
- **SC-006**: A consumer upgrading finds the removed tags and their replacement in the changelog,
  the documentation and the shipped skill.

## Assumptions

- The store is public surface from the day it lands: named, documented and subject to whatever
  deprecation policy the package settles on. That is what makes it worth building rather than an
  internal tidy-up, and it is how #346 is read.
- "App configuration" in #346 means the `layout` subtree of the package's configuration. The theme
  already reaches the client by its own mechanism, and the remaining settings are server concerns
  that nothing on the page reacts to.
- The drawer's existing control remains the thing that decides whether the sidebar is open, and
  the stylesheet keeps reacting to it directly. The store mirrors it. Making the store
  authoritative would put the sidebar's appearance behind the script's boot, which is the defect
  issue #178 was opened for.
- The package is pre-1.0, so the three tags are removed outright with a changelog entry rather
  than deprecated for a release. Neither tag is mentioned anywhere in the documentation today.
- The `{bp}:drawer-open` class stays assembled at render time. Unlike the three being removed, it
  is the drawer component's own published API, and replacing it would mean re-implementing that
  component's persistent-drawer rules in this package's preset to retire one safelist entry.
- Nothing the shell looks like changes. The visibility work is a substitution whose correctness
  condition is that no rendered page differs.

## Out of Scope

- Path-based layout overrides (#207) and the missing sign-in control below the breakpoint (#336),
  both of which touch the shell and are tracked separately.
- Any change to what the shell renders or how it looks.
- Any widening of the settings surface. No new configuration keys.
- Loading additional client-side plugins. The bundle's contents are unchanged.

## Clarifications

### Session 2026-09-14

- **Q**: Should responsive visibility move onto the store, as issue #345 proposes, so that regions
  are shown and hidden by script rather than by stylesheet rules?
  **A**: No. Script-driven visibility applies after the runtime has booted, and the bundle is
  deferred, so both regions would paint before being corrected — on every load and again on every
  boosted navigation. This package has already paid for that failure once: the blocking script in
  the sidebar exists solely because persisted state resolves after first paint (#178). Media
  queries resolve at paint, cost nothing, survive JavaScript being unavailable, and are what the
  rest of the library uses. The tags are removed, but the rules they built become stylesheet
  rules, not expressions. The store carries state and configuration only. (FR-016, FR-020, SC-003)

- **Q**: Is the sidebar toggle's own visibility tag in scope, given that neither issue names it?
  **A**: Yes. It builds its classes at render time from the same setting, against the same safelist
  block, for the same reason. Leaving it behind would retire two thirds of a mechanism and keep the
  safelist, the sync comments and the class construction it was meant to remove. (FR-015)

- **Q**: Are the tags deprecated for a release or removed outright?
  **A**: Removed outright. The package is pre-1.0 and says so, Article XVI permits it with a
  changelog entry, and no page of the documentation mentions either tag — a deprecation cycle would
  be announcing the withdrawal of something never advertised. (FR-015, FR-022)

- **Q**: Which element carries the attributes the stylesheet rules select on?
  **A**: An element rendered by a component rather than by the base template, containing all four
  regions. A project overriding the base template is a documented and expected extension, and an
  override that silently drops the rules would produce a shell whose header regions never hide.
  The spec states the constraint; which element satisfies it is a planning decision. (FR-017)

- **Q**: Does the store hold the whole configuration dictionary or part of it?
  **A**: The `layout` subtree only. Shipping the rest would publish settings that exist to be read
  on the server, widening the surface the package has to keep stable for no capability gained.
  (FR-009, assumption 2)

## Dependencies

- No new runtime dependency and no new client-side library. The store is built on the runtime the
  package already bundles.
- The JavaScript bundle is a committed build artifact (Article XV) and is rebuilt on this branch.
- The stylesheet is a committed build artifact and is rebuilt on this branch.
