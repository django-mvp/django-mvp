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

## 2026-09-24T08:05Z · Implementer US2 · T008

- **Did:** Added resvg-py to the test group (poetry.lock updated) and to the deptry allowances in pyproject.toml.
- **Verified:** poetry run deptry . — no issues. Runtime dependency set unchanged.
- **Next:** T009: the command.
- **Watch:** The allowance moved from DEP001 to DEP004 in T009, see D5.

## 2026-09-24T08:15Z · Implementer US2 · T009

- **Did:** Added mvp/management/commands/mvp_pwa_icons.py and tests/test_management/test_commands/test_mvp_pwa_icons.py (16 tests; PNG size from IHDR, corner and edge pixels from the first scanline with the standard library).
- **Verified:** poetry run pytest tests/test_management -p no:playwright — 16 passed, exit 0. Probe: widening the maskable padding to 100% made the safe-zone test fail. Started red with "Unknown command".
- **Next:** T010: docs and demo images.
- **Watch:** deptry reported DEP004 on the lazy import; moved the allowance (D5).

## 2026-09-24T08:22Z · Implementer US2 · T010

- **Did:** Added the "Generating the images" section to docs/installable-app.md, generated demo/static/brand/pwa/*.png with `python manage.py mvp_pwa_icons --output-dir demo/static`, and added a demo test that mvp.W002 is absent.
- **Verified:** poetry run pytest tests/test_demo/test_installable_app.py — 4 passed, exit 0 (was 1 failed before the images existed). Full suite: poetry run pytest — 2262 passed, 1 skipped, exit 0.
- **Next:** Forge re-verifies.
- **Watch:** The demo has no brand/icon.svg of its own, so its images are rendered from the package's mark.

## 2026-09-24T10:20Z · Implementer US3 · T011

- **Did:** resolve() returns a configured `service_worker` as `worker_url`, else the reversed packaged worker. Added tests for each override alone (resolver and manifest), configured colours in the manifest and the theme-color tag, no colours for an unshipped theme, the configured worker in the head, and a project `mvp/pwa/head.html` (tests/pwa_templates) replacing the packaged one.
- **Verified:** `poetry run pytest tests/test_pwa tests/test_templates.py -p no:playwright` — 253 passed, exit 0. The two worker tests were red first (`/sw.js` instead of `/my-worker.js`). The other new tests passed on first run, since the overrides existed from US-1.
- **Next:** T012 documentation.
- **Watch:** none.

## 2026-09-24T10:30Z · Implementer US3 · T012

- **Did:** documented `pwa.service_worker` in docs/configuration.md; added "Colours for a theme of your own" and "Bringing your own worker" to docs/installable-app.md; CHANGELOG Unreleased/Added, README feature line; demo sets theme_color and background_color to its light page colour (#f8f6f2); regenerated the demo images with mvp_pwa_icons.
- **Verified:** see the full-verify results in the completion report.
- **Next:** Forge re-verifies.
- **Watch:** only the apple-touch and maskable images changed, since the others have transparent backgrounds.

## 2026-09-24 — S5 CONVERGE

Every FR and SC maps to delivered, tested behaviour, so no gap tasks were needed. The
cleanup pass left two defects fixed test-first. Theme lightness written without a percent sign
would have parsed as a hundredth of its value. The image command would have written into a
prefixed static directory, where the manifest never looks. It now uses the first unprefixed
entry, or asks for `--output-dir`. No decision met the ADR bar, and each one records why.

## 2026-09-24T12:20Z · Implementer US3 · T013

- **Did:** moved `reverse_or_none` and `site_name` from `mvp/pwa/resolver.py` to `mvp/utils.py`; the resolver and the checks import them from there, with no alias left behind. Added `TestReverseOrNone` and `TestSiteName` to `tests/test_utils.py` (red first on the missing import). The Python reference in docs/installable-app.md names the new location.
- **Verified:** `poetry run pytest tests/test_utils.py tests/test_pwa -q` → 396 passed.
- **Next:** T014.
- **Watch:** the resolver's own name tests still go through `resolve()`.

## 2026-09-24T12:50Z · Implementer US3 · T014

- **Did:** `MVP_CONFIG` gains top-level `site_name` and `short_name` and `pwa` becomes `False`, `True` or a dict whose one key is `theme_color`. `InstallableApp` in `mvp/pwa/resolver.py` reads the setting; the resolver, checks, manifest view and icon command go through it. `base.html` tests `mvp_config.pwa` and takes its title suffix from `site_name` when set. Tests for removed keys were rewritten to the new shape or deleted; the golden head fixture is untouched. Demo settings, docs/configuration.md, docs/installable-app.md, CHANGELOG and CONTEXT.md describe the new shape.
- **Verified:** `poetry run pytest tests -q -n auto --dist loadscope` → 2294 passed, 1 skipped. Full verify results are in the completion report.
- **Next:** Forge re-verifies.
- **Watch:** the manifest view writes `background_color` from the same colour as `theme_color`.
