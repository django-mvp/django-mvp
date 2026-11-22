# Planning notes: Sheets for phones and wide screens

Notes for research and planning to answer by name. None of them is settled.

## Shared pieces

1. The sheet is drawn on `c-mvp.modal`, which
   https://github.com/django-mvp/django-mvp/issues/684 is redrawing without card markup right
   now. Build waits for that merge. Responsive placement comes from daisyUI's own
   `modal-bottom sm:modal-middle` classes passed through `c-modal`'s `class`; daisy-cotton is not
   changed.
2. FS-048 (https://github.com/django-mvp/django-mvp/issues/688, row actions) reuses this sheet for
   a row's ⋯ menu on touch screens, so the trigger and the menu-list markup inside the sheet are
   part of this feature's public surface.
3. Gesture code is the package's own small script (django-mvp already ships
   `mvp/static/js/django-mvp.js` and loads Alpine and htmx); no gesture library unless research
   finds an established one worth its weight, and every asset is shipped with the package (goal
   G14), never fetched from a CDN.
4. Desktop (`pointer: fine`, wide screens): centred dialog, no grab bar, no gestures.

## The agreed design

5. The look is agreed and is ported, never redrawn from django-mvp's current components. The build
   is handed the agreed templates and styles, which are copied across and cleaned to the package's
   standards. In outline:

   | Piece of the agreed design | Lands in django-mvp |
   |---|---|
   | the sheet: grab bar, head with art, title and the line under it, body, foot with a default closing button | a component |
   | a view: one panel of the body, shown while it is the current view | a component |
   | the trigger: an icon button named for its item, or worded content, that falls back to a link | a component |
   | the menu: a list of actions, each an icon and words, a destructive action last | a component, or `c-menu` and `c-menu.item` if they carry it |
   | the tall sheet: a pinned head and a scrolling body | the full-height option |
   | the sheet's styles: grab bar, head, menu rows, pinned head, safe-area padding at the foot | the package's stylesheet |

   Every screen of a merged build is checked side by side against the agreed design.
6. Names to consider, in the package's own pattern: `c-mvp.sheet`, `c-mvp.sheet.view`,
   `c-mvp.sheet.trigger` and `c-mvp.sheet.menu`. Research settles them, and whether the menu is
   the package's own or daisy-cotton's `c-menu`.

## For research

7. The gestures copy the platforms' documented behaviour (`research.md`, "How the platforms'
   sheets behave"). Research fixes the resting height's limit, the distance and the speed that
   count as a flick, and the settle animation, from those sources, and records each with its
   source.
8. Whether invoker commands (`commandfor`, `command="show-modal"`) can open the sheet without
   scripts in the browsers the package supports, alongside the fallback link.
9. Keeping a focused field visible above the on-screen keyboard (FR-013): what iOS Safari and
   Android Chrome do with a field near the bottom of an open modal `<dialog>`, and whether the
   VirtualKeyboard API or `visualViewport` is needed.
10. The drag scenarios need a real browser with touch. Article XIV of the constitution reserves
    browser tests for behaviour like this, so research says which scenarios are browser tests and
    which are rendered-template assertions.
11. The built stylesheet holds `modal-bottom` but not `sm:modal-middle` today. The sheet's template
    brings it into the Tailwind scan, and the stylesheet is rebuilt and committed on the branch
    (Article XV).
