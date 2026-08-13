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
