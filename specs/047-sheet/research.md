# Research: Sheets for phones and wide screens

What the specification rests on: how the platforms' own sheets behave, and the assumptions about
this repository checked before the specification gate. The rest of the research (how the sheet is
built) belongs to planning and answers the notes in `planning-notes.md`.

## How the platforms' sheets behave

Read on 2026-11-22.

| Behaviour | iOS (`UISheetPresentationController`) | Android (Material `BottomSheetBehavior`, modal) | This specification |
|---|---|---|---|
| Heights a sheet rests at | Detents: medium (about half the screen) and large, or custom ones | Collapsed (peek height), half-expanded (0.5 by default) and expanded; `fitToContents` sizes the expanded state to the content | Resting (content height up to a limit) and full, every sheet able to reach full unless the developer fixes it at resting (D2, D3) |
| Closing by drag | Dragging down from the smallest detent dismisses, unless the sheet is modal-in-presentation | `hideable` is true for modal sheets: dragging below the lowest state hides it | Dragging or flicking down from resting closes (D5) |
| Release | Settles at a detent, with velocity taken into account | Above the significant velocity threshold (500 px/s by default) the sheet moves in the fling's direction, otherwise to the nearest state | Nearest height by position, one step in the flick's direction when fast (D5) |
| Drag from scrolling content | `prefersScrollingExpandsWhenScrolledToEdge`, on by default | `draggableOnNestedScroll`, on by default | Not taken: drags start on the grab bar and head (D4) |
| Grab bar | `prefersGrabberVisible`; VoiceOver can activate it | Drag handle, optional; tapping cycles expanded and collapsed, double tapping hides, TalkBack offers expand and collapse | A control switching between the two heights (D6) |
| Wide screens | Sheets become centred form sheets on iPad | `maxWidth` 640dp; large screens use side sheets or dialogs | Centred dialog, no grab bar, no dragging (FR-019) |
| Tapping outside | Dismisses, unless modal-in-presentation | Dismisses a modal sheet | Closes (FR-010) |

Sources: Apple's `UISheetPresentationController` reference (detents, `prefersGrabberVisible`,
`prefersScrollingExpandsWhenScrolledToEdge`, `largestUndimmedDetentIdentifier`), and the Material
Components for Android bottom sheet documentation (`docs/components/BottomSheet.md`: states,
`behavior_significantVelocityThreshold`, `behavior_draggableOnNestedScroll`, the drag handle's
accessibility behaviour, `maxWidth`).

## Assumptions checked

Run on 2026-11-22 against `origin/main` in this branch's worktree.

| Assumption | Result |
|---|---|
| daisy-cotton's `c-modal` puts its `class` on the `<dialog>`, so `modal-bottom sm:modal-middle` reaches it | Holds on daisy-cotton 0.2.0: rendered `class="modal  modal-bottom sm:modal-middle"` on the dialog. |
| `c-mvp.modal` still draws a card inside the modal box | Holds: it renders `c-mvp.card` inside `c-modal`. https://github.com/django-mvp/django-mvp/issues/684 removes that, and the build waits for it. |
| The built stylesheet carries daisyUI's responsive modal placement | Partly. `.modal-bottom` is in `mvp/static/css/django-mvp.css`, `sm:modal-middle` is not, because no template uses it yet. The sheet's template brings it into the scan and the stylesheet is rebuilt (planning note 11). |
| Alpine runs on every app shell page, so the sheet's views can use it | Holds: `mvp/templates/mvp/base.html` loads `js/django-mvp.js`, which bundles Alpine, htmx and the package's own modules from `assets/js/`. |
| daisy-cotton's modal closes without submitting a surrounding form | Holds: its closing button and backdrop are `type="button"` controls calling `close()`. |
| A `<dialog>` can be opened without scripts | Only through invoker commands, which older supported browsers lack. The trigger falls back to a link (D9, planning note 8). |

## Planning notes, answered

Read on 2026-11-22, against `origin/main` after the modal was redrawn on its own box.

1. **Where the sheet is drawn.** Adopted in part. The sheet sits in daisy-cotton's `c-modal`, the
   box `c-mvp.modal` is drawn on, and passes `modal-bottom sm:modal-middle` through its `class`
   (checked: `class` lands on the `<dialog>`, `content_class` on the box). It does not wrap
   `c-mvp.modal` itself (its `class` goes to the box, so the dialog cannot take `sm:modal-middle`; FR-002 is reworded to name `c-modal`), because that component draws its own heading row and names the dialog
   from `aria-label`, while a sheet draws a head of its own (grab bar, art, title, line under it)
   and names the dialog from that title (D12). daisy-cotton is not changed.
2. **FS-048's trigger and menu.** Adopted. The trigger and the menu are components with a
   documented set of properties, not inline markup, and the window event that opens a sheet is
   documented as public (D13).
3. **Gesture code.** Adopted: a registered Alpine component in `assets/js/sheet.js`
   (`docs/adr/0035-behaviour-lives-in-registered-alpine-components.md`). No gesture library: the
   whole gesture is one pointer on one element moving along one axis, which the browser's pointer
   events with pointer capture give directly, and a library for it would add bytes to every page
   for the sheets of the few that use one (D14).
4. **Desktop.** Adopted. `sm:modal-middle` plus a rule hiding the grab bar from `sm` up, and the
   script reads the same width as a media query, so on a wide screen there is no drag to start.
