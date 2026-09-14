# Decisions — 029 Layout state store and static responsive visibility

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without
escalation. Each entry records what was unclear, what was chosen, and why the choice is
defensible on evidence already in this repository.

## D1 — Responsive visibility stays in the stylesheet

**Ambiguous because** issue #345 proposes the opposite: that regions be shown and hidden by
client-side expressions keyed off layout state, rather than by classes injected from template
tags.

**Chosen**: the tags go, but their rules become stylesheet rules. No region's visibility depends
on the client-side runtime.

**Why this is defensible on this repository's own evidence.** The shipped bundle is loaded with
`defer`, so nothing it registers exists until after the document has parsed. Expression-driven
visibility therefore applies after first paint, and both the wide and narrow copies of a region
are on screen until it does. This package has already paid for exactly that, in a different
place: `mvp/templates/cotton/layout/sidebar/index.html` carries a blocking inline script whose
whole purpose is to set the drawer's state before first paint, because resolving it after paint
turned a correction into a visible width animation (#178). Its comment says so. Reintroducing the
same ordering problem in the header, on every load and again on every boosted navigation, to
retire a template tag would be trading a maintenance cost for a user-visible one.

Three further properties the current approach has and an expression-driven one would not:
visibility survives JavaScript being unavailable, it costs no work on resize, and it is what every
other responsive decision in the library is expressed with, so the header would stop being special.

**What this does not settle.** The complaint underneath #345 is real and is acted on: the classes
are assembled at render time, which the stylesheet build cannot see, and the package compensates
with safelist entries and a test guarding them. That is the actual cost, and moving the rules into
the preset removes it without moving them into script.

**ADR:** `docs/adr/0021-responsive-visibility-is-resolved-by-the-browser.md` — graduated. The rule outlives this feature: it settles where any future responsive decision in the shell is expressed, and the reasoning is not obvious from the code it produces.

## D2 — The third tag joins the two named in the issue

**Ambiguous because** neither issue names `sidebar_navbar_toggle_class`, and the standing rule is
that scope comes from the issue rather than from what looks adjacent.

**Chosen**: it is in scope, on Sam's explicit ruling.

**Why**: it is the same mechanism — a class assembled at render time from the configured
breakpoint, covered by entries in the same safelist block, carrying the same "keep in sync"
comment. Removing two of three would leave the safelist, the comments and the render-time
construction standing, so the cost the feature exists to remove would survive it.

**ADR:** none — a scope ruling for this feature, made by Sam. ADR 0021 carries the rule the three tags were removed under.

## D3 — Removal without a deprecation period

**Ambiguous because** the three tags are reachable from any project template through
`{% load mvp %}`, which makes them public by access even though nothing advertises them.

**Chosen**: removed outright in this release, recorded as a breaking change.

**Why**: Article XVI states the package is pre-1.0 and that component and import APIs may change
between minor versions with a changelog entry. A search of `docs/`, `README.md` and the shipped
skill finds no mention of any of the three, so a deprecation cycle would be announcing the
withdrawal of something never announced in the first place. Sam ruled on this directly.

**ADR:** none — an application of Article XVI, which already states the policy. Recorded in the changelog as a breaking change.

## D4 — The attributes the stylesheet selects on go on a component-rendered element

**Ambiguous because** the obvious host for a document-wide attribute is `<body>`, which
`mvp/templates/mvp/base.html` renders.

**Chosen**: an element rendered by a component, containing all four governed regions. The spec
states the constraint rather than naming the element, because which one satisfies it is a
planning decision.

**Why `<body>` is the wrong host**: overriding the base template is a documented and expected
extension, and a project that does so writes its own `<body>`. The rules would then find no
attribute to select on and the header's trailing regions would never hide — a silent, width-
dependent failure of exactly the kind this feature is trying to reduce. Every one of the four
regions is already a descendant of the element the shell's drawer component renders, and that
component already resolves the breakpoint. The collapse mode is threaded through to it as part of
this work — see D7.

The same argument applies to the configuration payload the store reads, which is emitted from the
drawer component for the same reason and was corrected there after the design review.

**ADR:** `docs/adr/0021-responsive-visibility-is-resolved-by-the-browser.md` — the attribute host is part of the rule that ADR states, and the reason it is a component rather than the base template is recorded there.

## D5 — The store mirrors the drawer's control rather than owning it

**Ambiguous because** "one store holding layout state" reads as though the store should be the
single source of truth, and a mirror is a weaker claim.

**Chosen**: the drawer's existing checkbox stays authoritative for whether the sidebar is open.
The store tracks it in both directions, and the stylesheet keeps reacting to the checkbox
directly through the drawer-state variants.

**Why**: the same first-paint argument as D1, applied to the sidebar. The checkbox's state is
established during parse by a blocking script; a store's state is established when the deferred
bundle runs. Making the store authoritative would move the sidebar's resting position behind the
bundle and reinstate #178. It would also break the `is-drawer-open` / `is-drawer-close` variants,
which the sidebar, the drawer side panel and the icon rail all depend on and which cost nothing.

SC-002 still holds, because what it forbids is the same *fact* being written down twice, not a
reactive mirror of a fact with one owner. The duplication the feature removes is real and
separate: the sidebar's persisted default is currently spelled out once in the blocking script and
again in the persisted expression beside it.

**ADR:** `docs/adr/0022-the-layout-store-mirrors-state-it-does-not-own.md` — graduated. It constrains every future addition to the store, and a reader of the store alone would not see why it reads rather than owns.

## D6 — The store carries the layout settings only

**Ambiguous because** #346 says "app configuration", which could mean the whole merged
configuration dictionary.

**Chosen**: the `layout` subtree.

**Why**: the theme already reaches the client by its own mechanism, through the document attribute
the pre-paint script sets and the controls the bundle binds. The remaining top-level keys —
view names and table defaults — are read on the server to decide what to render, and nothing on
the page reacts to them. Publishing them would add public surface the package must then keep
stable, in exchange for no capability. If a later feature needs one, adding a key to a store that
already exists is cheap.

**ADR:** `docs/adr/0022-the-layout-store-mirrors-state-it-does-not-own.md` — what the store carries is a boundary on public surface, and that ADR states it.

## D7 — What the design review changed, and what it did not

The design was reviewed before any of it was built. Ten findings came back, six of them at high
severity, none critical and none about security. Every one was checked against the code before it
was acted on. All six were real, and all six cost an edit to the plan rather than a rework of a
branch, which is what reviewing a design before it exists is for.

**Corrections to a false premise.** The plan and `research.md` both stated that the drawer element
already receives the collapse mode. It does not: `mvp/templates/mvp/base.html` resolves it and
sends it to the sidebar and the header, and `mvp/templates/cotton/app/index.html` declares no such
variable. The stylesheet rule for the sidebar's duplicated controls needs the breakpoint and the
collapse mode on one element, so threading the value through is now part of the work.

**A behaviour the substitution would have changed.** Under the `never` setting, two of the three
replaced rules want their unconditional state and get it by no media query matching. The third does
not — the narrow-only region is *hidden* under `never`, so a project reads one set of header
actions instead of two stacked copies. Falling back to shown would have put the mobile copy on
screen at every width, in the one setting nobody exercises by accident. The preset now carries that
rule explicitly and the characterisation matrix covers the setting for all four regions.

**The proof method was not sound.** The characterisation tests were to be written against the
current package and stand unchanged afterwards, and this repository's habit is to assert class
strings in rendered HTML. The class strings are the mechanism being substituted, so such an
assertion either pins the old mechanism and has to be rewritten — at which point it is no longer a
regression test — or pins the new one and never said anything about the old. The tests now assert
computed visibility in a real browser, which is indifferent to how visibility is achieved. That is
a deliberate exception under Article XIV and the reason is recorded in the test module itself.

**Two sequencing faults.** The boosted-navigation task needed the viewport flag, which needed the
pixel width, which arrived only with a payload planned for a later story. And the three stories
shared a single committed bundle artifact, a store module, two test modules, a template and two
documentation pages — enough that parallel worktrees would collide by construction. The payload
moved into the foundational phase, where the plan's own through-line already put it, and the
stories are dispatched one at a time.

**A requirement the plan did not actually satisfy.** FR-006 asks that the persisted open state be
defined in exactly one place. Moving the persisted expression onto the store would have carried the
duplication with it, because the default and the storage key are written once in the blocking
pre-paint script and again beside it. The blocking script is now the single definition: it resolves
the value before first paint and renders the key and the value into the markup, and the store reads
both from there.

**Two medium findings applied rather than carried.** The store must register after the persist
plugin is installed, not merely before Alpine starts, because the plugin is what defines the
persisted-property helper. And the configuration payload was planned for `mvp/base.html`, the
template D4 had just rejected as an attribute host for the same reason — a project overriding it
would get a store with no configuration. Both were one-line corrections that remove a real defect,
so neither was left as a watch item.

**What the review confirmed.** Both Alpine claims in `research.md` were checked independently
against the bundled library and hold, including the ordering the whole first-paint argument rests
on. The count of safelist entries being retired was three, not four.

**ADR:** none — the corrections refine how this feature is built and nothing downstream inherits
them. D1, D4 and D5 already carry the architectural decisions, and their verdicts are recorded in
their own sections at convergence.

## D8 — Two corrections at the foundational phase's acceptance

**The guardrail that flags changes to pre-existing tests fired on
`tests/test_components/test_layout_config.py`.** Triaged and cleared: the change is purely
additive. The diff removes no line, and every test that existed before the refactor still reads
exactly as it did. That is the point of those tests — they are the evidence that moving
normalisation into one class changed no behaviour, and a refactor that needed them edited would
have been the wrong refactor. The flag is file-level, not assertion-level, so an addition to a file
containing older tests raises it by construction.

**The new resolver was undocumented and used underscore-prefixed names.** Both were fixed at
acceptance rather than sent back, and both trace to the brief rather than to the work: the brief
did not list `docs/` among the files the story could write, so the documentation the protocol asks
for had nowhere to go, and it did not state the naming convention.

`docs/layout.md` now carries a section on reading the resolved layout in Python. `LayoutConfig`
sheds `_raw_breakpoint` and `_disabled`: this codebase does not mark names private with a leading
underscore, and dropping the second one also removed it, since `persistent` already expressed the
same fact and the two other properties now read it.

**ADR:** none — both are corrections to one story's handover, with nothing downstream inheriting
them.

## D9 — Five assertions rewritten when the state they pinned moved

**The situation.** Moving the sidebar's open state and the header's stuck state into the store
broke five tests that had nothing to do with either behaviour. Each asserted a literal fragment of
the expression that used to sit in the markup — `$persist`, `desktopOpen`, `{ open: false }`,
`$watch`, `stuck = window.scrollY > 0`, and a `localStorage` call with the storage key spelled out
inside it. The behaviours those fragments stood for are unchanged. The fragments are not.

**Chosen**: rewrite the five assertions to name what the markup now carries, keeping every test's
subject, docstring intent and name. None was deleted, weakened or skipped.

**Why this is not a test being bent to fit a regression.** The distinction that matters is whether
the behaviour survived, and whether something independent proves it did. Both hold here:

- The pre-paint script is still there, still runs before the drawer-side markup, and still resolves
  the remembered state before the first frame. It now reads the storage key from the checkbox
  instead of repeating it, which is what made the key single-definition in the first place — so the
  assertion that broke is the one the requirement asked us to break.
- `tests/test_components/test_sidebar_persisted_state.py` proves, in a browser, that no width
  transition plays on a restoring load, that the sidebar is already open on the first frame, and
  that the store agrees with the checkbox at that moment. That is issue #178's actual guarantee,
  tested at the level the defect lives at.
- `tests/test_components/test_layout_store.py` proves the remaining behaviours end to end: the
  store follows every control the shell ships, a boosted navigation leaves it correct at a wide
  viewport and closes it at a narrow one, the shell still works with JavaScript off, and a page
  with no shell gets a store reporting defaults rather than an exception.

Every one of those is a stronger statement than the string it replaces. A test that reads an
expression out of rendered HTML cannot tell whether the expression works.

**Why the builder did not do it.** An Implementer may not modify a test it did not author, and it
was right to stop and report rather than edit its way to green. Triaging that report is the
orchestrator's job, and this is the triage.

**Revisit if** a future change moves this state again. The rewritten assertions name markup the
store reads, so they will break again the same way — which is the point at which someone should ask
whether they earn their place at all, given the browser coverage now standing behind them.

**ADR:** none — a testing judgement scoped to this feature's own diff.

## D10 — The resolved configuration stays a nested `config` object

**The question.** T010 asked whether a project should read the resolved configuration
(`breakpoint`, `breakpoint_px`, `collapse`, `sticky`, `boost`, `persistent`) off `$store.layout`
as a nested `config` object — the shape it already has, carried over unchanged from T004 — or
whether it should be flattened onto the store or exposed through named accessors.

**Chosen: leave it nested, and keep it that way deliberately rather than by omission.**

**Why.** The store already draws a line the flattening options would blur. `sidebarOpen`,
`desktopOpen`, `isWide` and `headerStuck` are reactive: Alpine tracks them, they mutate over the
page's lifetime (a click, a resize, a scroll), and `isWide` in particular is *derived* state built
from `config.breakpoint_px` by the `matchMedia` listener rather than being config itself. `config`'s
six values are resolved once, server-side, at render time, and never change for the life of the
page. Flattening `config` onto the store would mix a page's fixed facts in with the properties
Alpine actually watches, and a reader skimming the store's own keys couldn't tell which was which
without opening the source. Nesting the resolved values under one name states the distinction the
store already relies on: `isWide` stands alone because it behaves like state, `config.breakpoint_px`
stays nested because it does not.

Named accessors were the other option and were rejected as an unneeded layer: `config` is already
`LayoutConfig.as_dict()` (`mvp/layout.py`), the same plain-data shape the server resolves and the
client parses — an accessor method would wrap a value already sitting on a plain object for no
reader benefit, and this codebase's simplicity standard asks for the plain read over the wrapper
when both cost the same.

**What this means for T011/T012.** Tests read `Alpine.store('layout').config.<key>`; the
documentation table below describes the same six keys under that same name. Nothing in `layout.js`
changed for this decision — T004 already built the shape T010 asks for, including the never-
persistent case (`breakpoint_px` is `null` off `LayoutConfig.breakpoint_px`, not a meaningless
width) and the `matchMedia`-driven `isWide` flag. T010's work was confirming that shape deliberately
and extending the demo/`layout/store/` page to accept `?breakpoint=` so a browser test can reach a
per-page override and the never case without a new template.

**Revisit if** the store grows a second nested settings group — at that point one exception reads
as an accident and the naming should be reconsidered as a set, not patched again in isolation.

**ADR:** none — a naming judgement scoped to this feature's own store shape, already partly settled
by D6.

## D11 — The browser tests wait for a condition, never for a duration

**The situation.** One test in `tests/test_components/test_layout_store.py` failed once and passed
on re-run, reported as a flake. It was not a flake. At mobile width an open drawer lays its overlay
across the header, so the navbar control the test clicked a second time is genuinely unreachable —
the click was racing the drawer's transition and winning most of the time. The module also carried
five fixed two-hundred-millisecond sleeps standing in for "the bundle has booted by now".

**Chosen**: the module waits for conditions.

- Closing the drawer goes through the overlay, which is the documented way out of an open mobile
  drawer and a plain label wired to the same checkbox. The test now exercises what a person can
  actually reach.
- The sleeps became one helper that blocks until the layout store is registered. The bundle is
  deferred and stores register during start, so a loaded page is not a booted one, and a fixed
  sleep is a flake waiting for a slower machine — of which continuous integration is one.
- The never-persistent case waits for the browser to confirm the resize landed before asserting the
  viewport flag stayed false. Asserting on a resize that has not happened yet proves nothing.

Run three times in a row after the change, twelve passed each time.

**Why this was not left for the reviewer.** An intermittent test that lands is worse than a missing
one: it trains everyone reading the pipeline to re-run rather than to look, and this repository
already has an open issue about browser tests failing under the parallel matrix. Hardening it costs
minutes now and is unbounded later.

**ADR:** none — test-hygiene inside this feature's own diff.

## D12 — A file outside the brief's list also asserted the removed class strings

**The situation.** T015's brief named `tests/test_views/test_account.py` and the tag-level tests in
`tests/test_components/test_layout_config.py` as needing restatement or deletion once
`navbar_wide_only_class`, `navbar_narrow_only_class` and `sidebar_navbar_toggle_class` were deleted.
A grep for the three names, run before deleting them, found two more casualties the brief's file list
did not mention: `TestNavbarToggle` in `test_layout_config.py` (issue #114's regression, asserting
`"lg:is-drawer-open:hidden"` etc. on the navbar toggle) and the whole of `TestTheBrandMarkAppearsOnce`
plus two tests in `TestTheActionsGiveWayToTheTrail` in `tests/test_components/test_app_header.py` —
a file the brief's scope list does not name at all.

**Chosen:** restate all of them on the same basis the brief already authorised for
`test_account.py`'s two lines: the *subject* (the region hides/shows correctly) is unchanged and
still real; the *mechanism* the assertion named (a class string) is what is being deleted, so the
assertion has to change or the test simply asserts something that no longer exists. `TestNavbarToggle`
was deleted rather than restated — see below — everything else was restated in place, keeping each
test's name and docstring intent.

**Why this is not scope creep.** `craft-increments` prohibits touching files the story does not
require; it does not protect a file from a change the deletion the brief explicitly ordered
necessarily causes. Leaving `test_app_header.py` red at the end of this task would violate "the tree
is green between slices," and the story's own governing rule (D7, plan.md "How the substitution is
proved") already establishes the principle: a test asserting the replaced mechanism by name is
expected to change. This is that principle applied to two files the brief's author did not think to
grep for, not a new principle.

**Why `TestNavbarToggle` was deleted rather than restated.** Its two tests exist to prove one thing:
a per-page breakpoint/collapse override reaches the navbar toggle, not only the drawer and the rail
(issue #114). After T015 the toggle's own class is static (`mvp-sidebar-echo`) regardless of any
override — restating the assertion to check for that class present would be true unconditionally
and would not distinguish an override from the default, so it would guard nothing. The same
regression is now provably covered two other ways: `TestDrawerRendersLayoutAttributes` (T014,
`tests/test_components/test_layout_config.py`) proves the override reaches the drawer element's own
`data-mvp-breakpoint`/`data-mvp-collapse` attributes, using the same fixture
(`tests/app_shell_override.html`) this test used; and
`tests/test_components/test_responsive_visibility.py::TestSidebarEchoRegion` proves, in a browser,
that computed visibility actually follows both attributes at every breakpoint and both collapse
modes. Keeping a third, now-vacuous test would be padding, not coverage.

**Revisit if** another pre-existing test surfaces later asserting one of these three class strings —
this diff's own grep covered `tests/` only; a project's own test suite (outside this repository)
built against the removed tags is the actual audience D3's breaking-change entry is for.

**ADR:** none — test-fallout triage scoped to this story's own required deletion.

## D13 — Every review finding was fixed, including the low ones

Ten findings came back from the code review: one high, four medium, five low. All ten were checked
against the code before being acted on, all ten held, and all ten were fixed. A finding left open
because of its severity still has to be read by whoever merges, and is cheaper to close now than to
carry.

**The high one was the feature repeating its own mistake.** D4 rejected the document body as the
host for the attributes the stylesheet selects on, because a project that writes its own
`base.html` would silently lose them. The Account Center's layout then ended up depending on
exactly that: it extends the unqualified `base.html`, which a project may own and which need not
render the shell at all, and it had given up the breakpoint resolution that used to make it
self-sufficient. Both copies of its navigation would have shown at once, at some widths, in a
configuration the getting-started page explicitly supports. The row now carries the attributes
itself. Inside the shell the nested host resolves the same value from the same context, so nothing
changes there.

**One finding was a genuine gap in CSS, not in the code's intent.** The five media blocks used
`max-width: N-1px` as the complement of `min-width: Npx`. Between those two values lies every
fractional viewport width that browser zoom and display scaling produce, and at those widths
neither query matched and the region kept its default. Tailwind emits `not all and (min-width: N)`
for its own `max-*` variants for this reason. Five token changes.

**Two were dead weight the substitution left behind.** The header component still declared and
forwarded a breakpoint and a collapse mode to a navbar that no longer reads either, and the shipped
skill documented both as live attributes — so a project setting one would have got silence. And the
store's default configuration described a state the server cannot produce: the `lg` breakpoint with
persistence off and no pixel width, where the documentation promises the package defaults.

**Two more were about the tests proving less than they claimed.** One characterisation test says
"unconditionally" but never closed the drawer, so a rule wrongly gated on the drawer being open
would have passed it. Another names the drawer state in its title and never opened the drawer. Both
now do what their names say.

The rest: two fixed sleeps that survived D11, a store read that ran before the store existed, a
storage key restated as a literal in the bundle, and one documentation caveat about these classes
setting `display: flex` and sitting outside Tailwind's utility layer.

**ADR:** none — corrections within this feature's own diff. The rule the high finding violated is
already recorded in `docs/adr/0021-responsive-visibility-is-resolved-by-the-browser.md`.
