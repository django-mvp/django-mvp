# Implementation Plan: Sheets for phones and wide screens

**Branch**: `047-sheet` · **Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md)

## Summary

Five Cotton templates under `mvp/templates/cotton/mvp/sheet/` (the sheet, a view, a trigger, a
menu and a menu item), one registered Alpine component, `mvpSheet`, in `assets/js/sheet.js`, and a
block of rules in `mvp/tailwind/base.css`. The sheet sits in daisy-cotton's `c-modal` with
`modal-bottom sm:modal-middle`, so the browser's `<dialog>` supplies Escape, the focus trap and the
backdrop, and daisyUI supplies the narrow and wide placement. The script adds what a `<dialog>`
lacks: named views, the window event that opens a sheet, one open sheet at a time, focus return, the
two heights, the drag and flick, and the keyboard offset. The look is ported from the agreed
design, class names renamed under `mvp-sheet-` and colours replaced by theme variables.

## Technical context

- Python 3.12+, Django 5.2, 6.0 and 6.1. No new Python dependency, no new npm dependency.
- Front-end assets are committed build artifacts (Article XV): `npm run build:js:prod` and
  `uv run invoke build-stylesheet` after editing `assets/js/` or `mvp/tailwind/base.css`.
- Rendered-markup tests with `cotton_render_string_soup` in `tests/test_components/test_sheet.py`.
  Real-browser tests in `tests/test_components/test_sheet_e2e.py` (Article XIV's exception: layout,
  focus, drag and the page behind cannot be read from markup).
- The drag is driven in Chromium through the DevTools protocol's touch events with real timing, at
  a phone viewport with touch enabled. The wide screen is driven with the mouse.

## The markup contract (what tests and FS-048 rely on)

`<c-mvp.sheet id title sub icon full fixed wide class>`

- `id` and `title` required. `sub` is the line under the title. `icon` is an icon name drawn before
  the title. `full` opens at the full height, `fixed` keeps the sheet at its resting height, `wide`
  adds the package's wide size for the centred dialog. Slots: default (the body, views and menus),
  `art` (small art before the title), `description` (text that becomes the dialog's accessible
  description), `actions` (the foot, replacing the default closing button).
- Renders a `<dialog id class="modal modal-bottom sm:modal-middle mvp-sheet">` named by
  `aria-labelledby="{id}-title"`, described by `aria-describedby="{id}-description"` when there is
  one, carrying `data-mvp-sheet`, `data-mvp-sheet-full` and `data-mvp-sheet-fixed` when set, and
  `x-data="mvpSheet({ id })"`. Inside the box: the grab bar (`<button type="button"
  data-mvp-sheet-grab>` with `aria-label`), the head (`data-mvp-sheet-head`), the body
  (`data-mvp-sheet-body`) and the foot. Every closing control is `type="button"`.
- Views: `<c-mvp.sheet.view name="confirm">` renders `<div data-mvp-sheet-view="confirm"
  x-show="view === 'confirm'">`. The sheet's Alpine scope has `view` and `show(name)`, so any element
  inside switches with `@click="show('confirm')"`.
- Trigger: `<c-mvp.sheet.trigger for="id" href label view returns id>` renders `<a href>` when an
  address is given and a `<button type="button">` when not, with `aria-haspopup="dialog"`, an
  accessible name made from `label`, and a click that dispatches `mvp-sheet-open` on `window`
  with `{ id, view, returns, opener }`. An empty slot draws the icon-only button, a slot its words.
- Menu: `<c-mvp.sheet.menu>` is the list, `<c-mvp.sheet.menu.item text icon href danger>` a row,
  rendered with `c-menu` and `c-menu.item`.
- Any element opens a sheet with `$dispatch('mvp-sheet-open', { id, view })`.

## Heights and the drag (US3)

The box is a flex column: head and grab bar pinned, body `min-h-0 flex-1 overflow-y-auto`. At rest the
box's height is its content's up to `--mvp-sheet-rest` (50dvh); at full it is `--mvp-sheet-full`
(`100dvh` less the gap). `data-height="rest|full"` on the dialog is the state. A drag on the grab bar
or head (`touch-action: none` there, pointer capture on pointerdown, the first pointer only) sets
the box's height or its downward translate from the finger, records the last samples for velocity,
and on release `settle()` picks the target by D16 and animates there, then writes `data-height` and
clears the inline styles. Closing animates the box off the bottom and then calls `close()`.
`prefers-reduced-motion` skips every animation. The script's numbers are named constants.
The grab bar button toggles rest and full (not when fixed) and carries `aria-expanded`-style state
as `aria-label` text and `data-height`, since the platform controls read as expand and collapse.
At and above `sm` the script ignores pointer drags and hides nothing itself: the grab bar is hidden
by the stylesheet and `settle` is never called.

## Constitution check

| Article | How |
|---|---|
| I Testing | Test-first per task. Wording and design preferences (widths, spacing) are not tested. Roles, names, focus, heights reached by gestures, closing without submitting are |
| II Simplicity | One script module, five templates, no setting, no dependency |
| III Anti-abstraction | The menu wrapper has a present second use: FS-048's menu in the same sheet. No other abstraction |
| V Security | No user input reaches markup unescaped. Title, sub, labels are escaped by the template layer |
| VI Documentation | `docs/components.md` and `docs/developer/sheets.md` land in the tasks that add each name, README, CHANGELOG |
| VIII i18n | Grab bar label, closing button, More-for label are translatable |
| XI Components are the public API | The five templates, their properties and the `mvp-sheet-open` event are documented |
| XIII Rendered markup is a contract | Every `data-mvp-sheet-*` hook the script reads is asserted in rendered markup |
| XIV Browser tests are the exception | Drag, height, focus, scroll lock, keyboard offset, fallback link with scripts off |
| XV Built assets are committed | Stylesheet, its brotli copy and the bundle rebuilt on the branch |

## Which scenario is which kind of test

Rendered markup: US1 scenarios 1–10, 13, 14, FR-001, 003–005, 009, 019 (the wide size class). Real
browser: US1 scenarios 11, 12, 15; every US2 and US3 scenario; all edge cases; SC-002 to SC-005.
The keyboard offset (US2 scenario 10) is driven by redefining `visualViewport.height` and firing
`resize`, since no automated browser draws a keyboard; that is named in the test.

## Risks

- A closed sheet in a page of rows costs an Alpine instance each. A closed sheet binds nothing to
  `window` except the one `mvp-sheet-open` listener, and only the open one listens for pointer
  moves and `visualViewport` resizes (edge case: many sheets).
- `touch-action: none` on the head means a vertical swipe starting there never scrolls the page.
  That is the intent: the head is the drag region.
- FS-049 and FS-048 also touch `base.css`, `index.js`, the demo and the changelog. The sheet's
  rules sit in one block with its own comment header and the script registers on its own line, so
  a conflict is a keep-both resolution.
