# Tasks — 035 The basic components come from daisy-cotton

**Branch**: `035-basic-components-from-daisy-cotton` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I where a test can decide the result.
A task is done when its tests pass, the tree is green, and the work is committed. Wording,
appearance and documentation get no test (testing standard, section 1).

## Order

**US1 and US2 together → US3 → US4, one at a time, in one worktree.** They share the packaged
templates and the tests (plan, *Story order*).

---

## US1 — A basic component's tag reaches daisy-cotton's component (P1)

Issue: #461. Delivers FR-001 to FR-005 and the removal half of FR-023.

### T001 — The tests that say whose component answers, written first

**Files**: `tests/test_components/test_basic_components.py` (new), a project-override template
under `tests/` for the precedence test, `tests/test_components/test_component_prefix.py`

Plan, *New tests*, first bullet. For each of the sixteen tags: the template it resolves to is
inside the daisy-cotton package, and this package ships no file at that path. A dashed button
takes effect. `full` on a button has no effect on the component and raises nothing. This
package's menu entry renders inside daisy-cotton's menu and its avatar inside daisy-cotton's
avatar group. A project template at `cotton/badge.html` in a `TEMPLATES["DIRS"]` directory is
the one rendered. `PREFIX_EXCEPTIONS` becomes the icon alone.

The resolution tests and the prefix tests fail before T002 for the right reason (the package's
own template answers). T001 to T005 are one commit, so no commit leaves the suite failing.

### T002 — Remove the sixteen templates

**Files**: `mvp/templates/cotton/{alert,badge,button,divider,link}.html`,
`mvp/templates/cotton/{avatar,breadcrumbs,dock,menu,mockup}/`

Plan, *What is deleted*. `git rm` the sixteen files. `cotton/icon.html` and `cotton/mvp/` stay.
Committed with T001 and T003 to T005.

---

## US2 — The package's own pages keep working on daisy-cotton's components (P1)

Issue: #462. Delivers FR-006 to FR-016 and FR-020 for the package, and the rewrite half of FR-023.

### T003 — Rewrite the tests that pinned the removed markup, and add the page tests

**Files**: the tests in plan, *Tests that change*; new tests per plan, *New tests*, second and
third bullets

Written before T004. Remove what only asserted a removed template's markup. Rewrite what the
package still promises against the markup now rendered. Add: messages at each level and at an
unknown level; `related_objects_attrs` forwarded; the dock's landmark, name, the toggle's accessible
name and the current item; the dock class from configuration and by default; the accessible names of the
theme chooser and the share menu; the sidebar menu's navigation landmark; and no former
attribute name as an HTML attribute on the shell, list, detail, delete, sign-in, sign-out and
error pages. The dock toggle's keyboard operation gets no test of any kind: it is a known gap
(plan, *The dock toggle and the keyboard*).

### T004 — Move every packaged caller to daisy-cotton's attributes

**Files**: the templates in plan, *The packaged callers*; docstrings and comments named there

Follow the table exactly. Do not add `only` here: that is US3, and its check has to be seen
failing first. The one exception is a call that cannot render correctly without it, which is
listed in the completion report.

### T005 — The breadcrumb rule and the stylesheet

**Files**: `mvp/tailwind/base.css`, the prebuilt stylesheet under `mvp/static/`,
`tests/fixtures/stylesheet_classes_0_26_0.txt` only if a class drops out

Plan, *Breadcrumb truncation* and *The stylesheet*. Move the selector, rebuild with
`uv run invoke build-stylesheet`, commit the built file. The three browser tests in
`test_app_header_e2e.py` and the coverage tests decide it. Name any class removed from the
fixture in the completion report.

### T011 — Tests the first pass left pinned to daisy-cotton's markup

**Files**: `tests/test_components/test_button.py`, `test_menu.py`,
`test_breadcrumbs_href_attribute.py`, `test_app_header_e2e.py`

Decision D21. Remove the tests of the button's sizes, the menu's former `grow` and the crumb's
own markup. Point the breadcrumb browser tests' locator at the crumb markup now rendered.

### T012 — Raise the floor on daisy-cotton to 0.1.3

**Files**: `pyproject.toml`, `uv.lock`, `docs/adr/0031-daisy-cotton-is-a-runtime-dependency.md`,
`CHANGELOG.md` (the range in the unreleased entry)

Decision D22.

---

## US3 — A page's own variables cannot change a packaged component (P2)

Issue: #463. Delivers FR-017 to FR-019.

### T006 — The check and the leak tests, written first

**Files**: `tests/test_components/test_daisy_cotton_calls.py` (new),
`tests/test_components/test_daisy_cotton_isolation.py`

Plan, *`only`, and the check for it* and *New tests*, fourth and fifth bullets. The check names
every unisolated call by template and tag, and a second test proves it reports an offender. The
leak test renders packaged pages with and without context variables named after the attributes
in research's table and compares each element drawn by a call the package makes directly. An attribute a kept
component forwards is outside it (D15). Slot content inside an isolated
alert reads a page variable. A dismissible alert under `only` still draws its button and its
icon through this package's lookup.

Run them before T007 and record in `progress.md` how many calls the check names and which
elements the leak test finds changed.

### T007 — Isolate every call

**Files**: every template under `mvp/templates/` that calls a daisy-cotton component

Add `only` to each call the check names. Nothing else about a call changes.

---

## US4 — A developer upgrading can move their templates from the changelog alone (P2)

Issue: #464. Delivers FR-021, FR-022, FR-024, and FR-006 and FR-007 for the demo and the
documentation.

### T008 — The demo scan, written first, then the demo

**Files**: `tests/test_demo/` (new test), `demo/templates/**`, `demo/component_docs.py`

Plan, *New tests*, last bullet, and *Demo, documentation, changelog*. The scan fails first on
the demo's former attribute names, then the demo templates move.

### T009 — Documentation

**Files**: `docs/components.md`, `docs/icons.md`, `docs/styling.md`, `docs/account-center.md`,
`docs/layout.md`, `docs/views.md`, `README.md`, `CONTEXT.md`, `skills/django-mvp/SKILL.md`, and
any other page a search for the former names finds

Plan, *Demo, documentation, changelog*. The component reference says the sixteen come from
daisy-cotton and links to its documentation, explains `only`, and says what an existing override
now affects. Every example on a touched page has to run against the branch.

### T010 — Changelog

**Files**: `CHANGELOG.md`

One entry under the unreleased heading, marked breaking: all sixteen tags, every row of the
table in FR-006 with its replacement, the divider's swap called out on its own line. No version
bump.
