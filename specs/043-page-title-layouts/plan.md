# Implementation Plan: Page titles share one set of arguments and a choice of layouts

**Branch**: `043-page-title-layouts` · **Spec**: [spec.md](spec.md) · **Research**:
[research.md](research.md) · **Sketch**: [sketch.md](sketch.md)

## Summary

Every page title is drawn by `<c-mvp.page.title>` from one group of arguments the view gathers,
in a layout the view or the settings choose. The approved sketch's templates, classes and copy are
kept. The view code, the component's argument handling, the layout resolver and the checks behind
them are written test-first.

## Technical context

Python 3.12+, Django 5.2–6.1, django-cotton 2.8, daisy-cotton 0.2, Tailwind v4 with daisyUI 5 (the
built stylesheet is committed). Tests are pytest with the Django test client and rendered-template
assertions (Article XIV: no browser test is needed, since nothing here is behaviour a browser alone
can show).

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every task writes its tests first; the sketch's code is rewritten under them |
| II Simplicity, III Anti-abstraction | One resolver function and four templates; no registry class, no layout base class |
| VI, XVII Documentation | Each public name is documented in the task that introduces it |
| XI Components are the public API | The layouts are Cotton components under `cotton/mvp/page/title/`, reached by name |
| XII Configuration-driven layout | Resolution order: the view's layout, then `MVP_CONFIG["page_title"]["layout"]`, then the package default for the page type |
| XIII Rendered markup is a contract | Each layout has rendered-markup tests: one `<h1>`, the info trigger outside it, no empty element |
| XV Build artifacts | Tasks that change template classes rebuild and commit the stylesheet |
| XVI Compatibility | The `page_subtitle` rename is recorded in the CHANGELOG as breaking (pre-1.0, minor version) |
| XVIII Views forward component attributes as a dict | Not engaged: the new view attributes are the content of the title, which the view decides, not presentation of a component |

## Design

### The view (`mvp/views/base.py`)

`PageMixin` gains `page_eyebrow`, `page_lead`, `page_actions`, `page_title_layout` and `page_type`,
each value attribute with its `get_*()` method, as the sketch built. `page_subtitle` and
`get_page_subtitle()` go.

`get_page_title_args()` returns
`{"eyebrow", "title", "lead", "actions", "info", "info_actions"}` from the six methods.
`get_page_context()` keeps `title`, `info`, `info_actions`, `class`, `breadcrumbs` and `width`,
drops `subtitle`, and adds `title_args` (the dict) and `title_layout` (the resolved name).

`get_page_title_layout()` returns the view's `page_title_layout`, or the setting for the view's
`page_type`. `get_page_context()` passes the result through `title_layout_component()` (below) so
an unknown name raises `ImproperlyConfigured` with the view's class name in the message.

`page_type` is set on `MVPFormBase` (`form`), `MVPDeleteView` (`delete`), `MVPDetailView`
(`detail`), `MVPListViewMixin` (`list`) and `MVPTableViewMixin` (`table`).

### The setting (`mvp/config.py`) and its check (`mvp/checks.py`)

`MVP_CONFIG["page_title"]["layout"]` defaults to a dict by page type: `default` for page, form,
detail and delete, `inline` for list, `compact` for table. A string replaces the dict; a dict is
deep-merged with it. `mvp.E003` runs every value through the resolver at startup.

### The resolver (`mvp/utils.py`)

`title_layout_component(name) -> str`: a shipped name returns `mvp.page.title.<name>`. Any other
name is probed with `select_template` on the paths Cotton tries (`COTTON_DIR`, snake-cased when
`COTTON_SNAKE_CASED_NAMES` is on, then `/index.html`) and returned unchanged when one exists.
Otherwise it raises `ImproperlyConfigured` naming the value and the shipped names. The
`title_layout_component` filter in `mvp/templatetags/mvp.py` calls it, so a direct caller of the
component gets the same check.

### The component (`cotton/mvp/page/title/`)

`index.html` is the dispatcher. It takes `args` plus the plain attributes `title`, `eyebrow`,
`lead`, `info`, `info_actions`, `layout` and `inline_actions`, and the slots `eyebrow`, `heading`,
`lead`, `info_trigger` and `actions`. For each argument: a slot that was given, even empty, wins;
otherwise the attribute; otherwise `args`. It draws the info trigger from `info` and `info_actions`
unless `info_trigger` was given, and draws `actions` from a list of dicts as `<c-button>`s unless
the slot was given. It passes the five resolved parts, and `args` itself, to the chosen layout
through `<c-component is>`.

`default.html`, `inline.html`, `centred.html` and `compact.html` are the sketch's markup, kept as
approved.

### The page templates

`page_view.html`, `form_view.html`, `list_view.html` and `table_view.html` call the component with
`:args="page.title_args"` and `:layout="page.title_layout"`, and fill each slot from a block whose
default is the view's value: `page.eyebrow`, `page.heading`, `page.lead`, `page.info` and
`page.actions`. On list and table pages the title has no actions slot; `page.actions` stays in the
toolbar, drawing the view's actions before Add. `detail_view.html` calls `{{ block.super }}` before
Edit and Delete. `table_view.html` puts the title in the toolbar's new `heading` slot and sets
`heading_above` unless the layout is compact; the result summary stays in the bar's `title` slot.
`mvp/account/overview.html` passes `lead`.

## Story order and dispatch

US-1 → US-2 → US-3 → US-4 → US-5, sequentially in the feature worktree. Two Sonnet dispatches:
**A** US-1, US-2 and US-3 (the view, the setting, the component, the layouts, the resolver and the
check); **B** US-4 and US-5 (the blocks on every page type, a project's own layout, and the rest of
the documentation). B builds on A's accepted commit.

## Tests changed by this feature

| Test | Change |
|---|---|
| `tests/test_views/test_base.py`, `test_extra.py` — `subtitle` assertions | Renamed to the lead, read from `page.title_args` |
| `tests/test_views/test_list.py`, `test_detail.py`, `test_edit.py` — page context `subtitle` keys | The same |
| `tests/test_table_layout.py` — the title's position in the toolbar | Asserts the compact title in the bar and the summary in its own slot |
| `tests/test_templates.py` — `c-mvp.page.title` with `subtitle` | `lead` |

## Sketch debt

Every item under "What the sketch faked" is a task: the resolver and its errors (T006, T007), the
group of arguments (T001, T003), and tests and documentation in every task. The demo's
`?title_layout=` mixin stays as the demo's own feature and gets a demo test (T010).

## Cost estimate

Two Sonnet dispatches, about $15–25 each: $30–50 in all, inside the $120 hard budget.
