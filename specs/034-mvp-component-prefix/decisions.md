# Decisions: Every component this package keeps moves under the mvp. prefix

Rationale too long to inline in `spec.md`, and the ambiguities resolved while specifying. D1 to D6
are the maintainer's rulings for roadmap item R29, recorded as given. D7 to D15 were resolved
while writing the specification, without a question being put to the maintainer, and are open to
his veto.

## Rulings given by the maintainer

### D1. Every component the package keeps moves under `mvp.`

**Chosen:** `<c-mvp.card>` resolves to `cotton/mvp/card.html`, and likewise for every kept
component (FR-001).

**Why:** Cotton resolves `<c-a.b>` to `cotton/a/b.html` in the first installed app that has it.
Two packages using plain names means app order decides which component a tag reaches. A prefix
makes the owner visible in the tag and takes app order out of it.

**ADR:** docs/adr/0030-the-packages-components-carry-a-prefix.md

### D2. The icon keeps its bare name

**Chosen:** the icon stays at `cotton/icon.html` (FR-003).

**Why:** daisy-cotton's icon does no lookup. Its own decision record expects a project that wants
lookup by name to place a component at the same path, above daisy-cotton in `INSTALLED_APPS`, so
that every caller picks it up, daisy-cotton's own components included. This package's icon is
that replacement. Under a prefix it would stop reaching daisy-cotton's callers.

**ADR:** docs/adr/0030-the-packages-components-carry-a-prefix.md

### D3. No compatibility aliases, and no release from this feature

**Chosen:** old names are removed outright (FR-005). The change is recorded as breaking in the
changelog and ships with the rest of R29 in one minor version (FR-017).

**Why:** the packages built on this one should move once. An alias at the old name would also
recreate the collision the prefix removes, because the old names of the card, modal, avatar,
dropdown and menu entry are daisy-cotton's names.

**ADR:** none — a release-policy choice for this change; the no-alias rule itself is in the record for D1

### D4. The basic components are not renamed

**Chosen:** the components #435 removes stay at their bare names until then (FR-004).

**Why:** renaming them here and removing them in #435 would break the same tags twice. Left
alone, a caller changes once, when the daisy-cotton component takes over the name.

**ADR:** none — temporary; it ends when #435 removes the basic components

### D5. The card stays in this package

**Chosen:** `<c-mvp.card>` is a kept component for the whole of R29.

**Why:** it adds a header row and footer that daisy-cotton's card does not have. Whether it
belongs in an extension package is a later question.

**ADR:** none — a scope ruling for this roadmap item, revisited later

### D6. The constitution's article on components is amended in this feature's pull request

**Chosen:** Article XI gains the prefix rule, the icon exception and the statement that basic
daisyUI components come from daisy-cotton (FR-015).

**Why:** the article currently says only that component templates live under
`mvp/templates/cotton/`. After this feature that is no longer the whole rule, and a constitution
that disagrees with the code is worse than none. The constitution says its changes are
human-gated and not made mid-feature. The maintainer asked for this amendment as part of this
feature, which is the gate.

**ADR:** none — the amendment is the constitution's own text

### D6a. The rule against raw utility classes covers this package's own components only

**Chosen:** the amended Article XI keeps its rule that a template demonstrating a component uses
attributes and not raw utility classes, and scopes it to components this package owns (FR-015).
Given as a ruling after the specification was approved, when the work on #435 raised it.

**Why:** daisy-cotton documents a class as the way to set a few of its components' options, the
overlap of an avatar group being one. Once the basic components come from daisy-cotton, a
template that follows daisy-cotton's own documentation would otherwise break this package's
constitution.

**ADR:** none — the amendment is the constitution's own text

## Resolved while specifying

### D7. The issue's closing claim is true only once #435 lands

**Ambiguous:** the issue says that once this lands a bare name always means daisy-cotton's
component. D4 leaves sixteen basic component templates at bare names in this package.

**Chosen:** the specification promises what this feature can deliver alone: no kept component
shares a name with a daisy-cotton component, the icon excepted (FR-007, SC-002). It says plainly
that the wider statement completes with #435.

**Why defensible:** promising the wider statement here would either pull #435's removals into
this feature or leave a success criterion that fails on the day it merges.

**ADR:** none — about what this feature's specification promises, nothing downstream inherits it

### D8. Which components count as kept

