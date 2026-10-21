# Sketch: FS-042

The prototype was built before this specification and reviewed by Sam on the demo site over four
rounds (2026-10-20 and 2026-10-21). It is on branch `sketch/page-side`: the demo pages
"Layout › Side Panel" (every option switchable from a form at the top of the page) and
"List, Side Filters".

## What exists

- `mvp/templates/page_view.html` draws the title, then the content, inside `<c-mvp.page.content>`.
  The list and table page templates extend it and fill `page.content`.
- The app header (`cotton/app/header.html`) is `sticky top-0`; the window scrolls, not `<main>`,
  so `position: sticky` works on a page column with no scroll container of its own.
- The list page's filter form wraps the toolbar fields and the filter modal
  (`cotton/mvp/page/list/filters/modal.html`); `list_view.js` submits it on change.
- `slot_is_empty` (`templatetags/mvp.py`) is the package's test for an empty Cotton slot.

## What the screens need from the code

- The page layout needs to know the panel's side and alignment to place it, from the panel itself.
- The list panel needs the fields not named for the toolbar, the count of those applied, and the
  URL that clears them: the three values the filter modal is given today.
- The list panel's fields need to be submitted with the toolbar's form while drawn outside it.
- The list view needs a way for a developer to set the panel's width, side, alignment and
  breakpoint.
- Sticking needs the header's current height.

## What the sketch faked

- The list panel is a demo template (`demo/templates/demo/product_list_side.html`) with a second
  form that copies the toolbar's values as hidden inputs. The real list and table templates still
  use the modal.
- The page layout finds the panel's side by searching the rendered slot for an attribute value.
- The drawer's behaviour is written inline in the panel template's `x-data`.
- The drawer does not keep focus inside itself, and an open drawer stays open when the window is
  widened past the breakpoint.
- The column's own scrolling region is not focusable or named.
- Pages that fill the screen's height are not handled.
- `breakpoint=False` is not supported; the prototype offers `lg`, `xl` and `2xl` only.
- No tests, no documentation page, no component reference entry, no changelog entry.

## What was ruled by eye

- The panel's heading is small, semi-bold and muted, as in the existing "On this page" list on the
  documentation site.
- Widths: 14rem, 16rem and 20rem. Gap between content and column: 2.5rem.
- The column starts level with the title by default; on a list page, level with the content (round
  3).
- On an end-side column the panel fills its column, so the gap between content and panel is the
  same at both sides (round 4).
- A sticky column stands 1rem below the header.
- The list panel's apply and clear actions stay at the panel's foot.
- The panel button carries an icon and a one-word label, with the applied count as a badge.
