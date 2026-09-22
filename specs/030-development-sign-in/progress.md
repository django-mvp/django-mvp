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

## 2026-09-22T13:03:41Z · Implementer US-1 · T002

Did: `SignInView(LoginView)` in `mvp/views/account.py`, registered as `account_login` in
`mvp/urls.py`. New template `mvp/templates/mvp/account/login.html`, derived from
`demo/templates/registration/login.html`, with the identifying field's `label` read from
`form.username.label` rather than the hard-coded `"Username"` (FR-005) and its form action
pointed at `account_login`.

Verified: `poetry run pytest tests/test_urls.py -v` — 2 passed. `poetry run ruff check` and
`poetry run ruff format --check` on the touched files — clean. `poetry run mypy mvp/views/account.py
mvp/urls.py` — no issues.

Next: T003 (failed sign-in re-renders without disclosing why).

Watch: `mvp.urls` now registers `account_login` unconditionally (the `app_is_installed` guard is
US-2/T011's addition per plan.md, not this task's). No fixture outside this story's scope reverses
that name yet, so no effect observed at this task.