**Ambiguous:** the issue names seven groups and three components. The package ships others it
does not mention: the layout pieces (container, grid, group, toolbar, backdrop, rule, text,
section), the data field, messages, pagination, the entrance pages, the placeholder card, the
addons, the documentation block, the dropdown, and four menu parts.

**Chosen:** everything moves except the icon and the components #435 names. The full list is in
the specification's tables.

**Why defensible:** the roadmap item states the rule as "every component this package keeps",
and the issue's list reads as examples of it. The dropdown and the four menu parts move even
though #437 and #438 may later replace them, because until then they are this package's
components and two of them (dropdown, menu entry) carry a daisy-cotton name. daisy-cotton's own
templates call its menu entry, so leaving this package's at the bare name would put a narrower
component underneath them.

**ADR:** none — the list of what moved is in the specification and the changelog

### D9. The single-field form component moves, although #439 removes it

**Chosen:** `c-form.field` becomes `c-mvp.form.field`.

**Rejected:** leaving it at the bare name as a component about to be removed, the way the basic
components are.

**Why:** the basic components stay put because a daisy-cotton component takes over the same name.
Nothing takes over `form.field`: it is deleted, and its callers switch to different components.
Leaving it would split the form group across two namespaces for no saving.

**ADR:** none — the component is removed by #439

### D10. A component directory can be split

**Chosen:** the avatar moves and the avatar group stays. Four menu parts move and the menu
container stays. The application's dock region moves and the dock component stays.

**Why defensible:** it follows from D4 and D8 applied one component at a time. The split is
temporary: #435 removes the half that stays.

**ADR:** none — temporary; the split ends when #435 removes the staying halves

### D11. Component names in settings are written in full

**Ambiguous:** the navbar's widget lists in `MVP_CONFIG` hold component names. The issue does not
say whether a project keeps writing the short name.

**Chosen:** a name in a setting is used as written. The defaults change to the prefixed names.
(FR-008, FR-009)

**Rejected:** adding the prefix for the project. The same list can hold a project's own component
or one of daisy-cotton's, so the package cannot know which names to prefix without guessing.

**Rejected:** translating the old names with a warning. That is an alias, which D3 rules out.

**ADR:** docs/adr/0030-the-packages-components-carry-a-prefix.md

### D12. Stale overrides and stale tags are not detected

**Ambiguous:** a project's override at an old path silently stops applying, and for five names it
starts overriding daisy-cotton's component. A startup check could find such files.

**Chosen:** no check. The changelog entry names the five components and says overrides move with
their component (FR-012).

**Why defensible:** this feature is a rename with no new behaviour, and a check that walks a
project's template directories for a fixed list of old paths is new machinery that exists to
soften one upgrade. The constitution asks for the simplest design that satisfies the
specification. The maintainer can overrule this by asking for the check, which would be a small
addition.

**ADR:** none — a decision not to build something; the changelog carries what a project needs

### D13. The testing fixtures are not changed

**Chosen:** the fixtures go on rendering the name they are given. Their documented examples use
the new names. (FR-011)

**Why defensible:** they are a pass-through to Cotton and hold no component names of their own
outside their examples.

**ADR:** none — nothing changed

### D14. A guard keeps new components under the prefix

**Chosen:** the test suite fails when a component template sits outside the prefix and is not on
the exception list (FR-016).

**Why defensible:** without it the rule holds only until the next component is added from habit.
The exception list doubles as the record of what #435 still has to remove.

**ADR:** none — the guard is recorded as a consequence in the record for D1

### D15. No design review ahead of the build

**Chosen:** the feature is built without a prototype stage.

**Why defensible:** no page changes. Every packaged page is required to return the same response
as before (SC-003), which a test can decide.

**ADR:** none — a process choice for this feature

## Resolved while planning

### D16. Records are not rewritten

**Ambiguous:** FR-013 says every page under `docs/` uses the new names, and SC-006 says no old
tag remains in the documentation. `docs/adr/` and `docs/ROADMAP.md` are under `docs/` and mention
moved components by their old names 14 times between them.

**Chosen:** the decision records under `docs/adr/`, the roadmap, the released sections of the
changelog and everything under `specs/` are left as written. Every page a reader follows to use
the package is updated.

**Why defensible:** a decision record says what was decided in the words of its day, and the
roadmap's R29 entry describes this rename in terms of the old names, so rewriting either would
make it say something false. The documentation gate already treats `docs/adr/` as records, not
pages.

**Revisit if:** the maintainer reads SC-006 as covering the records too. It is a scripted
change of 14 mentions.

**ADR:** none — about this pull request's scope

