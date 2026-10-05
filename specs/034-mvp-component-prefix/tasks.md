# Tasks — 034 Every component this package keeps moves under the mvp. prefix

**Branch**: `034-mvp-component-prefix` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I where a test can decide the result.
A task is done when its tests pass, the tree is green, and the work is committed. Wording and
documentation get no test (testing standard, section 1).

## Order

**US1 → US2 → US3 → US4, one at a time, in one worktree.** They share the templates,
`mvp/config.py` and the tests (plan, *Story order*).

---

## US1 — A template names the package's components under their own prefix (P1)

Issue: #451. Delivers FR-001 to FR-007 and the default half of FR-008.

### T001 — The guard, written first

**Files**: `tests/test_components/test_component_prefix.py` (new)

Plan, *New tests*. `TestComponentPrefix`: every template under `mvp/templates/cotton/` is under
`mvp/` or on the exception list, with the offenders named in the failure; every exception
exists; `<c-page>`, `<c-toolbar>` and `<c-data-field>` raise `TemplateDoesNotExist`.
`TestNamesSharedWithDaisyCotton`, skipped at class level when `daisy_cotton` cannot be imported:
the template paths shared with daisy-cotton are exactly the exception list. The constant is
`PREFIX_EXCEPTIONS`. Run this class once before the move and once after with the published
0.1.2 wheel on the import path (it is not a dependency yet): 22 shared before, the 17 after.
Record both runs in `progress.md`.

Also first, in `tests/test_views/test_htmx.py`: an invalid htmx post to a stub view that sets no
`htmx_form_component` and does not patch `render_component` answers 200 with the form partial.
It passes before the move, fails after it, and passes again when the default becomes
`"mvp.form"`.

The first and third tests fail before the move, for the right reason (67 offenders named; the
three old names render). Commit them red together with T002, not on their own, so no commit
leaves the suite failing.

### T002 — Move the 67 templates and every caller in the package, the demo and the tests

**Files**: `mvp/templates/cotton/**`, `mvp/templates/**`, `mvp/config.py`,
`mvp/templatetags/mvp.py`, `mvp/views/htmx.py`, `mvp/tailwind/base.css` (comments only), `assets/js/layout.js`
(comment only), `demo/**`, `tests/**`

Plan, *The mapping* and *The move is one commit*; research R1, R2, R8.

1. Capture the before state (plan, *Proving nothing changed*) into a scratch directory outside
   the repository.
2. Move the 67 templates with `git mv` and rewrite every mention by script, following the
   mapping table exactly.
3. Edit by hand what the script cannot be trusted with: the names in `mvp/config.py:75,92`,
   `mvp/views/htmx.py:147` (and its docstrings at `:135` and `:182`), `demo/settings.py:148-154`
   and `tests/settings.py`, widget names in monkeypatched lists (`test_layout_config.py:50-51`
   and `:73-78`, `test_app_header.py:176`), paths built from segments with `pathlib`
   (`test_list_filter_action.py:30`, `test_form_formset.py:863` and `:1070-1077`,
   `tests/test_demo/test_library.py:73`), the path in `mvp/templatetags/mvp.py`, the path in the
   `mvp/config.py` warning and its docstring, the `is="page.list.actions.…"` literal, the
   tests' `cotton_render*` / `render_component` names and `render_to_string` / `get_template` /
   `template_name` paths, the `SKIP` key in `test_render_all.py`, and path comments.
4. Capture the after state and compare. Component output identical; page output identical apart
   from tags printed as text on gallery pages. Capture the demo URLs under `demo.settings` as
   well as `tests.settings`, before and after.
5. Confirm `test_render_all.py` and `test_declared_attributes.py` still collect 84 and the same
   number of declaring components as before.
6. Search `mvp/`, `demo/`, `tests/` and `assets/` for every old name: none left. The script's
   prose rule also rewrites the docstring examples in `mvp/fixtures.py`; T006 confirms them.

Existing tests change only where they name a component or a template path. No assertion is
changed, removed or weakened, and no test is skipped.

T001's tests pass. The full suite passes.

---

## US2 — A component named in settings is found under its new name (P2)

Issue: #452. Delivers FR-008, FR-009.

