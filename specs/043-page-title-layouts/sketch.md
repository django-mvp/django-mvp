# Sketch: Page titles share one set of arguments and a choice of layouts

## What exists

- `PageMixin` (`mvp/views/base.py`) builds the `page` context from one attribute and one
  `get_*()` method per value: `page_title`, `page_subtitle`, `page_info`, `page_info_actions`,
  `page_class`, `page_width`, `breadcrumbs`.
- `<c-mvp.page.title>` draws the title row, with `inline_actions` as its one variation. It is
  called from `page_view.html`, `form_view.html` (which overrides `page.content-wrapper` and so
  repeats the title), `list_view.html` (inline, with its actions in the toolbar) and
  `mvp/account/overview.html`.
- `table_view.html` does not use the component: it writes its own one-line `<h1>`, info trigger,
  result summary and subtitle into the title slot of `<c-mvp.page.table.toolbar>`.
- `detail_view.html` fills `page.actions` with Edit and Delete; list and table pages fill it with
  Add, inside their toolbars.
- daisy-cotton-ext's `<c-heading>` sets the family's eyebrow and lead: small semibold uppercase
  tracked text for the eyebrow, and both at `text-base-content/80`.

## What the screens need from the code

- Every view carries a page type (page, form, detail, delete, list, table), so the settings can
  name a layout for each.
- The view resolves its layout: its own `page_title_layout`, then the setting for its page type,
  then the setting for every page.
- Each page template hands the title its arguments as one group. The sketch passes each argument
  separately, in four templates that repeat the same block structure (FR-003).
- On the table page the result summary sits outside the `page.title` block, because the title
  can now be above the bar while the summary stays in it. `page.summary` is no longer nested in
  `page.title`.
- On detail, list and table pages, the view's actions are drawn before the package's own (Edit and
  Delete, or Add).
- The title component takes a layout by name and draws a project's own component by name.

## What the sketch faked

- The demo chooses a layout from `?title_layout=` through a demo-only mixin, so every layout
  can be seen on every page type without editing settings. The package itself reads only the view
  and the settings.
- The Page Title demo's Bookmark button does nothing, and the product detail page's Share button
  links to `#`.
- An unknown layout name raises Django's template-not-found error from the dynamic component,
  not an error naming the value and the view (FR-012). There is no startup check on the setting.
- The arguments are not passed to the title as one group (FR-003).
- There are no tests, and the documentation and `CONTEXT.md` are not updated.

## What was ruled by eye

Nothing yet.

## Design decisions

Recorded before and during the build. **Convention** decisions follow a rule; **taste**
decisions are a choice that had to be made.

| Decision | Class | Reason |
|---|---|---|
| One `<h1>` per page in every layout; the info trigger beside it, never inside it | Convention | The project's existing pattern: a control inside a heading becomes part of the heading's accessible name |
| No heading element when the title is empty | Convention | An empty heading has no accessible name (WCAG 2.4.6) |
| Eyebrow and lead at `text-base-content/80`, where the lead was at 70% opacity | Convention | WCAG 1.4.3 needs 4.5:1. daisy-cotton-ext measured 70% at 3.86:1 on the winter theme (daisy-cotton-ext #21). This is a small visible change to every existing lead |
| Lead capped at the prose width | Convention | Line length of about 75 characters (GOV.UK Design System, type scale), and the project already caps it there |
| Eyebrow style taken from daisy-cotton-ext's `<c-heading>` | Convention | The family's own established pattern outranks a fresh one |
| Eyebrow before the heading in source order | Convention | Source order matches the visual order (WCAG 1.3.2) |
| List and table pages keep their actions in the toolbar in every layout | Convention | The project's pattern: a list's actions sit with its controls |
| Centred heading one step larger than the other layouts, with extra space above and below | Taste | A centred title opens a section, so it should read as one |
| Centred actions under the lead, not beside the heading | Taste | Matches the heroes; in a centred column, a side position has nothing to align to |
| Compact eyebrow drawn inline before the heading, a size smaller | Taste | Keeps the layout one row high, which is the point of compact |
| On a table page, any layout but compact sits inside the toolbar's band, above its bar | Taste | It keeps one band at the top of the page with one background and one rule under it |
| Actions set on the view drawn as small buttons | Taste | Matches the size the package's own Edit, Delete and Add already use |
| Headings balanced and leads wrapped to avoid orphans | Taste | Long titles wrap evenly instead of leaving a single word |
