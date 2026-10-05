# Decisions: The shell's hand-written daisyUI markup uses daisy-cotton's components

Rationale too long to inline in `spec.md`, and the ambiguities resolved while specifying.

The first part records what the maintainer settled for all of R29 before this specification was
written. The second part records the readings chosen while writing it, where the issue was silent.
The maintainer was not asked about those, so each one says what was chosen and why it is
defensible. They are the places to look first when reviewing.

## Settled by the maintainer for all of R29

### G1. Every component the package keeps is under the `mvp.` prefix

`<c-mvp.messages>`, `<c-mvp.app.footer>` and the rest. The icon is the one exception and stays at
`<c-icon>`, so it replaces daisy-cotton's plain icon everywhere, including inside daisy-cotton's
own components. This specification writes names in that form. The rename itself is #434.

### G2. A call to a daisy-cotton component passes Cotton's `only`

Many daisy-cotton templates declare attributes with common names (`class`, `items`, `text`,
`icon`, `variant`), and Cotton fills an attribute the caller did not pass from a page variable of
the same name. The rule for R29 is that every call this package makes to a daisy-cotton component
passes `only`, and the leak is not fixed upstream. #433 proves that content placed in a slot still
sees the page context under `only`. FR-015 states the behaviour this protects. The mechanism is
this decision.

### G3. Forms rendered from a Django form stay where they are

Form rendering stays with django-crispy-forms and django-mvp-forms. Only fields written out by
hand in a template move to daisy-cotton's form controls, and that is #439. This is why FR-007
leaves the list search input alone and FR-013 treats rendered forms and row sets as exceptions by
rule.

### G4. The stylesheet question does not block

The prebuilt stylesheet already scans all of daisyUI's components and utilities, so a daisyUI
component class is present whatever daisy-cotton builds at render time. What still needs care is
plain utilities daisy-cotton's templates write literally and breakpoint-prefixed forms such as a
drawer that opens from a given width. #433 owns that coverage. FR-017 holds this feature to the
result.

### G5. No compatibility aliases, one breaking release

Renamed tags and attributes are breaking and are recorded in the CHANGELOG. All of R29 gathers on
the main branch and ships as one breaking minor release. No feature under R29 cuts a release.
FR-016 follows from this.

## Resolved while specifying

### D1. This feature moves the drawer, #438 moves what is inside the sidebar

**Ambiguous:** #438 says the sidebar is drawn with daisy-cotton's "menu, submenu and drawer". #440
names the drawer too, and says in its dependency line that the drawer "is shared with the sidebar
work".

**Chosen:** the drawer element, with its toggle and overlay, belongs here. The menu, the rail and
the user menu belong to #438. If #438 has already moved the drawer when this feature is built,
this feature checks the drawer scenarios against it and changes nothing (FR-005).

**Why defensible:** #440 depends on #438, so whichever way #438's specification reads, the drawer
is settled by the time this feature starts, and FR-005 covers both outcomes. The scenarios in
Story 1 are worth keeping either way because they are the drawer's contract.

### D2. The package's own components keep their attributes and slots

**Ambiguous:** the issue says the pieces "should be composed from" daisy-cotton's components. It
does not say whether `<c-mvp.pagination>` and the others may change how they are called.

**Chosen:** they may not (FR-010).

**Why defensible:** the breaking changes of R29 belong to #434 (names) and #435 (attributes of the
basic components). This issue's stated gain is that fixes arrive without being made twice, which
needs no change to any caller. Keeping the surface still also means the packages built on this one
have nothing to do for this feature.

### D3. A gap in daisy-cotton is raised there and the piece waits

**Ambiguous:** the issue assumes each daisy-cotton component fits. Reading daisy-cotton 0.1.2
suggests some do not yet (see the assumptions in `spec.md`).

**Chosen:** raise the gap on daisy-cotton, leave that piece hand-written, record it as an exception
with the link (FR-012). SC-002 adds that if the piece is one of the six the issue names, the
blocking issue is linked from #440 before merge, so the shortfall is visible where the request was
made.

**Rejected:** writing the daisy-cotton component's root by hand around a default slot, or patching
the rendered element from a script. Both keep the markup in two places, which is what the feature
removes.

**Why defensible:** R29 says "gaps found along the way are raised there rather than worked around
here".

### D4. The feature covers thirteen pieces, not six

**Ambiguous:** the issue lists messages, footer, navbar, drawer, pagination and the filter badge.
Its title says "the shell's hand-written daisyUI markup".

**Chosen:** the six, plus the header row's loading indicator and sidebar toggle, the two search
groups, the theme switch, the data field hint and the hero banner. All of them are templates that
write a daisyUI component daisy-cotton provides.

**Why defensible:** the title and the roadmap deliverable are general, and the issue's list reads
as examples. Leaving the other seven out would leave the same duplication in place with no issue
tracking it.

### D5. A sweep and a check, at the lowest priority

**Ambiguous:** nothing in the issue says how anyone knows the job is finished.

**Chosen:** Story 5. The rest of the templates are checked, each remaining piece is moved, left to
its owning sibling feature or recorded, and the test suite fails on new hand-written markup
(FR-013, FR-014).

**Why defensible:** "fixes arrive without being made twice" stops being true the first time a
template writes the markup by hand again. It is P3 so that Stories 1 to 4 can be delivered and
reviewed without it. This is the decision most open to a veto: it adds a test that every later
template change has to satisfy.

### D6. Differences in rendered elements are accepted and recorded

**Ambiguous:** daisy-cotton's components do not render the same elements. Its navbar is a `nav`
with an accessible name, its toggle carries the switch role, its tooltip renders the hint as an
element, and its drawer orders the page before the sidebar.

**Chosen:** take them, keep every behaviour, and list each difference in the CHANGELOG (FR-011,
FR-016). Two are called out as edge cases because they affect assistive technology and keyboard
use: the header row and the breadcrumb trail both being navigation landmarks, and the order in
which the sidebar and the page are reached.

**Why defensible:** these differences are the accessibility work the issue wants the shell to
inherit. The package is pre-1.0 and its constitution allows markup to change in a minor release
with a CHANGELOG entry.

### D7. No sketch stage

**Chosen:** none. The feature swaps where markup comes from. Nothing is designed and no flow
changes, and every outcome is something a test can assert.

### D8. Goals

**Chosen:** G1 and G5, as the issue's footer claims. G1 because the frame of the shell is what
moves. G5 because the gain is the accessibility and polish work done once in daisy-cotton. G6 is
touched through FR-017 but is served by #433, not here.
