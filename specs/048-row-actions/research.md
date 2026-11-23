# Research: Swipe and menu actions on list rows

Checked against `origin/main` on 2026-11-22, with the sheet (FS-047) and the reorderable list
(FS-049) both merged. Planning notes are answered at the end.

## Assumptions checked

| Assumption | Check | Result |
|---|---|---|
| `c-list.row` exists | Read daisy-cotton's `list/row.html` | Holds: `<li class="list-row {{ class }}" {{ attrs }}>{{ slot }}</li>`, with `class` and `attrs` and one slot |
| htmx is part of the shipped front end | `assets/js/index.js` imports `htmx.org` into the bundle built to `mvp/static/js/django-mvp.js` | Holds |
| Scripts ship with the package, not from a CDN | Same bundle, built by esbuild from `assets/js/` | Holds: a new module joins that bundle |
| The default icon names include one for the ⋯ trigger | `mvp/utils.py` | Fails for the name `ellipsis`. `more, options, kebab` is the vertical three dots. FR-029 adds `ellipsis` as the horizontal three dots, resolved through the configured provider, with no icon file shipped (ADR 0038) |
| The sheet exists | `mvp/templates/cotton/mvp/sheet/` | Holds (FS-047): `c-mvp.sheet`, `.trigger`, `.view`, `.menu`, `.menu.item`. A trigger opens a sheet by dispatching `mvp-sheet-open` on `window` with the sheet's id |
| Reordering announces its start and end | `assets/js/reorder.js`, ADR 0045 | Holds: `mvp:reorder-start` and `mvp:reorder-end` are dispatched on the list's root element (`[data-mvp-reorder]`), bubble, and carry `detail.source` of `drag`, `button` or `mode`. A drag and a button move each fire a pair and a reorder mode fires one pair around the whole mode, so the pairs nest |
| Alpine sets up markup that htmx swaps in | Alpine's mutation observer, which `c-mvp.sheet` and `c-mvp.reorder` already rely on | Holds: a row carrying `x-data` is set up when it arrives, so rows that arrive by htmx need no extra call |
| The sheet menu item takes arbitrary attributes | `sheet/menu/item.html` passes `:attrs` to `c-menu.item` | Holds: `id`, `form`, `hx-*` and `aria-label` land on the link or button |

## What the agreed look is made of

Read from the files of the agreed design. Each piece, and
what it becomes in the package:

| Reference piece | What it is | What it becomes |
|---|---|---|
| Row template | A list item holding a face (the content that narrows) and an under layer of buttons | `c-mvp.list.row` over `c-list.row`: the face and the ⋯ control are rendered by the template, the under layer by the script (below) |
| Button template | An icon over a word, a tone, "full", "leaves", an accessible label | `c-mvp.list.row.action`, a thin wrapper of `c-mvp.sheet.menu.item` carrying the same marks as data attributes |
| Assets template | Links the stylesheet and script | Dropped: both ship in the package's own bundle and stylesheet |
| Gesture script | Pointer drag, wheel, 60% commit, flick, edges, one open row, hint, fold and restore | `assets/js/row_actions.js`: ported, then cleaned. It becomes one Alpine component registered in `index.js`, with named constants, no global written by the script other than the documented interface, mouse dragging removed (D1), direction taken from the page's direction (D2), the inert and focus rules of D3, and the reorder announcements (FR-025) |
| Stylesheet | The face narrows (`width: calc(100% + x)`), the under layer widens, the full button grows past 60%, reduced motion | A block in `mvp/tailwind/base.css` under the prefix `mvp-row-`, with daisyUI theme variables and logical properties kept as they are |
| Menu template | The ⋯: a dropdown for a mouse, a sheet for a finger, the menu given once and drawn twice | The ⋯ control of `c-mvp.list.row`, with the menu drawn once (D10), see the answers below |
| Pointer rules | `pointer: fine` shows the dropdown, `pointer: coarse` the sheet button | Kept: the browser resolves it in CSS (ADR 0021), with the sheet button shown only once the script has set the row up |
| App glue script | Two application-specific actions | Not carried. Evidence only |

## Defects of the reference that are not carried forward

1. The menu is drawn twice with one copy hidden by CSS, so every id and form hook is on the page
   twice. The package draws it once.
2. A mouse can drag a row. It cannot here (D1).
3. Only left-to-right pages are handled. The package mirrors on right-to-left (D2). The face
   narrows from the end edge and the layer under it sits on that edge with logical properties,
   which already mirror. Only the arithmetic of the drag and the wheel needs the page's direction.
4. Tabbing to a button under a closed row opens the row. The package takes those buttons out of
   the tab order instead and sends a keyboard user to the menu (D3).
5. Its script interface is published under one global name while the reorder code looks for
   another. The package publishes one, `mvpRows`, documents it, and also answers the reorder
   announcements itself so nothing needs to find the global.
6. The commit always folds the row. A main action that does not take the row out of the list
   slides back closed instead (FR-016).

## Planning notes, answered

1. **Sheet and dropdown (adopted).** The ⋯ control holds a `c-mvp.dropdown` and a
   `c-mvp.sheet.trigger` for a `c-mvp.sheet`. The one menu is drawn into the dropdown's panel, so a
   page without script opens it as a dropdown on every device. When the sheet opens, the script
   moves that one `<ul>` into the sheet's body, and moves it back when the sheet closes. One
   menu, so each id once (D10), and no script means a working dropdown.
2. **Build on the list row components (adopted).** `c-mvp.list.row` renders `c-list.row`, so the
   list's own look and dividers apply. The `list-row` grid moves to the face and the outer item
   becomes a block, because the item holds the face and the layer under it. A row with no actions
   renders as the plain `c-list.row` and nothing else.
3. **Reorder announcements and the script interface (adopted).** A listener on `document` for
   `mvp:reorder-start` and `mvp:reorder-end` switches swiping off for the announcing element and
   back on. Pairs nest, so it counts. `window.mvpRows.off(list)`, `.on(list)` and `.shut()` are the
   developer's interface, with a flag of their own beside the count.
4. **Gesture code is the package's own (adopted).** Part of the bundle built from `assets/js/`.
   Nothing is fetched; icons come from the icon provider (G14's exception).
5. **The look carried across (adopted).** The row narrowing rather than sliding and the main
   action filling the row past 60% are in the stylesheet block ported from the reference.
6. **Platform conventions, no status badges (adopted).** The under buttons are an icon over a
   word, as in mail and music apps. No badge is drawn.
7. **Drawn twice (not carried).** See defect 1.
8. **Script interface under one name (adopted).** See defect 5.

## What already exists

| New piece | Where the search stopped |
|---|---|
| The menu's items | This repo: `c-mvp.sheet.menu` and `.menu.item` (FS-047). The row's action wraps the item |
| The dropdown | This repo: `c-mvp.dropdown` with its upgrade script `dropdown.js` |
| The sheet, its trigger and focus return | This repo: `c-mvp.sheet`, `c-mvp.sheet.trigger`, `mvpSheet` |
| The list row | An installed package: daisy-cotton's `c-list.row` |
| The ⋯ icon | This repo: `mvp/utils.py` default names gain `ellipsis`, resolved by the configured provider |
| Swipe to reveal, fold, flick velocity | New code. No maintained package was adopted: the gesture is a few hundred lines already agreed, and a dependency would add more than it removes |
| A unique id for the row's sheet | The developer gives the row an `id`, as `c-mvp.sheet` already requires |
| Counting main actions | New code: one template filter, because a template cannot raise |
| `window.mvpRows` | New code: a three-method object, the documented interface FR-024 asks for |