### D17. The rename script is not committed

**Chosen:** the script that moves the files and rewrites the names is written for this change,
kept outside the repository and discarded.

**Why:** it is correct for exactly one commit of this repository. The rule it applies is in
`plan.md`, and the guard test keeps the result true afterwards.

**ADR:** none — local to this feature

### D18. "The same response as before" is shown while building, not by a committed test

**Chosen:** SC-003 is demonstrated by a before-and-after capture of every component's and every
demo page's output, compared during the build and recorded in `progress.md`, and by the existing
markup tests passing with only their names changed.

**Why:** a test in the suite cannot see the commit before it. A stored snapshot of every page
would be a change detector of the kind the testing standard rules out.

**ADR:** none — local to this feature

### D19. The constitution goes to 5.1.0

**Chosen:** the amendment to Article XI is a minor version: a rule is added and one is scoped,
and none is removed or reversed.

**ADR:** none — a version number

### D20. The stories are built in order, in one worktree, and the settings default moves in the first

**Chosen:** US1 to US4 run one after another in the feature's worktree. The default navbar
widget names change in US1's commit, although FR-008 is listed under US2.

**Why:** the move has to leave the suite green, and the default widget list names two components
that move. US2 then adds the tests and the documentation for how a name in a setting is written.

**ADR:** none — build order, local to this feature

## Design review, 2026-10-05

One reviewer, three lenses. Verdict: changes requested, one high finding. Every finding was
verified against the code before it was acted on.

### D21. The htmx form mixin's default component moves with the form

**Found:** `HtmxFormMixin.htmx_form_component` defaults to `"form"`, a packaged component name
held as a Python string. Research had said the file named none. After the move a view using the
default would fail on an invalid htmx post, and no test would notice.

**Chosen:** the default becomes `"mvp.form"` in the same commit as the move, with a test that
posts an invalid form through a view that sets no component of its own. The changelog and
`docs/integrations.md` say so.

**ADR:** none — a correction to the plan; the rule it follows is in the record for D1

### D22. Findings carried into the build

- The demo's own settings list packaged navbar widgets and are read by no test: edited by hand,
  and the demo is rendered under its own settings before and after the move.
- The test for the default widget list reads the default from the configuration module and
  never from a literal in the test.
- The comparison with daisy-cotton is run once during the build against the published 0.1.2
  wheel, before and after the move, since it is skipped until #433 installs the package.
- Paths the tests build with `pathlib` and widget names in monkeypatched lists are on the
  hand-edit list.
- A sentence asking for fixture examples to be rewritten beyond what FR-011 asks was dropped.

**ADR:** none — review findings, local to this feature

### D23. Two points are the maintainer's and go to the merge gate

- D16 reads SC-006 as not covering decision records and the roadmap. That is a reading of an
  approved requirement and is put to the maintainer when the pull request is offered.
- The specification assumes nothing under `.github/` needs to change. A contributor skill at
  `.github/skills/demo-views/SKILL.md` shows `<c-page>` and `<c-app>` in three places. This run
  may not edit `.github/`, so the three mentions are left and reported.

**ADR:** none — open questions for the maintainer, not decisions

## Build

### D24. Existing tests were edited for names only

**Found:** the move touched 47 existing test modules and two fixture templates, which the check
on changes to existing tests flags.

**Checked:** each file was compared with its version before the move with the prefix removed.
Every difference is a component name, a tag, a template path, or a long string split across
lines to keep it within 88 columns. No assertion was changed, removed or weakened and nothing
was skipped.

**Chosen:** accepted. Changing the names a test asks for is the change this feature makes
(SC-003).

**ADR:** none — a check made during the build

## Code review, 2026-10-05

One reviewer, one round. Verdict: changes requested, one high finding and two low.

### D25. Review findings and what was done

- **High: three settings examples still listed navbar widgets by their old names** (`README.md`,
  `docs/getting-started.md`, the assistant skill). Copied as written they break every page.
  Fixed: the five names take the prefix (T011).
- **Low: the decision record and the changelog overstated two things** that only become true
  when #435 lands: that a bare name always means daisy-cotton's component, and that nothing
  shares a name. Reworded to say what is true now (T012).
- **Low: two moved templates had their line endings changed** from CRLF to LF by the move.
  Restored, so every moved template is identical to its earlier version apart from names (T013).

The fixes were made directly, without a separate build session: each is a wording change or a
byte-level restore, with nothing to design.

**ADR:** none — review findings, local to this feature
