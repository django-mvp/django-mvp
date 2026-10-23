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
`get_page_context()` keeps `title`, `info`, `info_actions`, `class`, `breadcrumbs` and `width`
for the templates that use them outside the title (the browser title, the share menu, the form
heading), drops `subtitle`, and adds `title_args` (the dict) and `title_layout` (the layout's
name, such as `compact`, never the component name).

`get_page_title_layout()` returns the view's `page_title_layout`, or the setting for the view's
`page_type`. `get_page_context()` passes the result through `title_layout_component()` (below) so
an unknown name raises `ImproperlyConfigured` with the view's class name in the message.

`page_type` is documented in `PageMixin`'s docstring and in `docs/views.md`. It is set on `MVPFormBase` (`form`), `MVPDeleteView` (`delete`), `MVPDetailView`
(`detail`), `MVPListViewMixin` (`list`) and `MVPTableViewMixin` (`table`).

### The setting (`mvp/config.py`) and its check (`mvp/checks.py`)

`MVP_CONFIG["page_title"]["layout"]` defaults to a dict by page type: `default` for page, form,
detail and delete, `inline` for list, `compact` for table. A string replaces the dict; a dict is
deep-merged with it. `mvp.E003` runs every value through the resolver at startup.

### The resolver (`mvp/utils.py`)

`title_layout_component(name) -> str`: a shipped name returns `mvp.page.title.<name>`. Any other
name is probed with `select_template` on exactly the four candidates django-cotton 2.8 tries
(`django_cotton/templatetags/_component.py:449-464`): the configured `COTTON_DIR` path, its
`/index.html`, then, when different, the default `cotton/` path and its `/index.html`, with
`COTTON_SNAKE_CASED_NAMES` applied as Cotton applies it. The name is returned unchanged when one
exists.
Otherwise it raises `ImproperlyConfigured` naming the value and the shipped names. The
`title_layout_component` filter in `mvp/templatetags/mvp.py` calls it, so a direct caller of the
component gets the same check.

### The component (`cotton/mvp/page/title/`)

`index.html` is the dispatcher. It declares `layout=""`, `title`, `heading`, `eyebrow`, `lead`,
`info`, `info_actions`, `info_trigger`, `actions`, `inline_actions` and `class`, every one with an
empty default, so a bare call (without `only`) never reads a same-named variable from the caller's
page. (Cotton reads an undeclared-default name from the caller's context when the call has no
`only`: `django_cotton/templatetags/_component.py:322-332`; a declared default shadows it,
`_vars.py:100-102`.) The heading is the `heading` slot when it has content, otherwise `title`. The
info trigger is the `info_trigger` slot when it has content, otherwise one drawn from `info` and
`info_actions`. It hands the five parts (`eyebrow`, `heading`, `lead`, `info`, `actions`) to the
chosen layout as slots through `<c-component is="…" :attrs="attrs" only>`, so a direct caller's
own attributes still land on the layout's root. The component takes no `args`: the page templates
fill every slot from the group, so nothing would read it.

`default.html`, `inline.html`, `centred.html` and `compact.html` are the sketch's markup, kept as
approved, with one change: the info trigger is drawn whenever it has content, beside the heading
when there is one, so an empty title or an emptied `page.heading` removes that argument alone
(spec edge case, FR-005, FR-008).

### The page templates

`page_view.html`, `form_view.html`, `list_view.html`, `table_view.html` and
`mvp/account/overview.html` call the component with `:layout="page.title_layout"` and fill each
slot from a block whose default reads the group: `page.eyebrow` from `page.title_args.eyebrow`,
`page.heading` from `.title`, `page.lead` from `.lead`, `page.info` from `.info`, `.info_actions`
and `.title`, and `page.actions` from `.actions`, drawn as `<c-button>`s. Overriding
`get_page_title_args()` therefore changes what is drawn. On list and table pages the title is given
an empty actions slot, and `page.actions` stays in the toolbar, drawing `page.title_args.actions`
before Add. `detail_view.html` calls `{{ block.super }}` before Edit and Delete. `table_view.html`
puts the title in the toolbar's new `heading` slot and sets `heading_above` unless the layout is
compact; the result summary stays in the bar's `title` slot.

## Story order and dispatch

US-1 → US-2 → US-3 → US-4 → US-5, sequentially in the feature worktree. Two Sonnet dispatches:
**A** US-1, US-2 and US-3 (the view, the setting, the component, the layouts, the resolver and the
check). A starts by restoring the sketch's Python (`mvp/views/`, `mvp/config.py`,
`mvp/integrations/django_tables/views.py`, `mvp/templatetags/mvp.py`) to origin/main, so its tests
are written red and the code rebuilt under them. The approved templates stay; a test written
against a template that already passes is shown able to fail by a recorded mutation; **B** US-4 and US-5 (the blocks on every page type, a project's own layout, and the rest of
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
