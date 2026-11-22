# Decisions: Swipe and menu actions on list rows

Rationale for the ambiguities settled while writing the specification, each resolved from the
issue, its sibling feature requests and the agreed design. How the feature is built is not
settled here: that is research and planning, with the notes in `planning-notes.md`.

## D1: A finger and a trackpad swipe, a mouse does not

The issue puts swiping on a phone and the ⋯ menu with a mouse. Dragging a row with a mouse is
what a text selection or a link drag already does, so it would fight the browser. A trackpad's
two-finger sideways swipe is the gesture laptops use for the same job in mail clients, and it
cannot be confused with a selection, so it moves the row too.

## D2: One direction, towards the start of the line

Mail and music apps on both phone platforms reveal row actions from the end edge. A second
direction would need a second set of actions per row, which the issue does not ask for. The
direction mirrors on a right-to-left page, because the actions sit at the end of the line.

## D3: Keyboard users reach actions through the ⋯ menu

The issue asks that a keyboard user reach every action. The menu holds every action already, so
leaving the actions under a closed row in the tab order would make a keyboard user pass every
action twice per row. They are taken out of the tab order and out of the accessibility tree
while the row is closed, and the menu is the keyboard path.

## D4: The primary pointer picks dropdown or sheet

A laptop with a touch screen has both pointers. Following the primary pointer, the one CSS media
queries report as `pointer`, gives one predictable answer per device and is what the issue's
"a dropdown with a mouse and a sheet on a touch screen" describes.

## D5: At most one main action, and none is allowed

The issue's long swipe runs "the main one". Some rows have no action safe to run in one
movement, so a row may have none, and then a long swipe opens it and stops. Two main actions has
no meaning, so the developer is told rather than one being picked silently.

## D6: An action that takes the row out folds it at once, and a failure puts it back

The issue asks that an action failing on the server put the row back. Folding the row as the
request is sent, rather than after the answer, is what makes a swipe feel immediate. The
failure path then restores it. This applies to htmx requests, which are the requests the page
can observe failing. A full-page form or link leaves the page, so there is nothing to restore.

## D7: Swiping can be switched off for one list, from one script interface

The reorder feature (https://github.com/django-mvp/django-mvp/issues/689) drags rows by a handle,
and a row that opened under that drag would break it. It needs swiping off for the list being
reordered and any open row shut. That is a developer-facing interface, so it is one named,
documented script object that the reorder feature uses too, rather than a private hook each
feature finds for itself.

## D8: The 60% point and the 20-pixel edges are specified

These two numbers decide what a gesture does, not how anything looks, and they are what the
agreed design was approved with. 60% is far enough that a partial swipe never runs the main
action by accident, and 20 CSS pixels keeps clear of the back-gesture area on both phone
platforms. They are in the requirements so the build does not choose different ones.

## D9: The row is a "list row"

`CONTEXT.md` already uses *row* for a formset's related row. This feature's row is called a
*list row* throughout, with *row action*, *main action* and *row menu* as its new terms. They are
added to `CONTEXT.md` when the feature is built.

## D10: The menu is drawn once per row

A menu drawn twice, once as a dropdown and once as a sheet with one hidden, puts every id and
form hook on the page twice: a label points at the wrong control and a script finds the hidden
copy. The requirement is that each id appears once. How the one menu becomes a dropdown or a
sheet is for planning.
