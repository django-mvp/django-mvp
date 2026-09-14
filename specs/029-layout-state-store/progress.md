# Progress — 029 Layout state store and static responsive visibility

A dated, append-only record of what happened at each point in this feature's delivery.

## 2026-09-14 — Intake

Two open issues assessed together: #346 (publish layout state and configuration for the page to
read) and #345 (are the responsive visibility template tags necessary). They describe one piece of
work, so #346 became the feature and #345 is resolved by the same change.

Agreed with the maintainer before any artifact was written:

- Responsive visibility stays resolved by the browser. The tags go; their rules become stylesheet
  rules rather than client-side expressions.
- `sidebar_navbar_toggle_class` is in scope alongside the two tags #345 names.
- The tags are removed outright rather than deprecated for a release.

## 2026-09-14 — Specification

`spec.md` written: three user stories, FR-001 to FR-023, SC-001 to SC-006. Every requirement is
mapped to exactly one story. Five ambiguities resolved without escalation and recorded under
`## Clarifications`, with the longer reasoning in `decisions.md` as D1 to D6.

Issue graph built: #346 promoted to the feature's parent issue, with #347, #348 and #349 attached
as its stories. Draft pull request #351 opened from this branch, carrying a closing line for each
of the five issues.

Title lint: green.

## 2026-09-14 — Specification sign-off

Approved by the maintainer, unchanged. Planning starts. The maintainer also waived the
post-planning notification, so the next point he is involved is the merge decision.

## 2026-09-14T21:55:00Z · Implementer US0 · T001

Did: Added `mvp/layout.py` with `LayoutConfig` — one class carrying `breakpoint`, `persistent`,
`breakpoint_px`, `collapse`, `sticky`, `boost` and `as_dict()`. Normalisation (never/none in any
case, unrecognised name falls back to `lg`) lives only in this class's `breakpoint`/`persistent`/
`breakpoint_px` properties.

Verified: `poetry run pytest tests/test_layout.py -x` → 15 passed. `poetry run ruff check` and
`poetry run ruff format --check` on both new files → clean. `poetry run mypy mvp/layout.py` →
clean.

Next: T002 — the surviving tags read the resolver.

Watch: none.

## 2026-09-14T22:05:00Z · Implementer US0 · T002

Did: `sidebar_breakpoint_class`, `breakpoint_px` and `sidebar_has_breakpoint` in
`mvp/templatetags/mvp.py` now construct a `LayoutConfig` and read its `breakpoint`/`persistent`
properties instead of calling `_breakpoint_disabled` and repeating the `SIDEBAR_BREAKPOINTS`
lg-fallback lookup inline. Added `resolve_layout_config`, the tag T003 uses to resolve a
`LayoutConfig` for a template. Left `_breakpoint_disabled`, `SIDEBAR_BREAKPOINTS` and the three
visibility tags (`sidebar_navbar_toggle_class`, `navbar_wide_only_class`,
`navbar_narrow_only_class`) untouched — they are a later story's to remove and still use the
helper.

Verified: `poetry run pytest tests/test_components/test_layout_config.py -q` → 53 passed,
including every pre-existing test in the file, unmodified. `poetry run ruff check` and
`poetry run mypy` on `mvp/templatetags/mvp.py` → clean.

Next: T003 — the configuration payload.

Watch: `tests/test_components/test_layout_config.py` already failed `ruff format --check` before
this story touched it (two pre-existing lines, unrelated to T002) — confirmed by checking the
file at the pre-story commit. Left as-is per scope containment; noted in the completion report's
`concerns`.

## 2026-09-14T22:15:00Z · Implementer US0 · T003

Did: `mvp/templates/cotton/layout/sidebar/index.html` (the drawer, `<c-layout.sidebar>`) gained
three new component attributes — `collapse`, `sticky`, `boost` — each defaulting to its
`MVP_CONFIG["layout"]` value, and resolves a `LayoutConfig` via `resolve_layout_config`. Emits
`layout.as_dict()` through Django's `json_script` filter at id `"{{ id }}-layout-config"`, placed
next to the drawer checkbox rather than in `mvp/base.html` (D4/D6: a project overriding the base
template keeps `<c-app>` and therefore keeps the payload).

Verified: `poetry run pytest tests/test_components/test_layout_config.py -q` → 57 passed
(53 pre-existing + 4 new), pre-existing tests unmodified. `poetry run ruff check` on the test file
→ clean. `poetry run mypy mvp` → clean, 31 source files.

Next: none — US0 is Phase 0's last task. Handing off for the story's full verify.

Watch: `docs/components.md` and `skills/django-mvp/references/components.md` document
`<c-layout.sidebar>`'s attributes as `id`, `breakpoint`, `class` — now stale, since this task added
`collapse`, `sticky` and `boost`. Neither file is in this story's scope
(`files_you_may_create_or_edit`); flagged in the completion report's `concerns` for whichever story
or pass owns docs next.

