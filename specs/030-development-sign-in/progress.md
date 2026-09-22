# Progress — 030 Sign-in and sign-out pages in the package

## 2026-09-22 — PLAN

Branch `030-development-sign-in` cut from `origin/main` at `16e70a2`, the commit that merged the
specification (PR #382). Epic #381, stories #383, #384, #385.

Base verified green before any change: lint, types, 522-test suite and build all pass.

One repair to the base, unrelated to this feature. The conformance check was red on `main`:
`tests/test_full_page_fill_e2e.py` measures computed layout in a browser and has no Python module
to mirror, but was never declared under `[tool.forge.conformance] non-mirror-paths` the way its
siblings are. Declared, with the same reasoning as the entries beside it. Nothing else on the base
was touched.

Planned: `plan.md`, `research.md`, `tasks.md`. Sixteen tasks over a foundational phase and three
stories, run sequentially — all three stories touch the same four files.

## 2026-09-22 — S3R DESIGN_REVIEW

One reviewer, three lenses, one round. Verdict `request_changes`: three verified high findings,
one medium, two low. All six applied — three as plan edits (T005, T010, T011, T016), three as
decisions (D12, D13, D14). Editorial notes swept into `plan.md` and `tasks.md`.

## 2026-09-22 — S4 IMPLEMENT

**T001 done.** `django-allauth` 65.19.4 added to the test dependency group; `deptry` is clean
without a per-rule ignore, so none was added — the entry the task anticipated would have silenced
a finding that does not exist. Research R11 records the test configuration read out of the
installed package, including the one thing that would otherwise have been discovered failure by
failure: `override_settings` populates the app registry before it installs any other overridden
value, so allauth's middleware check fires against the un-overridden `MIDDLEWARE` unless the two
overrides are nested.

Implemented directly rather than dispatched: one task, a dependency addition and a written
finding, with no design content.