### T003 — The three settings scenarios

**Files**: `tests/test_components/test_layout_config.py`

Plan, *New tests*, settings paragraph. Default configuration: the theme controller and the login
widget are in the navbar, in that order. The default lists come from a fresh evaluation of
`mvp/config.py` with `MVP_CONFIG` empty (the imported module is left alone) and are then
rendered; the names are never typed into the test. The default already moved in T002, so these
tests are added green: probe each by putting an old name back and seeing it fail, and say so in
the report. A configuration naming a packaged widget by its prefixed
name: that widget is in the navbar. A configuration naming `navbar.test-widget`: the demo's
widget is in the navbar. Assert on ids or `data-` hooks the widgets already carry, not on text.
Where an existing test already proves a scenario after T002, do not duplicate it: name it in the
report.

### T004 — Document how a widget is named

**Files**: `docs/configuration.md`, `docs/layout.md`

The sections on navbar widget lists show the prefixed names for packaged widgets, say that a name
is written in full the way it would follow `c-` in a tag, that nothing is added for the project,
and that a project's own component is listed by its own name. Update every example on those two
pages that names a packaged widget or the path a name resolves to.

---

## US3 — A project upgrading finds every renamed component in one place (P2)

Issue: #453. Delivers FR-010, FR-011, FR-012, FR-017.

### T005 — An override follows its component

**Files**: `tests/test_templates.py`, `tests/fixtures/override_templates/cotton/mvp/app/sidebar/footer.html`,
`tests/fixtures/override_templates/cotton/app/sidebar/footer.html`

Plan, *New tests*, overrides paragraph; research R5. With the fixture directory first in the
template search path, as `test_a_project_head_template_replaces_the_packaged_one` does it, a page
that draws the sidebar carries the prefixed-path template's `data-` marker and not the old-path
template's.

### T006 — The fixtures' examples

**Files**: `mvp/fixtures.py` (docstrings only), `tests/test_fixtures.py` (confirm)

Each docstring example that names a moved component uses the prefixed name. Confirm
`tests/test_fixtures.py` renders a moved component by its prefixed name through each fixture; add
a case only where a fixture has none.

### T007 — The changelog entry

**Files**: `CHANGELOG.md`

Plan, *The record*, changelog bullet. Under `## [Unreleased]`, `### Changed`, marked breaking.
The note on names outside a tag covers overrides, names in `MVP_CONFIG`, and a view's
`htmx_form_component` set to `"form"`. The table has one row per moved component, generated from the files under
`mvp/templates/cotton/mvp/` and checked against that directory: 67 rows, no duplicates. No
version heading, no version bump, nothing else in the file touched.

---

## US4 — The documentation, the demo and the project's rules describe the new names (P3)

Issue: #454. Delivers FR-013, FR-014, FR-015. FR-016's guard landed in T001.

### T008 — Documentation, README and the assistant skill

**Files**: `docs/*.md`, `docs/contributing/**`, `README.md`, `CONTRIBUTING.md`,
`skills/django-mvp/SKILL.md`

Apply the mapping to every tag, every name in prose and every template path, including the
documented default of `htmx_form_component` in `docs/integrations.md`. `docs/configuration.md`
and `docs/layout.md` were done in T004: sweep them, do not redo them. Not `docs/adr/`,
not `docs/ROADMAP.md` (research R7, D16). `docs/components.md` gains a short statement of the
rule: the prefix, the icon exception, the basic components waiting on #435, and that an override
sits at the prefixed path. Every example must be true against the branch: each tag resolves to a
template that exists. Close with a search for every old name in these files: none left.

### T009 — The glossary

**Files**: `CONTEXT.md`

The component library lists every component under its current name. The naming rules state the
prefix, the icon exception and the components waiting on #435, and the examples in rules 1 and 3
are true.

### T010 — Article XI

**Files**: `CONSTITUTION.md`

Plan, *The record*, constitution bullet. Amend Article XI and nothing else in the document
except the version line: 5.1.0, last amended on the day of the change.

---

## Convergence

### TC01 — Decision record

**Files**: `docs/adr/NNNN-the-packages-components-carry-a-prefix.md`

Written at convergence, numbered from what is free on `main` at the merge gate.