## 2026-09-14 — Design review

Reviewed before implementation, across three lenses. Ten findings: six high, three medium, one
low. No critical, none about security. Every finding was checked against the code before being
acted on, and all six high findings were real.

Two of them changed the shape of the work. The collapse mode does not reach the element the
stylesheet rules need it on, so threading it through is now part of the task list. And the
characterisation tests could not have proved what they claimed — the class strings they would have
asserted on are the mechanism under substitution — so they assert computed visibility in a browser
instead.

The rest: the configuration payload moved into the foundational phase, the stories were declared
sequential, the persisted sidebar default got a single definition, and three task file lists were
corrected. Reasoning in `decisions.md` D7.

## 2026-09-14 — Foundational phase complete

T001, T002 and T003 done. `LayoutConfig` resolves the shell's layout facts once, the three
surviving template tags read it instead of reimplementing normalisation, and the drawer component
emits the resolved values to the client as escaped JSON.

Independently verified on the resulting commit: conformance, documentation, lint, type check, the
full test suite and the package build all green. The pre-existing-test guardrail flagged one file
and was cleared as additive. Two corrections were applied at acceptance — see `decisions.md` D8.

## 2026-09-14 · Implementer US-1 · T004

Did: added `assets/js/layout.js`, registering `Alpine.store("layout", ...)` from
`assets/js/index.js` after `Alpine.plugin(persist)` and before `Alpine.start()`. `init()` parses
the T003 config payload (falling back to package defaults when no shell renders one), reads the
drawer checkbox's checked state for `sidebarOpen`, and derives `isWide` from a `matchMedia` query
on the resolved pixel width with a `change` listener — permanently `false` when the sidebar is
never persistent. `desktopOpen` is a placeholder `Alpine.$persist(true).as("mvp-app-drawer-open")`
for this task; T005 replaces it with a key/value read from the drawer's markup so the default and
key have exactly one definition (FR-006).

Verified: `poetry run invoke build-js` (esbuild, byte-reproducible) rebuilt
`mvp/static/js/django-mvp.js`, 128.3kb. `poetry run pytest tests/test_components/test_layout_config.py`
— 57 passed — confirms the payload T004 parses is unchanged.

Next: T005 — bind the drawer checkbox to the store and move the persisted default/key onto the
blocking pre-paint script as their single definition.

Watch: `desktopOpen`'s key/default are still written twice (blocking script and store) until T005
lands; not yet a violation of any task's acceptance since T004 doesn't claim FR-006.

## 2026-09-14 · Implementer US-1 · T005

Did: wrote two new tests in `tests/test_components/test_sidebar_persisted_state.py` first
(extending the #178 regression suite, not replacing its existing tests) and watched
`test_the_key_and_default_are_not_declared_twice` fail for the right reason — the storage key
rendered twice — against T004's code. Then made the checkbox bind directly to
`$store.layout.sidebarOpen` (dropping its local `open`/`desktopOpen`/`$watch` x-data), and made
the blocking pre-paint script the single definition of the persisted default and the storage key:
it renders the key onto the checkbox as `data-mvp-persist-key`, and after resolving the value from
`localStorage` it writes that resolved value onto `data-mvp-persist-open`. `assets/js/layout.js`
reads both attributes to construct `Alpine.$persist(initial).as(key)` at store-construction time,
rather than hardcoding either. The store mirrors `sidebarOpen` back into the persisted
`desktopOpen` via `Alpine.watch` (not `Alpine.effect` — it must not fire on registration, only on a
later change, the same guarantee the old `$watch` gave).

Verified: `poetry run invoke build-js` rebuilt the bundle. `poetry run pytest
tests/test_components/test_sidebar_persisted_state.py` — 4 passed, including both new tests.

Next: T006 — move the header's stuck state onto the store.

Concern (see also T006/T008 below): four pre-existing tests in `tests/test_components/test_layout_config.py`
(from the foundational T001-T003 phase, not authored in this story) now fail —
`test_drawer_state_persisted_with_breakpoint_default`, `test_persisted_state_applied_before_alpine_hydrates`,
`test_overlay_state_is_transient_desktop_state_persists`, `test_breakpoint_never_component_override`.
Each asserts literal Alpine expression text this story's design deliberately removes from the
markup (`$persist(...)`, `$watch`, `desktopOpen`, `{ open: false }`, a hardcoded `localStorage.getItem('mvp-app-drawer-open')`
call) — exactly the mechanism T005 moves into `assets/js/layout.js` so the default and key have one
definition (FR-006). This is the same "proof method was not sound" situation D7 already resolved
for `test_responsive_safelist.py`: an assertion pinning the mechanism under substitution cannot
survive the substitution. Per the Implementer protocol these are not mine to edit (not authored in
this story); left untouched and reported in the completion report's `concerns` for Forge/review to
reconcile — most likely by rewriting them to assert the store's behaviour, the way
`test_sidebar_persisted_state.py` now does.

## 2026-09-14 · Implementer US-1 · T006

Did: the header's scroll handler now writes `$store.layout.headerStuck` instead of a local
`stuck` in its own `x-data`; the `:class="{ 'shadow-xs': ... }"` binding reads the same store
property. Shadow behaviour (appears on scroll, gone at the top) is unchanged.

Verified: `poetry run pytest tests/test_components/test_app_header.py` — 18 passed (breadcrumb/
header layout coverage untouched by this change).

Next: T007 — re-derive sidebar state after a boosted navigation.

Concern: one further pre-existing test in `tests/test_components/test_layout_config.py`,
`TestHeaderStickiness.test_default_header_is_sticky`, asserts the literal string
`"stuck = window.scrollY > 0"`, which no longer appears verbatim (`$store.layout.headerStuck`
replaces the bare `stuck` local). Same class of conflict as T005's; left untouched, folded into the
same concern for Forge/review.

## 2026-09-14 · Implementer US-1 · T007

Did: `assets/js/layout.js`'s store gained `rebindAfterNavigation()` (open only when the viewport is
wide and the remembered desktop state says so); `assets/js/index.js`'s existing
`htmx:afterSettle` handler calls it when the swap target was `document.body`, alongside the
pre-existing theme/dropdown rebinding.

