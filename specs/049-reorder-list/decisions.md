# Decisions: Reorder a list by dragging

Every place the issue is silent, settled while writing the specification from the issue and the
agreed design. How the feature is built is not settled here: that is research and planning, with
the notes in `planning-notes.md`.

## Reading of the issue

A developer makes a list reorderable and chooses where its order goes. A person then reorders it
by dragging a row's handle, or with up and down buttons, from a mouse, a finger or a keyboard.
Swiping rows for their actions and the sheet a list may sit in belong to
https://github.com/django-mvp/django-mvp/issues/688 and
https://github.com/django-mvp/django-mvp/issues/687. This feature uses the first and may sit in
the second, and builds neither.

## D1: An order goes to one of three places

The issue names two: "saved with the form or sent to the server as the list changes". Saved with
a form splits in two, because a row set already carries `ORDER` fields that Django reads back,
while a plain list of records inside a form has no field until the developer names one. So a row
set fills its `ORDER` fields, any other list in a form sends the rows' identifiers in order under
a name the developer chooses, and a list outside a form posts that same order to an address each
time it changes. Each list uses one of the three.

**ADR:** none, the three destinations are documented in docs/reorder.md and nothing downstream inherits the split


## D2: The package saves an order to a position field

The issue says many models carry a position field. Without a helper every project writes the
same renumbering, and the same check that nobody reorders records they may not touch. The helper
takes the received order and the records the person may reorder, and refuses the whole order if
it names a record outside them or leaves one out. Refusing rather than saving the valid part
keeps a stale page from scrambling the list. Who may reorder what stays the developer's decision,
expressed by the records they pass.

**ADR:** none, a helper's contract is documented in docs/reorder.md


## D3: Always reorderable in a form, a reorder mode otherwise

The agreed design has both: a list in a form, or a dialog with Confirm and Cancel, that is
reorderable whenever it is shown, and a list read most of the time that offers a reorder mode,
started from a control and ended by a second control or Escape, as phone apps do for an edit
mode. The developer chooses per list. The control is the developer's to place, because the package
provides components and the host places them.

**ADR:** none, a per-list choice documented in docs/reorder.md


## D4: Reordering announces its start and end, and other behaviour pauses itself

A row that can both be swiped and dragged would answer one gesture two ways. Rather than reach
into another feature to turn its swiping off, the list announces on itself, as documented events,
when reordering starts and when it ends. Swiping rows for their actions
(https://github.com/django-mvp/django-mvp/issues/688) listens for them, turns swiping off and
shuts any open row: that side is delivered there. So this feature depends on no other and can be
built alongside it, and any later behaviour on a row can pause the same way.

**ADR:** docs/adr/0045-reordering-announces-its-start-and-end-on-the-list.md


## D5: A refused order is undone and the person is told

A list that posts as it changes shows a move before the server has accepted it. If the server
refuses or cannot be reached, leaving the row where it was dropped would show an order that was
not saved. The list returns to its order before that move and says the change was not saved.

**ADR:** none, local to the posting list


## D6: Vertical lists, one list at a time

Neither the issue nor the agreed design moves rows between lists, nests them, or lays them out as
a grid. Each would need its own rules for where a row may land. They are left out until a project
asks for one.

**ADR:** none, a scope boundary recorded in the specification


## D7: Without scripts, the saved order is shown

Dragging and the up and down buttons need scripts. Without them a list shows its rows in their
saved order, and a row set keeps its `ORDER` number fields, which is what Django renders today,
so the order can still be set by typing. A list that posts as it changes offers nothing to
reorder without scripts.

**ADR:** none, follows from what Django already renders


## D8: Up and down buttons on every row, and an announced position

The issue asks for buttons "for anyone who cannot drag". Each row carries both, the impossible
move is not usable (up on the first row, down on the last), focus stays with the row that moved,
and its new position is announced, so a keyboard or screen reader user can follow what happened.

**ADR:** none, local to the row controls


## D9: Reduced motion is respected

Rows that slide into place are motion a person may have asked their system to avoid. With
reduced motion requested, rows take their new places without animation.

**ADR:** none, a browser setting honoured


## Design review of the plan

One review round. Every finding but one was applied as the plan's "Corrections from the design
review". Not adopted: merging the ADR task into the row set's layout task, because the ledger
already holds the task rows and the merge saves nothing. All other notes were sweeps of wording.
**ADR:** none, local to this feature.

## D10: A reorder mode ends with the dialog that holds it

An earlier test pinned that Escape inside an open dialog closed the dialog and left the reorder
mode on. A list in a dialog that is closed without submitting returns to its order from when the
dialog opened, so a mode left on would show handles on a list the person has abandoned. The mode
now ends when the dialog closes, and the test was rewritten to assert that. It was written in this
same feature and replaced because the requirement it pinned was wrong, not weakened to pass.
**ADR:** none, local to this feature.
