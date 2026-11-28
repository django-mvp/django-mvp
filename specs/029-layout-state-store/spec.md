# Feature Specification: Static responsive visibility

**Feature Branch**: `029-layout-state-store`

**Created**: 2026-09-14

**Status**: Draft

**Goals**: G1 (a complete, responsive application shell that a project configures rather than builds), G6 (no front-end build tooling required)

**Roadmap**: R1 — A configurable application shell. The visibility work also serves R10, which asks that every class the library builds at render time reach the stylesheet.

**Issues**: #346, #345

**Input**: Three template tags built responsive visibility classes from the configured breakpoint at render time, which the stylesheet build cannot see and a safelist had to compensate for.

The shell's layout state, its arrangement and the sidebar that never collapses are described in
`specs/050-shell-layout-code`, which replaced the layout store this feature first delivered.

## User Scenarios & Testing *(mandatory)*

### User Story 3 - Responsive visibility comes from the stylesheet, not from classes built at render time (Priority: P3)

Some regions of the shell are shown at some viewport widths and hidden at others: the dock, the
header's own sidebar button where a project has no dock, and the search, a field on a wide
window and a button on a narrow one. Which width divides them is the sidebar's breakpoint, a project setting, so the
classes that expressed it used to be assembled at render time by three template tags.

A class assembled at render time is invisible to the stylesheet build. The package compensated
with safelist entries and a test that checked the entries still covered what the tags could
produce. That was three tags, four safelist entries and a test standing in for a rule that could
simply be written down once, and an instance of the failure R10 names as the sharpest threat to
the promise that the package needs no build tooling.

This story writes the rules into the stylesheet, keyed off the configured breakpoint as a
server-rendered attribute on the shell, and removes the tags.

**Why this priority**: It changes nothing a user sees and nothing a project can call — it lowers
the cost of the shell's existing behaviour.

**Independent Test**: Render the shell at each supported breakpoint setting, with and without
JavaScript, and confirm every region's visibility follows the breakpoint.

**Acceptance Scenarios**:

1. **Given** any of the supported breakpoint settings, **When** a page renders at a width below it
   and again at a width at or above it, **Then** each region is visible exactly on its side of the
   breakpoint.
2. **Given** a browser with JavaScript disabled, **When** a page renders at any width, **Then**
   every region's visibility is the same as with JavaScript enabled.
3. **Given** a sidebar whose behaviour keeps it a drawer at every width, **When** a page renders
   at any width, **Then** the regions meant for a narrow window are the ones shown.
4. **Given** a project that imports the package's stylesheet preset and builds its own CSS,
   **When** it builds, **Then** the rules are present without any safelist entry naming them.

### Edge Cases

- **A page-level override that differs from the project default.** The stylesheet rules must
  reflect the value the page resolved, not the project-wide setting.
- **A project that overrides the shell's base template.** The attribute the stylesheet rules key
  off must be rendered by a component the project keeps, not by a template it is likely to replace,
  or an override silently loses the rules.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-015**: The template tags `navbar_wide_only_class`, `navbar_narrow_only_class` and
  `sidebar_navbar_toggle_class` MUST be removed from the package.
- **FR-016**: The regions those tags governed MUST take their visibility from rules in the
  package's stylesheet preset, selected by the configured breakpoint.
- **FR-017**: The configured breakpoint MUST reach those rules as an attribute rendered by the
  shell, placed on an element that contains every such region and that survives a project
  overriding the shell's base template.
- **FR-018**: The resulting visibility MUST follow every supported breakpoint setting, including a
  sidebar that is a drawer at every width.
- **FR-019**: None of the classes involved MUST be assembled at render time, and the safelist
  entries and safelist test covering the removed tags MUST be removed with them.
- **FR-020**: Visibility MUST be resolved by the browser without JavaScript.
- **FR-022**: The removal of the three template tags MUST be recorded as a breaking change, with
  the replacement stated.

### Requirement coverage

| Story | Requirements |
|---|---|
| US-3 — visibility from the stylesheet | FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-022 |

The numbers are kept from the feature as delivered, so commits and tests that cite them still
point at the right requirement.

### Key Entities

- **Shell attributes**: the configured breakpoint, rendered onto an element of the shell so the
  stylesheet can select on it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-003**: With JavaScript disabled, every region of the shell is visible at exactly the widths
  it is visible with JavaScript enabled, at every breakpoint setting.
- **SC-005**: The stylesheet preset carries no safelist entry for the three removed tags, and no
  shell class is assembled at render time from the breakpoint.
- **SC-006**: A consumer upgrading finds the removed tags and their replacement in the changelog,
  the documentation and the shipped skill.

## Assumptions

- The package is pre-1.0, so the three tags are removed outright with a changelog entry rather
  than deprecated for a release. Neither tag is mentioned anywhere in the documentation.
- Nothing the shell looks like changes. The visibility work is a substitution whose correctness
  condition is that no rendered page differs.

## Clarifications

### Session 2026-09-14

- **Q**: Should responsive visibility move into script, as issue #345 proposes, so that regions
  are shown and hidden by script rather than by stylesheet rules?
  **A**: No. Script-driven visibility applies after the runtime has booted, and the bundle is
  deferred, so the regions would paint before being corrected, on every load and again on every
  boosted navigation. Media queries resolve at paint, cost nothing, survive JavaScript being
  unavailable, and are what the rest of the library uses. (FR-016, FR-020, SC-003)

- **Q**: Is the sidebar toggle's own visibility tag in scope, given that neither issue names it?
  **A**: Yes. It built its classes at render time from the same setting, against the same safelist
  block, for the same reason. (FR-015)

- **Q**: Are the tags deprecated for a release or removed outright?
  **A**: Removed outright. The package is pre-1.0 and says so, Article XVI permits it with a
  changelog entry, and no page of the documentation mentioned either tag. (FR-015, FR-022)

- **Q**: Which element carries the attribute the stylesheet rules select on?
  **A**: An element rendered by a component rather than by the base template, containing every
  region it governs. A project overriding the base template is a documented and expected
  extension, and an override that silently drops the rules would produce a shell whose regions
  never hide. The spec states the constraint; which element satisfies it is a planning decision.
  (FR-017)

## Dependencies

- No new runtime dependency and no new client-side library.
- The stylesheet is a committed build artifact and is rebuilt on the branch that changes it.
