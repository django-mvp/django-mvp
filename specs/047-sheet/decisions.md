# Decisions: Sheets for phones and wide screens

Rationale for the ambiguities settled while writing the specification, each resolved from the
issue, the agreed design and the platforms' documented sheet behaviour (`research.md`). How the
sheet is built is not settled here: that is research and planning, with the notes in
`planning-notes.md`.

## D1: One width for every sheet, daisyUI's small breakpoint

The agreed design changes from the bottom of the screen to the middle at two different widths in
different places. A component library has one. daisyUI's own responsive modal classes,
`modal-bottom sm:modal-middle`, change at its `sm` breakpoint (40rem), and taking the placement
from those classes means the package adds no breakpoint of its own and stays on daisyUI's
documented behaviour. A tablet in portrait is above that width and gets the centred dialog.

**ADR:** none. It follows from FR-002 and is documented with the component.

## D2: Two heights, resting and full

Sam asked for a sheet that is swiped closed and swiped up to grow. iOS sheets rest at detents
(medium and large) and Material bottom sheets at states (collapsed, half-expanded, expanded), and
both reduce, for a modal sheet, to a height where the sheet rests and the full height. Two heights
cover the request without a third state nobody asked for. The resting height is the content's
height up to a limit, because the agreed design sizes its menus to their content, and the limit
keeps the page visible above the sheet as both platforms do at their resting state.

**ADR:** none. The limit itself is a planning decision.

## D3: Every sheet can grow to its full height, unless the developer fixes it

The request is a sheet that is swiped up to grow, as the native sheet is. An iOS sheet with medium
and large detents grows to large whatever its content, so every sheet on a phone can be dragged,
flicked or switched by its grab bar to its full height, even when its content already shows in
full at its resting height. A developer whose sheet has nothing to gain from more room, such as a
two-item menu, fixes it at its resting height, which is an iOS sheet with only the medium detent.
A fixed sheet follows the finger a little when dragged up, so the drag is felt, settles back, and
still closes when dragged down.

## D4: Drags start on the grab bar and the head only

Both platforms let a drag inside scrolling content move the sheet once the content is scrolled to
its edge (iOS `prefersScrollingExpandsWhenScrolledToEdge`, Material
`draggableOnNestedScroll`). In a web page that hand-off fights the browser's own scrolling and any
slider, map or drag-to-reorder list a sheet holds. Starting drags on the grab bar and the head,
which is the region the issue names, keeps every control in the body working and is the smaller
script. Scrolling a long body works at both heights.

**ADR:** none.

## D5: A release settles by position, a flick by direction

Material decides a release by its significant velocity threshold: above it, the sheet moves in the
fling's direction; below it, it settles at the nearest state. iOS behaves the same way between
detents. One step per flick keeps a downward flick at full height from throwing away a sheet the
user only meant to shrink. The threshold itself is a planning decision.

## D6: The grab bar is a control

Material's drag handle is an accessibility control: tapping it cycles the sheet's states, and
TalkBack offers expand and collapse on it. iOS's grabber is likewise activated by VoiceOver. A
person who cannot drag, or who uses a keyboard on a narrow window, must still reach the full
height, so the grab bar is a button that switches between the two heights and says which one the
sheet is at. Closing stays with Escape, the closing button and a tap outside.

## D7: One sheet at a time; a sheet opened from a sheet replaces it

The issue asks for a second sheet opened from the first, with focus returned where it belongs. The
agreed design closes the first sheet and opens the second, then returns focus to the element the
developer names when the second closes, usually the first sheet's trigger. Stacking sheets would
put two modal dialogs and two backdrops on a phone screen with nothing to gain, so the rule is the
same everywhere: opening any sheet closes the open one.

## D8: A developer can open a sheet at full height

The agreed design has a tall sheet with a pinned head and a scrolling body for long content such
as a list to pick from. That is a sheet whose only useful height is full, which iOS expresses as a
sheet with only the large detent. It is an option, and the sheet can still be dragged down to its
resting height or closed, so the gestures behave the same on every sheet.

## D9: A trigger with an address falls back to a link

