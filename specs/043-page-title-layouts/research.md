# Research: Page titles share one set of arguments and a choice of layouts

Done after the sketch was approved, against main at `f75475ff`. The approved templates, markup and
copy are kept; everything behind them is rebuilt test-first.

## Planning notes, answered

**Follow daisy-cotton-ext's heroes.** Adopted for the vocabulary and the look. The arguments are
eyebrow, title, lead and actions, the names the three hero layouts share. The eyebrow and lead
classes copy daisy-cotton-ext's `<c-heading>` (`daisy_cotton_ext/templates/cotton/heading/index.html`),
including its `text-base-content/80` contrast floor. **Not adopted:** calling `<c-heading>` or the
hero components themselves. daisy-cotton-ext is a development dependency of django-mvp only
(`pyproject.toml`, `[dependency-groups].dev`), so a shipped template cannot use it. The heroes'
`level`, `invert`, `size`, `announcement`, `footnote` and `media` are left out, as the spec says.

**Every part has a block as well as a view attribute.** Adopted. Each argument has a view
attribute, a `get_*()` method and a block: `page.eyebrow`, `page.heading`, `page.lead`,
`page.actions` and `page.info`, nested in `page.title`.

**One attribute per part, or one dictionary?** Adopted as settled at intake. One attribute and one
method per part, and one method, `get_page_title_args()`, that gathers them into a dict. The page
context carries that dict as `page.title_args`, and each page template passes it whole to
`<c-mvp.page.title>` as `:args`. A slot given for an argument replaces that argument; an argument
with no slot is taken from `args`. A new argument therefore reaches every layout, including a
project's own, without any page template changing. Only its override block has to be added. The
four templates still each declare the blocks, because Django blocks cannot be shared through an
include, and `form_view.html` and `table_view.html` have to place the title somewhere other than
`page_view.html` does.

**No deprecations.** Adopted. `page_subtitle`, `get_page_subtitle()`, `page.subtitle` and the
component's `subtitle` attribute are removed and nothing warns. The CHANGELOG's Unreleased section
says so under a breaking-change heading.

## What the sketch needs, and how each is met

| Need | How |
|---|---|
| A page type on every view | `PageMixin.page_type = "page"`, overridden by `MVPFormBase` (`form`), `MVPDeleteView` (`delete`), `MVPDetailView` (`detail`), `MVPListViewMixin` (`list`) and `MVPTableViewMixin` (`table`). Built in the sketch; kept |
| Layout resolution | `get_page_title_layout()`: the view's `page_title_layout`, else `MVP_CONFIG["page_title"]["layout"]`, a string for every page or a dict by page type. A dict the project gives is deep-merged with the defaults by the existing `mergedeep` call, so naming one page type leaves the others at their defaults |
| An unknown name fails loudly (FR-012) | A function in `mvp/utils.py` turns a layout name into its component name. A shipped name maps to `mvp.page.title.<name>`; any other name must resolve to a Cotton template, probed with Django's `select_template` on the same candidates Cotton itself tries (`cotton/<path>.html`, then `cotton/<path>/index.html`, snake-cased). Otherwise it raises `ImproperlyConfigured` naming the value. The view calls it and adds its own class name to the message |
| The setting fails at startup | A system check in `mvp/checks.py`, `mvp.E003`, runs the same function over every value in the setting |
| Arguments as one group (FR-003) | `get_page_title_args()` and `:args`, above |
| The table page's summary outside `page.title` | Kept from the sketch. The summary is in the toolbar's own title slot, so the heading can move above the bar without it |
| View actions before the package's own | `page.actions` defaults to the view's actions. `detail_view.html` calls `{{ block.super }}` before Edit and Delete; `list_view.html` and `table_view.html` draw them before Add |
| A project's own component, by name | The same resolver; `<c-component is>` draws it |

The sketch's demo-only `?title_layout=` mixin stays in the demo, because it is how the Page Title
page shows every layout on every page type. It is in `demo/views.py` and is never shipped.

## Unknowns settled

- **Telling an emptied block from an argument with no block.** Cotton leaves a slot that was
  never given unset, so `<c-vars>` sees `None`; a slot given with nothing in it is an empty string.
  The dispatcher uses the slot when it is not `None`, and otherwise the value in `args`. A block a
  project empties therefore draws nothing (FR-005), and a direct caller that passes only attributes
  still works (FR-018).
- **Direct callers.** `<c-mvp.page.title title=… lead=… info=… layout=…>` keeps working with plain
  attributes, which the dispatcher folds into `args`. `inline_actions` with no `layout` picks
  `inline`.
- **The table page's toolbar.** `<c-mvp.page.table.toolbar>` gains a `heading` slot and a
  `heading_above` flag, as sketched. Compact draws the heading at the start of the bar; any other
  layout draws it above the bar, inside the same band.
- **Empty title.** No `<h1>` is drawn. The info trigger is drawn only beside a heading, so it goes
  too.

## What already exists

| New piece | Where the search stopped |
|---|---|
| Per-argument attributes and methods | 2, this repo: the `page_info` / `get_page_info()` pattern in `PageMixin` |
| Picking a layout component by name | 3, django-cotton: `<c-component is>`, already used in `cotton/app/navbar.html` and `cotton/mvp/page/list/actions/index.html` |
| Deciding whether a slot is empty | 2, this repo: the `slot_is_empty` filter in `mvp/templatetags/mvp.py` |
| Drawing an action from a dict | 3, daisy-cotton: `<c-button :attrs="…">`, as `cotton/mvp/page/info.html` draws `page_info_actions` |
| Merging a partial setting with the defaults | 2, this repo: the `mergedeep.merge` call in `mvp/config.py` |
| Checking a component template exists | 4, Django: `django.template.loader.select_template` on Cotton's candidate paths |
| A startup check on a setting | 2, this repo: `mvp/checks.py`, registered in `mvp/apps.py` |
| The four layout templates | 7, new code: no layout of this shape exists in the repo, daisy-cotton or Django |
| The name-to-component resolver and its error | 7, new code: a few lines in `mvp/utils.py` |

## Documentation to update

- `docs/views.md`: the page attributes (`page_eyebrow`, `page_lead`, `page_actions`,
  `page_title_layout`, `get_page_title_args()`), and the two places that mention the subtitle.
- `docs/layout.md`: a "Page title" section with the layouts, the setting, the blocks and a
  project's own layout, and the block tables that mention the subtitle.
- `docs/configuration.md`: `MVP_CONFIG["page_title"]`.
- `docs/components.md`: `c-mvp.page.title` and its layouts.
- `docs/integrations.md`: the table page's `page.title` row.
- `CONTEXT.md`: page title, title, eyebrow, lead, page actions, title layout.
- `CHANGELOG.md`: the feature and the breaking rename, under Unreleased.
