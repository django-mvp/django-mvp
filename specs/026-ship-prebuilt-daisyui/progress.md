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
