# Progress — FS-026 Themes that ship with the package

Append-only stage and gate log. Gate outcomes are written here at the moment they are decided.

| When | Stage | Event |
|---|---|---|
| 2026-08-13 | S0 INTAKE | Grilled from a free-text request. Three options put to the maintainer after establishing the mechanics from the pinned daisyUI package; option A chosen (ship the themes in the package), with a mandate that custom-theme authoring be documented in full. Feature statement confirmed. |
| 2026-08-13 | S0 EXIT | Issue #230 filed from the agreed statement, labelled `feature-request` + `accepted`. Roadmap R18, serves G8, G6, G14. No milestone: R18 sits under the v1.x range, and a range is not a milestone. |
| 2026-08-13 | S1 SPECIFY | Branch `026-ship-prebuilt-daisyui` created. `spec.md` authored: 3 user stories (P1/P2/P3), 20 functional requirements, 8 success criteria. |
| 2026-08-13 | S1 CLARIFY | Taxonomy scan run; 6 ambiguities identified and self-resolved from grilling context and from the pinned package. Recorded in `spec.md` under `## Clarifications`, with evidence in `decisions.md` (D1–D7). Nothing escalated. |
| 2026-08-13 | S1 GATE | Spec lint green: no unresolved markers, goal ids cited, every story has an independent test and acceptance scenarios, every requirement maps to a story, ids sequential. |
| 2026-08-13 | S2 SETUP | Branch pushed. Issue #230 promoted to epic in place; story sub-issues #231, #232, #233 created with no lifecycle labels; draft PR #234 opened by the bot with a `Closes` line per issue. No milestone: R18 sits under the v1.x range. Title lint and S2 stage-exit both green. |
| 2026-08-13 | SPEC GATE | Brief posted to #230. Maintainer overruled the start-up validation of theme names: the package cannot evaluate the check, because a project's own theme lives in a file the package never reads. Specification amended — the requirement is now that an unmatched name falls through to the default theme and is documented rather than validated. Decision record D5 rewritten, requirements renumbered to FR-021, SC-008 restated, story issues #231 and #233 re-synced. Spec lint re-run green. Re-gated. |
| 2026-08-13 | SPEC GATE | **Approved** by the maintainer, on the amended specification. Scope frozen at 3 stories, 21 functional requirements, 8 success criteria. |
| 2026-08-13 | S3 PLAN | `plan.md` (constitution check across 17 articles, all pass or N/A), `tasks.md` (15 tasks, 5 phases, test-first throughout), `feature-state.json` created and schema-valid. Two rejected alternatives recorded: per-theme static files, and a theme registry for validation. **Spec defect caught and corrected during planning:** FR-002 forbade fetching "a theme definition or stylesheet" from a third party, which the pre-existing icon-font link already violated and which the approved scope excludes. Narrowed to theme definitions, restoring the requirement to what the gate approved rather than widening the feature. SC-002 narrowed to match. |
| 2026-08-13 | S3R DESIGN REVIEW | `request_changes`, risk medium, three findings, all verified against the repository before being accepted. Two orphaned exact-string assertions on `@plugin "daisyui";` given owning tasks, and T012's file list repointed away from a test module that does not exist and that Article X forbids creating. T001's theme-completeness guard given the skip-and-non-empty treatment T010 already carried, so it cannot report green on an empty glob in a CI job that never installs node_modules. SC-004 had no task: T016 added, one browser test for the `data-set-theme` path, and the Article XIV row in `plan.md` corrected rather than argued around. 16 tasks, 5 phases. Recorded as D8. |

## Implementer US1 task log

## 2026-08-13T00:00Z · Implementer US1 · T001

