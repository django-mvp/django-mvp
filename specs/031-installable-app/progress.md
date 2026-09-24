# Progress — 031 Installable app

## 2026-09-24 — PLAN

Branch `031-installable-app` cut from `origin/main` at `507c5a0`, the commit that merged the
specification (PR #391). Epic #186, stories #392, #393, #394.

Base verified green before any change: conformance, lint, types, suite and build all pass.

Planned: `plan.md`, `research.md`, `tasks.md`. Twelve tasks over three stories, run
sequentially in one worktree because all three share the resolver, the head template and the
docs page.

## 2026-09-24 — S3R DESIGN_REVIEW

One reviewer, three lenses, verdict approve. No critical or high findings. Four medium and two
low findings were applied to the plan: a missing root include no longer breaks pages, theme
colours come from the committed stylesheet instead of a generated file, the head reaches the
resolver through a template tag, and the colour test uses independent reference values. Recorded
as D1–D4.

## 2026-09-24T07:43Z · Implementer US1 · T001

- **Did:** Pinned the shell head with the feature off: tests/fixtures/base_head_off.html and TestShellHeadWithInstallableAppOff.
- **Verified:** poetry run pytest tests/test_templates.py — 181 passed, exit 0.
- **Next:** T002.
- **Watch:** The fixture has no trailing newline; regenerate it as the test docstring says.

## 2026-09-24T07:43Z · Implementer US1 · T002

- **Did:** Added the pwa config block and mvp.pwa.resolve().
- **Verified:** poetry run pytest tests/test_pwa/test_init.py tests/test_config.py — 26 passed, exit 0.
- **Next:** T003: theme colours.
- **Watch:** resolve() returns colours only from config until T003; the service_worker key is defined but not read until US-3.

## 2026-09-24T07:44Z · Implementer US1 · T003

- **Did:** Added ThemeColors (mvp/pwa/colors.py) and wired the default theme's colour into resolve().
- **Verified:** poetry run pytest tests/test_pwa tests/test_config.py — 33 passed, exit 0; 35 themes resolve; light/dark/cupcake match the reference values.
- **Next:** T004: views and URLconf.
- **Watch:** Colours read the base-100 value from the committed stylesheet; a rebuilt stylesheet changes them, by design (D2).

## 2026-09-24T07:44Z · Implementer US1 · T004

- **Did:** Added mvp/pwa/views.py, urls.py, the packaged worker template and tests through a root-mounted test URLconf.
- **Verified:** poetry run pytest tests/test_pwa — 34 passed, exit 0.
- **Next:** T005: head template.
- **Watch:** The worker template has no fetch listener; the test asserts the word 'fetch' is absent from the body.

## 2026-09-24T07:46Z · Implementer US1 · T005

- **Did:** Added the mvp_pwa tag, mvp/pwa/head.html and the include on the dark favicon line of base.html; tests in tests/test_templates.py and tests/test_templatetags.py, plus two shell URLconfs (tests/urls_shell_pwa.py, urls_shell_no_pwa.py) because the shell page needs the demo's URL names.
- **Verified:** poetry run pytest tests/test_templates.py tests/test_templatetags.py — 241 passed, exit 0; the off-state golden test passes.
- **Next:** T006: system checks.
- **Watch:** djlint (not a pre-commit hook) would move the include onto its own line; the brief's placement is kept.

## 2026-09-24T07:47Z · Implementer US1 · T006

- **Did:** Added mvp.W001 and mvp.W002 (mvp/pwa/checks.py), registered from MvpConfig.ready().
- **Verified:** poetry run pytest tests/test_pwa/test_checks.py — 8 passed, exit 0. Probe: removing the ready() import made 5 tests fail.
- **Next:** T007: docs and demo.
- **Watch:** Tests pin STATICFILES_FINDERS to the file-system finder so images the demo gains in US-2 cannot satisfy the missing-image test.

## 2026-09-24T07:48Z · Implementer US1 · T007

- **Did:** Wrote docs/installable-app.md, linked it from docs/index.md, added the pwa keys to docs/configuration.md, added Installable app and Service worker to CONTEXT.md, turned the feature on in demo/settings.py and mounted mvp.pwa.urls in demo/urls.py; tests/test_demo/test_installable_app.py.
- **Verified:** poetry run pytest tests/test_demo tests/test_smoke.py — 154 passed, exit 0.
- **Next:** Full verify, then the report.
- **Watch:** The demo warns mvp.W002 until US-2 supplies images; the demo test does not assert its absence.

## 2026-09-24 — US-1 accepted

Re-verified independently at the story's tip. Conformance and docs were red on the returned
work: the resolver sat in the package's `__init__.py`, which has no test module to mirror, and
four new public names had no page. The resolver moved to `mvp/pwa/resolver.py` with its tests
in `tests/test_pwa/test_resolver.py`, and `docs/installable-app.md` gained a Python reference
section. After that, every step was green. The tamper flag on `tests/test_templates.py` covers
new imports and new test classes only, and no existing assertion changed.