5. **The agreed design.** Adopted. See "What is ported" below.
6. **Names.** `c-mvp.bottom_sheet`, `c-mvp.bottom_sheet.view`, `c-mvp.bottom_sheet.trigger`, `c-mvp.bottom_sheet.menu` and
   `c-mvp.bottom_sheet.menu.item`. The menu is the package's own thin wrapper over daisy-cotton's
   `c-menu` and `c-menu.item`, which already render an icon with words as a link or a button
   (checked in daisy-cotton 0.2.0). The wrapper adds what they lack: the sheet's row sizing and a
   `danger` mark on an item (D15).
7. **Gesture numbers.** Fixed in D16, each from the platforms' documentation read above: the
   flick threshold is Material's `significantVelocityThreshold`, 500 px/s; the resting limit is
   the half-expanded and medium detents' half of the screen; the settle animation is the length
   Material's own sheet uses for settling.
8. **Invoker commands.** Not adopted. `commandfor` with `command="show-modal"` reached baseline
   support in January 2026 (MDN, "Invoker Commands API"; InfoQ, 2026-01), but it works only on a
   `<button>`, and the fallback for a trigger given an address has to be a link that works in
   every browser still in use. A trigger given no address is a button that needs scripts anyway,
   since views, heights, focus return and one-sheet-at-a-time are all script (D9).
9. **The on-screen keyboard.** `<dialog>` opened with `showModal()` is `position: fixed` against
   the layout viewport. Chrome on Android resizes only the visual viewport since Chrome 108, which
   matches Safari and Chrome on iOS (Chrome for Developers, "Prepare for viewport resize behavior
   changes coming to Chrome on Android"), so a bottom-anchored box stays where the keyboard is
   drawn over it. The package does not set `interactive-widget` (it would apply to the page, not
   the sheet) and does not use the VirtualKeyboard API (Chromium only). The sheet reads
   `window.visualViewport`: while open it sets the distance between the layout viewport's bottom
   and the visual viewport's bottom as a custom property on the dialog, the box takes that as a
   bottom offset and its maximum height shrinks by it, and a focused field is scrolled into view
   inside the body (D17).
10. **Which scenarios are browser tests.** Everything about dragging, height, focus, the page
    behind and the keyboard offset is a browser test, because it reads layout or events. Everything
    about what the markup holds, names and falls back to is a rendered-template assertion. The
    split is in `plan.md`.
11. **The stylesheet.** Adopted: `sm:modal-middle` is written in the sheet's template so the
    Tailwind scan finds it, and the stylesheet and its brotli copy are rebuilt and committed.

## What is ported

The agreed design is read from the two source checkouts with `git show`, never checked out. Each
piece becomes the following. Class prefixes are the package's, `mvp-sheet-`, and colours are
daisyUI theme variables.

| Agreed piece | Becomes |
|---|---|
| The sheet's dialog, box, grab bar, title, closing button and backdrop | `mvp/templates/cotton/mvp/bottom_sheet/index.html`; the rules in `mvp/tailwind/base.css` |
| A head with art, a title and a line under it, and a rule | the same template's head, `mvp-sheet-head` |
| The tall box with a pinned head and a scrolling body | the full height, which every sheet now has: the box is a column whose body scrolls |
| One panel of the body shown by name | `c-mvp.bottom_sheet.view` |
| The ⋮ button, a link where scripts do not run | `c-mvp.bottom_sheet.trigger`, icon button form |
| The worded link that opens a sheet from a sheet and returns focus | `c-mvp.bottom_sheet.trigger`, worded form, with `returns` |
| The menu of icon-and-words rows, a destructive row last | `c-mvp.bottom_sheet.menu` and `c-mvp.bottom_sheet.menu.item` |
| The open-at-a-view window event | the `mvp-sheet-open` window event, documented |
| The grab bar swipe | replaced by the drag to either height (new, specified) |

## What already exists

One line per piece the plan would write, the first place on the existing-first list where the
search stopped.

| Piece | Found | Where |
|---|---|---|
| Modal box, backdrop, closing controls, responsive placement | an installed package | daisy-cotton `c-modal` and daisyUI `modal-bottom sm:modal-middle` |
| A menu row, link or button, with an icon | an installed package | daisy-cotton `c-menu`, `c-menu.item` |
| Icon by name | this repo | `c-icon` and the packaged icon set (`more` is checked in the first task) |
| Escape, focus trap, system back gesture, focus return on close | the browser | `<dialog>` with `showModal()` |
| Page behind does not scroll | an installed package | daisyUI's `:root:has(.modal[open])` overflow lock in the built stylesheet |
| Hiding a panel | an installed package | Alpine `x-show` |
| Pointer tracking with capture | the browser | pointer events and `setPointerCapture` |
| Reduced motion, wide screen | the browser | `prefers-reduced-motion` and `matchMedia`, as `page_side.js` already reads |
| Keyboard offset | the browser | `window.visualViewport` |
| An Alpine component registered once and configured by markup | this repo | `assets/js/page_side.js` and `index.js` |
| Showing the window events other components use | this repo | `mvp-page-side-open`, the same shape |
| The sheet's script and rules | new code | `assets/js/sheet.js`, `mvp/tailwind/base.css`. No package does the two heights and the drag on a native `<dialog>`; a pointer-events gesture is the smallest thing that does |
| Sheet, view, trigger, menu and menu item templates | new code | `mvp/templates/cotton/mvp/bottom_sheet/` |
