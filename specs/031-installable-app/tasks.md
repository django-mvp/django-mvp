# Tasks — 031 Installable app

**Branch**: `031-installable-app` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed. Documentation for a public name lands in the task
that introduces it.

## Order

**US-1 → US-2 → US-3, one at a time, in one worktree.** They share `mvp/pwa/__init__.py`,
`mvp/templates/mvp/pwa/head.html` and the docs page (plan, *Story order*).

---

## US-1 — A project becomes installable by turning on one setting (P1)

Issue: #392. Delivers FR-001–FR-009, FR-012, FR-016–FR-018, and the US-1 parts of FR-019 and
FR-020.

### T001 — The off state is pinned before anything changes

**Files**: `tests/fixtures/base_head_off.html`, `tests/test_templates.py`

Render the `<head>` of a shell page on the untouched base, with the test settings and a fixed
request, and save it as the fixture. Add a test asserting that the same render still matches it
byte for byte. It passes now, and it must keep passing through every later task (SC-002, US-1
scenario 1).

### T002 — Configuration defaults and the resolver

**Files**: `mvp/config.py`, `mvp/pwa/__init__.py`, `tests/test_pwa/test_init.py`,
`tests/test_config.py`

Add the `"pwa"` block of research R1. Write `resolve(request)`, which returns the resolved name
(R3), short name, start URL and scope (the script prefix, R2), display, theme and background
colours (R4, falling back to omission), worker URL and the four image URLs (R5).

Tests:
- defaults
- name from `Site` with the sites framework installed, and from the request host without it
- the prefix under `set_script_prefix("/app/")`
- colours for a shipped theme and `None` for an unknown one

### T003 — The theme colours artifact and its build task

**Files**: `tasks.py`, `mvp/pwa/theme_colors.json`, `tests/test_pwa/test_theme_colors.py`
(add it to `non-mirror-paths` only if the conformance check says a JSON file has no mirror)

Write `invoke build-theme-colors` per R4: OKLCH → sRGB hex in plain Python, reading
`node_modules/daisyui/theme/*.css`, writing sorted, stable JSON. Add it to `prerelease`.
Generate and commit the artifact.

Tests:
- one entry per `[data-theme=…]` name in the committed stylesheet, with no extras
- every value matches `^#[0-9a-f]{6}$`
- `light` is `#ffffff`. Its base-100 is `oklch(100% 0 0)`, which is a fixed point that checks the
  conversion.

### T004 — Manifest and worker views, and the root URLconf

**Files**: `mvp/pwa/views.py`, `mvp/pwa/urls.py`, `mvp/templates/mvp/pwa/sw.js`,
`tests/test_pwa/test_views.py`, `tests/test_pwa/test_urls.py`, a test URLconf mounting
`mvp.pwa.urls` at `""`

Tests:
- Manifest: status 200, content type `application/manifest+json`. Keys `name`, `short_name`,
  `start_url`, `scope`, `display`, `icons` (192, 512, and a 512 with `purpose: "maskable"`).
  Colour keys present for a shipped theme and absent for an unknown one (US-1 scenarios 3 and 4).
- Worker: status 200, content type `text/javascript`, `Cache-Control: no-cache`, served at
  `/sw.js` (scenario 5).
- Worker body: it has no `fetch` listener (FR-009, scenario 6). Assert on the rendered text.
- Escaping: a site name containing `"`, `<` and `</script>` yields valid JSON that round-trips
  exactly (FR-017).
- Both views work with the feature on. They also answer when it is off, because mounting is the
  project's explicit act.

### T005 — The head template and its include

**Files**: `mvp/templates/mvp/pwa/head.html`, `mvp/templates/mvp/base.html`,
`tests/test_templates.py`

Include it exactly as research R8 shows, on the existing favicon line.

Tests:
- With the feature on: the manifest link, `theme-color` (present for a shipped theme, absent for
  an unknown one), the `apple-touch-icon`, `apple-mobile-web-app-title`, `mobile-web-app-capable`
  and the registration script naming the reversed worker URL (US-1 scenarios 2 and 7).
- A name containing `</script>` stays escaped in the head (FR-017).
- T001's golden-file test still passes with the feature off.
- The head carries no absolute URL to any host other than the site's own (FR-018).

### T006 — Startup warnings