Did: Replaced `TestShippedStylesheetShipsCompleteDaisyUI.test_named_themes_are_not_shipped` (the
#190 named-theme exclusion guard) with a new class `TestShippedStylesheetShipsEveryPrebuiltTheme` in
`tests/test_smoke.py`, asserting the inverse plus the two FR-006 invariants: theme names discovered
from `node_modules/daisyui/theme/*.css` (skips explicitly and asserts non-empty before
parametrising), the `:where(:root)` default binding, and the `@media (prefers-color-scheme: dark)`
block. Recorded the reversal as D9 in decisions.md, citing #190 and this spec, without deleting the
original #190 reasoning.
Verified: `poetry run pytest -q tests/test_smoke.py::TestShippedStylesheetShipsEveryPrebuiltTheme` →
33 failed (one per theme not yet shipped), 5 passed (discovery + both invariants), 0 errors — red for
the expected reason: the stylesheet has not been rebuilt yet.
Next: T002 rebuilds the stylesheet with `themes: all` to turn this green.
Watch: none.

## 2026-08-13T00:05Z · Implementer US1 · T002

Did: Changed `assets/tailwind.css`'s bare `@plugin "daisyui";` to the block form with
`themes: all;`, updated the stale adjoining comment that claimed themes "default to light/dark
only", relaxed `tests/test_smoke.py`'s exact-string assertion from `'@plugin "daisyui";'` to
`'@plugin "daisyui"'` (still guards the plugin line's presence, now tolerant of the block form),
and rebuilt+committed `mvp/static/css/django-mvp.css` and its `.br` sibling with
`poetry run invoke build-stylesheet`. That command also regenerated `demo/static/css/demo.css` as
a side effect (single-line non-deterministic reordering, no content change — `assets/demo.css`
still uses the bare, unmodified `@plugin "daisyui";`); reverted it with `git checkout --` since it
is outside T002's file list.
Verified: `poetry run pytest -q tests/test_smoke.py` → 65 passed, 0 failed — T001's completeness
class is now fully green (34 discovery/invariant + parametrised theme cases), and the relaxed
entry-css assertion passes.
Measured (Article XV discipline — one session, one tool, brotli quality 11 via the repo's own
`build_stylesheet` task): pre-change committed `django-mvp.css.br` = 41,670 B (verified via
`git show HEAD~1:mvp/static/css/django-mvp.css.br`, matching decisions.md D3's recorded baseline);
post-change = 46,532 B. Growth = 4,862 B (4.75 KiB), under the 8 KB bound (SC-003).
Next: T003 adds the `theme` block to `MVP_CONFIG`.
Watch: none.

## 2026-08-13T00:10Z · Implementer US1 · T003

Did: Added `tests/test_config.py` (new file, mirrors `mvp/config.py` per Article X) covering
`theme.default == "light"` / `theme.choices == []` with no override, and — exercised directly
against `mergedeep.merge` since `MVP_CONFIG` is a process-wide singleton and `tests/settings.py`
carries no `theme` override — that overriding one theme key leaves the other and sibling
top-level blocks (`brand`, `layout`) untouched. Then added the `theme` block to `mvp/config.py` as
a top-level sibling of `brand`, with the plan's comments including the fall-through/no-validation
note pointing at decisions.md D5.
Verified: `poetry run pytest -q tests/test_config.py` → before the production change, 5 failed
(`KeyError: 'theme'`) — red for the right reason; after, 5 passed. Also ran
`poetry run pytest -q tests/test_components/test_layout_config.py` (adjacent config consumer) →
40 passed, no regression from the `mvp/config.py` edit.
Next: T004 makes the pre-paint guard read `theme.default`.
Watch: none.

## 2026-08-13T00:15Z · Implementer US1 · T004

Did: Added `tests/test_components/test_theme_controller.py` (new file) covering the pre-paint
guard's position (first thing in `<head>`, before any stylesheet link — FR-005), its
stored-value-or-default expression against `theme.default` (SC-006, FR-003), and that a configured
value containing a quote and a closing `</script>` tag cannot break out of the script (Article V).
Then changed `mvp/templates/mvp/base.html`'s guard from the hardcoded
`localStorage.getItem('theme') || 'light'` to reading `mvp_config.theme.default` through
`{{ ... |escapejs }}` embedded as a double-quoted JS string literal, rather than raw interpolation.
Verified: `poetry run pytest -q tests/test_components/test_theme_controller.py` → before the
production change, 2 failed (default-expression tests, red for the right reason — script still
hardcoded `'light'`), 2 passed (position + escaping, trivially, since the config value wasn't read
yet); after, 4 passed. Also ran
`poetry run pytest -q tests/test_components/test_layout_config.py tests/test_smoke.py` (adjacent
`base.html` consumers) → 105 passed, no regression.
Next: T005 — a name matching nothing falls through, no production code.
Watch: T007 (not mine, Phase 3/US-2) adds the `theme.choices` membership arm to this same guard —
this task deliberately implements only the default-fallback arm FR-003/FR-005/FR-006 need.

## 2026-08-13T00:20Z · Implementer US1 · T005

Did: Added `TestUnmatchedThemeNameFallsThrough` to
`tests/test_components/test_theme_controller.py` (no production code, per the task): a configured
theme name matching no shipped or project block (1) renders without raising, (2) is emitted
unvalidated by the guard — same as a matching name — because the package cannot see a project's
own theme file (decisions.md D5), and (3) the shipped stylesheet's `:where(:root)` fall-through
binding, which is what makes that safe, is still present. This is the regression guard on the
deliberate non-validation decision.
Verified: `poetry run pytest -q tests/test_components/test_theme_controller.py` → 7 passed (all
green immediately, as expected for a no-production-code coverage task — the behaviour it guards
was already delivered by T002/T004). One self-correction during authoring: the first attempt used
a hyphenated fixture name (`totally-not-a-real-theme`); `escapejs` escapes every `-` to the
six-character sequence backslash-u-0-0-2-D (it guards against `--&gt;` breaking an HTML comment),
so the literal-substring assertion failed for a reason unrelated to the guard's correctness. Switched to a hyphen-free fixture name
(`totallynotarealtheme`, matching the un-hyphenated shape of every real daisyUI theme name) and
reran green — not a same-file/same-error repeat, so craft-debugging was not invoked.
Next: T003-T005 (US1) complete. Full-suite verify runs once, at the completion report.
Watch: none.

## Implementer US2 task log

## 2026-08-13T00:30Z · Implementer US2 · T006

Did: Added `TestThemeControllerUnconfiguredShape` to
`tests/test_components/test_theme_controller.py` first, against the *unmodified*
`theme_controller.html`, and ran it to confirm it passed before any production change — the
regression guard the task requires. Then added `TestThemeControllerOfferedSetShape` (4 tests:
exact configured set in order, unconfigured checkbox dropped, each entry has an accessible name,
control's label goes through `gettext`) and confirmed it RED against the unmodified template.
Changed `mvp/templates/cotton/actions/theme_controller.html`: with `mvp_config.theme.choices`
populated, renders `<c-dropdown>` (the same component `actions/language-switcher.html` already
uses) with one `<li><a data-set-theme="{{ choice }}">{{ choice }}</a></li>` per configured theme,
in order; with `choices` empty, renders the pre-existing checkbox `<label>` unchanged. No new
attribute added to `theme-controller` itself (Article XI) — the branch reads `MVP_CONFIG` directly,
matching how `navbar.html`/`sidebar/footer.html` already read it.
Verified: `poetry run pytest -q tests/test_components/test_theme_controller.py::TestThemeControllerUnconfiguredShape`
→ 1 passed (before the template change, confirming the regression guard against the current
markup). `poetry run pytest -q tests/test_components/test_theme_controller.py::TestThemeControllerOfferedSetShape`
→ 4 failed (before the template change, RED for the right reason: no `data-set-theme` in the
rendered page). After the template change: `poetry run pytest -q tests/test_components/test_theme_controller.py`
→ 12 passed. Also ran `poetry run pytest -q tests/test_components/test_layout_config.py
tests/test_smoke.py` (adjacent consumers of the same widget slots) → 110 passed, no regression.
`poetry run pre-commit run --files mvp/templates/cotton/actions/theme_controller.html
tests/test_components/test_theme_controller.py` → all hooks passed/skipped, no findings.
Next: T007 — the pre-paint guard's membership check.
Watch: T007 depends on T006 only for the offered set already existing in `MVP_CONFIG` (it does,
since US1) — no coupling to this task's template change.

## 2026-08-13T00:35Z · Implementer US2 · T007

Did: Added `TestPrePaintThemeGuardMembership` to `tests/test_components/test_theme_controller.py`
(3 tests: offered set reaches the guard, guard checks stored-value membership before honouring it,
empty offered set keeps the array present so the length-check short-circuit still applies) and
confirmed RED against the unmodified `mvp/base.html` guard. Changed the guard: emits
`mvp_config.theme.choices` as an inline array of individually `escapejs`-escaped string literals
(`offeredThemes`), reads the stored value once, and only honours it when
`offeredThemes.length === 0 || offeredThemes.indexOf(stored) !== -1` — with `choices` empty this
reduces to the v0.18.0 `stored || default` expression exactly, so `TestPrePaintThemeGuardDefault`
(US1, not touched) stays green unmodified. Recorded decisions.md D12: why the offered set is an
inline escaped array rather than `json_script`, and why T007's tests stay at the source-inspection
seam T004 already established in this file rather than shelling out to a JS runtime.
Verified: `poetry run pytest -q tests/test_components/test_theme_controller.py::TestPrePaintThemeGuardMembership`
→ 3 failed (before the base.html change, RED for the right reason — no `offeredThemes`/membership
check in the emitted script). After the change: `poetry run pytest -q
tests/test_components/test_theme_controller.py` → 15 passed. Also ran `poetry run pytest -q
tests/test_components/test_layout_config.py tests/test_smoke.py` → 110 passed, no regression.
`poetry run pre-commit run --files mvp/templates/mvp/base.html
tests/test_components/test_theme_controller.py` → all hooks passed/skipped, no findings.
Next: US2 (T006, T007) complete. Full-suite verify runs once, at the completion report. T016 is
out of this dispatch (depends on T013, US3, not built).
Watch: T016, when dispatched, needs a `[data-set-theme]` entry to click against — this task's
dropdown markup provides it once `theme.choices` is configured in whatever fixture/settings T016
uses.
