# Decisions: The dropdown decided on evidence

Rationale too long to inline in `spec.md`, the rulings the maintainer gave for the whole of
roadmap item R29, and the assumptions made while specifying. The maintainer was not asked about
the assumptions in the second section. Each one can be overruled on the specification's pull
request.

## Given by the maintainer for R29

### G1. No compatibility aliases

Renamed components and attributes are breaking and are recorded in the changelog. Nothing in the
package translates an old name to a new one (FR-008, FR-013).

### G2. Every component the package keeps moves under `mvp.`

If the dropdown is kept it is `<c-mvp.dropdown>`, so that `<c-dropdown>` always means
daisy-cotton's and nothing depends on the order of the installed apps (FR-013).

### G3. Calls to daisy-cotton's components are isolated at the call site

Many daisy-cotton components declare attribute names that pick up a page variable of the same name
when the caller does not pass them. Every call this package makes to one passes Cotton's `only`
attribute. Content in a slot still sees the page's variables, which #433 proves with a test
(FR-009).

### G4. All of R29 ships as one breaking minor release

No feature under R29 cuts a release of its own (FR-027).

### G5. The dropdown is decided by the placement tests

The issue and the roadmap both say the dropdown is kept or replaced on the evidence of the
existing placement tests run against daisy-cotton's version (FR-001, FR-003).

## Given at review of this specification

### R1. The evidence comes from Chromium, Firefox and WebKit

The first draft took the evidence in the one browser the suite already runs in, which is Chromium.
That was sent back. Chromium is where CSS anchoring has been available longest, so a pass there
cannot show that a dropdown with no script holds where this package's script holds today.

The placement tests are run against daisy-cotton's dropdown in all three of Playwright's engines,
installed locally for the evidence run. Adoption needs both behaviours to pass in all three, and
the decision record gives the result and the version for each engine (FR-001, FR-003, FR-004).
The suite that runs on every change may stay on Chromium, so no workflow changes.

A browser older than those three current engines, with the popover but no CSS anchoring, remains a
documented limit under adoption (FR-022).

## Resolved while specifying

### D1. "The existing placement tests" means the whole browser test module

**Ambiguous:** `tests/test_components/test_dropdown_placement_e2e.py` holds two groups of tests.
One measures where the panel lands. The other reads the trigger's reported state. Only the first
is about placement in the narrow sense.

**Chosen:** both groups are the evidence (FR-002).

**Why:** the module is the one the issue points at, and the state reporting exists only because
this package's script takes the panel over. A replacement that lost it would be a step backwards
that the placement measurement alone would not catch.

### D2. The tests keep their assertions and may change their selectors

**Ambiguous:** the tests find the trigger and panel through this package's class names and a data
attribute its script reads. Run unchanged against daisy-cotton's markup they would fail before
measuring anything.

**Chosen:** the scenario and the assertions stay. How the test finds the two elements may change
(FR-001).

**Why:** a test that fails on a selector says nothing about placement, and the issue asks for
evidence about behaviour.

### D3. Reported state is read from the accessibility tree

**Ambiguous:** the current tests read `aria-expanded` as an attribute. A trigger wired to its
panel with the browser's popover attributes can report the same state to assistive technology with
no such attribute in the markup.

**Chosen:** the state the browser exposes is what counts (FR-002).

**Why:** the attribute was a means. Failing daisy-cotton's dropdown for reporting the state
natively would reject it for doing the job with less.

**Rejected:** requiring the literal attribute. That would force a script back in to write it,
which is the thing adoption is meant to remove.

### D4. Both behaviours must pass

**Chosen:** adoption needs both. Any failure keeps this package's dropdown (FR-003).

**Why:** the issue gives two outcomes and no middle one. Adopting daisy-cotton's dropdown and
adding a script to patch the failing half would leave the package maintaining a dropdown script
anyway.

### D5. Hover opening and trigger-width panels do not count as evidence

**Ambiguous:** this package's dropdown has `hover` and `full`. daisy-cotton's has neither. Nothing
in the issue says whether losing them blocks adoption.

**Chosen:** they do not. Under adoption both attributes are removed and recorded as breaking
(FR-008).

**Why:** the issue names the tests as the criterion. Inside the package `hover` is used only on
the demo page. `full` is used by the sidebar's user menu, where the calling template can size its
own panel. R29 also asks for one attribute vocabulary, daisy-cotton's.

**Open to veto:** if a panel that matches its trigger's width matters enough to keep, the right
place for it is a request on daisy-cotton, not a second dropdown here.

### D6. "Five custom triggers" means the five dropdowns the package ships

**Ambiguous:** four of the package's dropdowns pass their own trigger: the theme chooser, the list
sort action, the share menu and the sidebar's user menu. The language switcher uses the default
button. The demo page has two more custom triggers.

**Chosen:** the five shipped dropdowns are in scope, including the language switcher, and the demo
page is covered separately (FR-012, FR-023).

**Why:** the dropdown script's own comment counts "the five dropdowns this package ships", which
is the likeliest source of the number. Leaving the language switcher out would leave one caller on
a removed name.

### D7. Older browsers are a documented limit

**Chosen:** under adoption, a browser older than the three engines in R1, with the popover but no
CSS anchoring, opens the panel away from its trigger. The documentation says so, and it is not
tested (FR-022).

**Why:** the evidence in R1 covers every current engine. Holding the decision to browsers that
none of them still ships would keep the script for an audience that shrinks with each release.

### D8. The outcome is written as a decision record

**Chosen:** an entry under `docs/adr/` (FR-004).

**Why:** the question will be asked again when daisy-cotton or daisyUI changes its dropdown. The
answer has to be findable without reading a merged pull request.

### D9. A failing behaviour is reported to daisy-cotton

**Chosen:** if the dropdown is kept, the gap is raised on daisy-cotton's tracker and linked from
the decision record (FR-016).

**Why:** R29 says gaps found in daisy-cotton are raised there. It also gives a later contributor
the condition under which the decision can be revisited.

### D10. The kept dropdown changes its name and nothing else

**Ambiguous:** the kept dropdown could also take daisy-cotton's `placement` attribute in place of
`valign` and `halign`, so the two dropdowns read alike.

**Chosen:** only the name changes (FR-014).

**Why:** the issue says "keep this package's dropdown under its own name". Changing its attributes
as well would break every caller twice for no behaviour gained.

### D11. Panel contents are out of scope

**Chosen:** this feature changes how each dropdown is called and what its trigger is. The entries
inside the panels, and the menu and button components that draw them, belong to #435 and #438
(FR-021).

**Why:** those issues own the menu and button moves. Doing them here would put two features on the
same lines.

### D12. No prototype is needed before planning

**Chosen:** the feature goes straight to planning with no design prototype.

**Why:** it swaps one dropdown's markup for another's, like for like, and what must hold is
asserted by tests. Nothing in it needs judging by eye.