**Files**: `mvp/pwa/checks.py`, `mvp/apps.py`, `tests/test_pwa/test_checks.py`

Write `mvp.W001` and `mvp.W002` per R7, registered in `ready()`.

Tests, using `override_settings` for the URLconf and a temporary static directory:
- no warnings with the feature off
- W001 when the include is missing, and when it is mounted under `pwa/`
- W002 naming each missing image, with a hint naming `mvp_pwa_icons`
- none when everything is in place

### T007 — US-1 documentation and demo

**Files**: `docs/installable-app.md` (new), `docs/index.md` (table of contents),
`docs/configuration.md` (the `pwa.enabled` key, pointing to the new page), `CONTEXT.md`
(glossary: *Installable app*, *Service worker*), `demo/settings.py`, `demo/urls.py`,
`tests/test_demo/`

The page covers turning it on, the root include and why it must be at the root, what the
packaged worker does and doesn't do, where the images must be, and the two warnings. Only the
US-1 half goes in. US-2 and US-3 extend the same page. The demo turns the feature on and mounts
the include. A demo test asserts the manifest answers.

The demo images come in T010. Until then W002 fires in the demo, which is correct, and the demo
test must not assert its absence.

---

## US-2 — The developer generates the app images from the brand mark (P2)

Issue: #393. Delivers FR-013–FR-015 and the US-2 parts of FR-019 and FR-020.

### T008 — `resvg-py` as a test dependency

**Files**: `pyproject.toml`, `poetry.lock`

Add it to the test group and to `DEP001` under `[tool.deptry.per_rule_ignores]`, with a one-line
reason beside the existing entries. `poetry run deptry .` stays clean. The runtime dependency
set does not change.

### T009 — The `mvp_pwa_icons` command

**Files**: `mvp/management/commands/mvp_pwa_icons.py`,
`tests/test_management/test_commands/test_mvp_pwa_icons.py`

Implement research R5 and R6.

Tests, reading PNG dimensions from the IHDR header:
- all four files are written at 192, 512, 512 and 180 (scenario 1)
- re-running after swapping the mark changes the bytes (scenario 2)
- a 1:2 mark is not stretched: the rendered image has transparent columns at left and right
  (edge case)
- the maskable and Apple images have an opaque corner pixel and the plain ones a transparent one
- with `resvg_py` import-blocked via `monkeypatch` on `sys.modules`, the command raises
  `CommandError` naming `resvg-py` (scenario 3)
- with only the package's mark available, the output says so (scenario 4)
- with neither `--output-dir` nor `STATICFILES_DIRS`, it raises a `CommandError` naming
  `--output-dir`
- it prompts for nothing (scenario 5)

### T010 — US-2 documentation and demo images

**Files**: `docs/installable-app.md`, `demo/static/brand/pwa/*.png`, `tests/test_demo/`

Document the command, the optional install, `--output-dir`, and running it in CI. Generate the
demo's four images with the command and commit them. The demo test now asserts no `mvp.W002`.

---

## US-3 — A project adjusts what it installs as (P3)

Issue: #394. Delivers FR-010, FR-011, and the US-3 parts of FR-012 and FR-019.

### T011 — Each value can be overridden, and the project's own worker can be registered

**Files**: `mvp/pwa/__init__.py`, `tests/test_pwa/test_init.py`, `tests/test_pwa/test_views.py`,
`tests/test_templates.py`

Tests:
- each of `name`, `short_name`, `start_url`, `display`, `theme_color` and `background_color`
  overrides alone, with the rest unchanged (scenario 1)
- configured colours reach both the manifest and the `theme-color` meta tag (scenario 2)
- an unshipped default theme with no colours omits them (scenario 3, already covered by T004;
  re-assert through the configuration path)
- a configured `service_worker` URL is the one the head registers (scenario 4)
- a project template at `mvp/pwa/head.html` in a test template directory replaces the packaged
  one (scenario 5)

### T012 — US-3 documentation

**Files**: `docs/installable-app.md`, `docs/configuration.md`

Document every `pwa.*` key in the configuration reference, and on the page: bringing your own
worker (including why it has to be served from the root to control the site), overriding
`mvp/pwa/head.html` and `mvp/pwa/sw.js`, and keeping colours in step with your own theme.
