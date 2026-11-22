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

## D3: A sheet that already shows everything does not grow

Material's sheets sized to their content (`fitToContents`) have no state taller than the content.
Growing a three-item menu to the top of the screen would show empty space and nothing more. The
sheet follows the finger a little, so the drag is felt, and settles back.

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
