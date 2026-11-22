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
