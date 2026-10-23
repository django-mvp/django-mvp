# Tasks — 043 Page titles share one set of arguments and a choice of layouts

**Branch**: `043-page-title-layouts` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md) · **Sketch**: [sketch.md](sketch.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green, and the work is committed. Documentation for a public name lands in the task that introduces
it. A task that changes a template's classes runs `invoke build-stylesheet` and commits the
artifact. The approved sketch's markup, classes and copy are the starting point for every
template; the code behind them is written here, test-first.

## Order

US-1 → US-2 → US-3 → US-4 → US-5, in the feature worktree, in two dispatches (plan, *Story order
and dispatch*).

---

## US-1 — A developer sets a page's eyebrow, lead and actions from its view (P1)

Issue: #595. Delivers FR-001–FR-004, FR-014, FR-015, FR-017, SC-003, SC-005.

### T001 — The title's arguments on the view

**Files**: `mvp/views/base.py`, `mvp/views/account.py`, `tests/test_views/test_base.py`,
`tests/test_views/test_extra.py`, `docs/views.md`, `CHANGELOG.md`

Tests (`TestPageTitleArgs`): each of `page_eyebrow`, `page_lead`, `page_actions` defaults empty and
reaches `page.title_args`; each `get_*()` override wins over its attribute; a subclass changing one
attribute keeps the parent's others; overriding `get_page_title_args()` replaces the whole group;
`page.title`, `page.info` and `page.info_actions` are still in the context; `page.subtitle` is not,
and a view setting `page_subtitle` puts no lead in `title_args`. Then the code, and the existing
`subtitle` assertions renamed to the lead. Docs: the page attributes table in `docs/views.md`; the
CHANGELOG's Unreleased section, with the rename under a breaking-change heading.

### T002 — The component takes the group, and slots override it

**Files**: `mvp/templates/cotton/mvp/page/title/index.html`,
`tests/test_components/test_page_title.py`, `docs/components.md`

Tests (`TestPageTitleArguments`): `args` alone draws every argument; a slot given for an argument
replaces its `args` value; a slot given empty draws nothing for that argument; a plain attribute
(`title`, `eyebrow`, `lead`, `info`, `info_actions`) is used when no slot is given; actions given
as a list of dicts are drawn as buttons with each dict's keys; the info trigger is drawn from
`info` and `info_actions` unless `info_trigger` is given; an argument absent everywhere draws no
element. Docs: `c-mvp.page.title` in `docs/components.md`, with `args`, `layout` and the slots.

### T003 — Every page template draws its title from the group

**Files**: `mvp/templates/page_view.html`, `mvp/templates/form_view.html`,
`mvp/templates/list_view.html`, `mvp/templates/table_view.html`,
`mvp/templates/detail_view.html`, `mvp/templates/mvp/account/overview.html`,
`tests/test_views/test_list.py`, `tests/test_views/test_detail.py`, `tests/test_views/test_edit.py`,
`tests/test_table_layout.py`, `tests/test_templates.py`

Tests: on a page, form, detail, delete, list and table view that sets every argument, the title
draws each one; on list and table views the view's actions are in the toolbar before Add and not in
the title; on a detail view they are drawn with Edit and Delete; a view setting nothing new renders
the same title area as before apart from the lead's name and contrast (SC-003). Then the templates:
`:args="page.title_args"`, `:layout="page.title_layout"`, and each slot filled from its block.

## US-2 — A developer chooses the title layout for the whole site (P1)

Issue: #596. Delivers FR-007–FR-009, FR-013, FR-016, SC-001, SC-004.

### T004 — Each view's page type, and the setting

**Files**: `mvp/views/base.py`, `mvp/views/edit.py`, `mvp/views/detail.py`, `mvp/views/list.py`,
`mvp/integrations/django_tables/views.py`, `mvp/config.py`, `tests/test_views/test_base.py`,
`docs/configuration.md`

Tests (`TestPageTitleLayoutSetting`): with no setting each view type resolves its current layout
(default for page, form, detail and delete; inline for list; compact for table); a string setting
applies to every type; a dict naming one type changes that type and leaves the rest at their
defaults. Docs: `MVP_CONFIG["page_title"]` in `docs/configuration.md`.

### T005 — The four layouts' rendered contract

**Files**: `mvp/templates/cotton/mvp/page/title/default.html`, `inline.html`, `centred.html`,
`compact.html`, `mvp/templates/cotton/mvp/page/table/toolbar.html`,
`tests/test_components/test_page_title.py`, `tests/test_table_layout.py`, `docs/layout.md`,
`docs/integrations.md`, `mvp/static/css/django-mvp.css`

Tests (`TestPageTitleLayouts`, parametrised over the four layouts): every argument given is drawn;
an argument not given leaves no element behind; exactly one `<h1>`, holding the title text and no
control; the info trigger is a sibling of the `<h1>`, not inside it; an empty title draws no `<h1>`.
On a table page: compact puts the heading in the toolbar's bar; any other layout puts it above the
bar, and the bar keeps its controls and result summary. Docs: a "Page title" section in
`docs/layout.md` (the layouts, the setting, choosing per view); the table page's `page.title` row in
`docs/integrations.md` and the block tables in `docs/layout.md` and `docs/views.md`.

## US-3 — A developer chooses a different title layout for one view (P1)

Issue: #597. Delivers FR-010, FR-012.

### T006 — Resolving a layout name, and its error at render time

**Files**: `mvp/utils.py`, `mvp/templatetags/mvp.py`, `mvp/views/base.py`, `tests/test_utils.py`,
`tests/test_views/test_base.py`, `docs/views.md`

Tests (`TestTitleLayoutComponent`): a shipped name maps to its component; a project component name
that exists, as `<name>.html` or `<name>/index.html`, is returned unchanged; an unknown name raises
`ImproperlyConfigured` naming the value. (`TestPageTitleLayoutOnTheView`): `page_title_layout` on a
view wins over the setting; an overridden `get_page_title_layout()` wins; an unknown name on a view
raises at render time with the value and the view's class name in the message. Docs: the two view
attributes in `docs/views.md`.

### T007 — The setting is checked at startup

**Files**: `mvp/checks.py`, `mvp/apps.py`, `tests/test_checks.py`, `docs/configuration.md`

Tests: a valid string and a valid dict produce no message; an unknown name, as the string or as one
value in the dict, produces `mvp.E003` naming the value. Docs: the check in
`docs/configuration.md`.

## US-4 — A developer replaces one part of a page's title in a template (P2)

Issue: #598. Delivers FR-005, FR-006, FR-018.

### T008 — A block for every argument, on every page type

**Files**: `tests/test_templates.py`, `tests/fixtures` or `tests/templates/` as the existing tests
do, `docs/layout.md`

Tests (`TestPageTitleBlocks`, over the page, form, list, table and detail templates): filling
`page.eyebrow`, `page.heading`, `page.lead`, `page.info` or `page.actions` replaces that argument
alone, in each shipped layout; filling one with nothing removes it even though the view sets it;
overriding `page.title` replaces the whole area; a template calling `<c-mvp.page.title>` directly
with attributes and a layout draws what a page view with the same arguments draws; a direct call
with `inline_actions` and no layout draws the inline layout. Docs: the blocks in `docs/layout.md`.

## US-5 — A developer adds a title layout of their own (P3)

Issue: #599. Delivers FR-011.

### T009 — A project's own layout

**Files**: `tests/templates/cotton/…` (a test layout), `tests/test_components/test_page_title.py`,
`docs/layout.md`

Tests: a project component named in the setting draws every page's title, receiving the five
slots and `args`; one named on a view draws that view's title only; a filled block's content
reaches the project's layout in place of the view value. Docs: "A layout of your own" in
`docs/layout.md`, the slots it receives and an example.

## Cross-cutting

### T010 — The glossary, the demo and the map

**Files**: `CONTEXT.md`, `demo/views.py`, `tests/test_demo/test_page_title.py`,
`skills/django-mvp/SKILL.md`

Tests: the demo's Page Title page renders each layout chosen by `?title_layout=` and ignores an
unknown value; its switches add and remove each argument. Then `CONTEXT.md`'s entries (page title,
title, eyebrow, lead, page actions, title layout) and the `c-mvp.page.title` line, and the skill's
routing table pointing at the new `docs/layout.md` section.