This task also fixed a real, observed regression from moving sidebar state into a global store:
before this task, `tests/test_components/test_sidebar_boost.py::TestBoostedNavigationClosesTheDrawer::test_the_overlay_drawer_closes_after_a_boosted_click`
failed — the global store's `sidebarOpen` survived a boosted swap where the old per-element local
`open` did not, leaving a mobile overlay open across navigation. This task's re-derivation is what
that test exists to prove closes again.

Verified: `poetry run invoke build-js` rebuilt the bundle. `poetry run pytest
tests/test_components/test_sidebar_boost.py` — 8 passed (previously 7 passed / 1 failed before this
task).

Next: T008 — the store's behaviour, in a browser (new test file).

Watch: T005's own commit (`abbddc7`) landed after T006 and T007 rather than before them — its
`assets/js/layout.js` share was made alongside the template/test changes but got swept into T007's
commit (`d3a3f6b`) instead of committed on its own, since nothing was staged between the T005 edits
and the T006 edits that followed. Functionally nothing is missing or duplicated (verified by
diffing each commit's `assets/js/layout.js` hunk against what T005/T007's acceptance each ask for),
but the commit boundary for T005 doesn't include all of T005's diff. Caught during T008 while
reviewing `git log` before writing new tests; recorded rather than rewritten, per the "never rebase
to hide a mistake" instinct — the history says what happened.

## 2026-09-14 · Implementer US-1 · T008

Did: `tests/test_components/test_layout_store.py` (new), covering what only a browser can show: the
store exists and reports sidebar/collapse/stuck state; the checkbox (bound to the store since T005)
follows every control the shell ships — navbar toggle, sidebar header toggle, drawer overlay; a
boosted navigation leaves the store correct at both a wide and a narrow viewport; the shell still
opens and closes with JavaScript disabled; a shell-less page (`/errors/404/`) still gets a store
reporting defaults without throwing.

Two things surfaced while writing this suite, both fixed in the test rather than the product:
- The drawer overlay's own visual stacking under the open sidebar's content (a DaisyUI/stylesheet
  concern outside this story's scope) made a coordinate-based click land on the wrong element;
  switched that one assertion to a native `el.click()`, which still proves the label's `for`
  wiring reaches the store.
- Without JavaScript the blocking pre-paint script never runs either, so the sidebar starts closed
  (not open, as the desktop default assumes) — the no-JS test opens it first via the navbar toggle
  before closing it again, rather than assuming a start state that only JS produces.

Probed rather than trusted: temporarily commented out `registerLayoutStore(Alpine)` in
`assets/js/index.js`, rebuilt, and confirmed 8 of the 9 new tests fail (the ninth needs the boosted
config fixture regardless of the store) — then restored it and rebuilt again. `git diff` against
the T007 commit confirms the restore is byte-identical.

Verified: `poetry run pytest tests/test_components/test_layout_store.py` — 9 passed.

## 2026-09-14 — US-1 complete

The layout store exists and the shell's own sidebar and header read it. T004 to T009 done.

Five older tests broke: each asserted a literal fragment of an expression this story removed from
the markup. Triaged and repointed at what the markup carries now, with the behaviours they stood
for covered end to end in a browser instead — see `decisions.md` D9. None was deleted, weakened or
skipped, and the guardrail's second flag was the additive extension of the #178 regression tests
its own task called for.

Independently verified after the work landed: conformance, documentation, lint, type check, the
full suite and the build all green, the store and persisted-state browser tests pass, and the
committed JavaScript bundle rebuilds byte-identically from source.