Without scripts, a `<dialog>` opens only through the newer invoker commands (`commandfor` with
`command="show-modal"`), which older browsers still in use lack. A link works everywhere. The agreed design's
trigger is a link to the item's own page that, where scripts run, opens the sheet instead. The
address is optional because some sheets, such as a setting, have no page of their own; such a
trigger is a button and needs scripts, which the documentation states.

## D10: Every way of closing changes nothing

The agreed design's sheets close without effect on Escape, a tap outside and a swipe down, and
show a closing button at the foot when the developer gives no buttons of their own. daisy-cotton's
modal closes from `type="button"` controls that call `close()` rather than a `method="dialog"`
form, so a sheet inside a form never submits it, and the sheet's own closing controls keep to
that.

## D11: Three stories

A developer building a sheet, a user working in one, and a user on a phone dragging one. Views, a
sheet opened from a sheet, the full-height option and the fallback link are settings and variants
of building one, so they are scenarios under the first story. The drag is its own story because it
was asked for in its own words and is something a user sets out to do: see more of the sheet, or
put it away.

## D12: The sheet is drawn in daisy-cotton's `c-modal`, not wrapped in `c-mvp.modal`

`c-mvp.modal` draws its own heading row from `title`, names the dialog with `aria-label`, and
places its actions in a row of its own. The sheet's head (grab bar, art, title, the line under
it) and foot replace all three, and the dialog is named by the sheet's own title so a description
can sit beside it. Both draw on the same thing, daisy-cotton's `c-modal` with daisyUI's modal box,
which is what FR-002 asks for. The `search` dialog already uses `c-modal` directly for the same
reason.

**ADR:** none. Local to this component.

## D13: The trigger, the menu and the open event are the public surface

FS-048 places the trigger and the menu in a sheet on touch screens, so both are components with
documented properties. Opening a sheet from anywhere is one window event, `mvp-sheet-open`, with
the sheet's `id` and optionally a `view` and the id of the element to return focus to. The trigger
uses it, and so can any other element a developer writes.

**ADR:** none. It follows from FR-003, FR-004 and FR-006.

## D14: No gesture library

A drag here is one pointer on the grab bar and the head, along one axis, settling at one of three
places. Pointer events with pointer capture do it in about a hundred lines. A library for it would
ship to every page, and the packages that do bottom sheets are framework components, not
something that attaches to a native `<dialog>`.

**ADR:** none.

## D15: The menu wraps `c-menu`

daisy-cotton's `c-menu` and `c-menu.item` render a link or a button with an icon and words. The
sheet's menu is `c-mvp.sheet.menu` (the list) and `c-mvp.sheet.menu.item` (a row), thin wrappers
that add the sheet's row height and a `danger` mark, so nothing a row renders is written twice.

**ADR:** none.

## D16: The gesture's numbers

- A release at 500 px/s or more is a flick, Material's `significantVelocityThreshold`.
- The resting height is the content's height up to half the screen, the iOS medium and Material
  half-expanded detents.
- The full height is the screen below a gap of 2.5rem plus the top safe area, so the page shows
  above it as it does above an iOS large detent.
- A release settles at the nearest of full, resting and closed, measured on the sheet's top edge;
  a drag past the resting height by more than a quarter of it counts as nearer closed.
- A fixed sheet follows a drag up by a quarter of the distance, capped at 1.5rem, and settles
  back.
- The settle is 250 ms with an ease-out curve and none under reduced motion.

None is pinned in the specification. They are named constants at the top of `sheet.js` and the
tests drive the sheet through them.

**ADR:** none.

## D17: The keyboard offset is read from `visualViewport`

On iOS and, since Chrome 108, on Android, the on-screen keyboard shrinks the visual viewport and
leaves the layout viewport alone, so a bottom-anchored box stays under it. While a sheet is open
it reads `window.visualViewport` and gives the box the difference as a bottom offset, and shrinks
its maximum height by it. This is the smallest thing that works in both and uses no API only one
engine has.

**ADR:** none.

## D18: Five templates and one script

`sheet`, `sheet.view`, `sheet.trigger`, `sheet.menu` and `sheet.menu.item` are templates; the
sheet's behaviour is one registered Alpine component, `mvpSheet`, in `assets/js/sheet.js`. A
trigger and a view are template markup using Alpine's own bindings and the window event, so they
need no component of their own.

**ADR:** none.
