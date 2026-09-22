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
