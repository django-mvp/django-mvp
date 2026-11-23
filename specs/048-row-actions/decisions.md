# Decisions: Swipe and menu actions on list rows

Rationale for the ambiguities settled while writing the specification, each resolved from the
issue, its sibling feature requests and the agreed design. How the feature is built is not
settled here: that is research and planning, with the notes in `planning-notes.md`.

## D1: A finger and a trackpad swipe, a mouse does not

The issue puts swiping on a phone and the ⋯ menu with a mouse. Dragging a row with a mouse is
what a text selection or a link drag already does, so it would fight the browser. A trackpad's
two-finger sideways swipe is the gesture laptops use for the same job in mail clients, and it
cannot be confused with a selection, so it moves the row too.

**ADR:** none — local to this feature, nothing downstream inherits it

## D2: One direction, towards the start of the line

Mail and music apps on both phone platforms reveal row actions from the end edge. A second
direction would need a second set of actions per row, which the issue does not ask for. The
direction mirrors on a right-to-left page, because the actions sit at the end of the line.

**ADR:** none — local to this feature, nothing downstream inherits it

## D3: Keyboard users reach actions through the ⋯ menu

The issue asks that a keyboard user reach every action. The menu holds every action already, so
leaving the actions under a closed row in the tab order would make a keyboard user pass every
action twice per row. They are taken out of the tab order and out of the accessibility tree
while the row is closed, and the menu is the keyboard path.

**ADR:** none — local to this feature, nothing downstream inherits it

## D4: The primary pointer picks dropdown or sheet

A laptop with a touch screen has both pointers. Following the primary pointer, the one CSS media
queries report as `pointer`, gives one predictable answer per device and is what the issue's
"a dropdown with a mouse and a sheet on a touch screen" describes.

**ADR:** none — local to this feature, nothing downstream inherits it

## D5: At most one main action, and none is allowed

The issue's long swipe runs "the main one". Some rows have no action safe to run in one
movement, so a row may have none, and then a long swipe opens it and stops. Two main actions has
no meaning, so the developer is told rather than one being picked silently.

**ADR:** none — local to this feature, nothing downstream inherits it

## D6: An action that takes the row out folds it at once, and a failure puts it back

The issue asks that an action failing on the server put the row back. Folding the row as the
request is sent, rather than after the answer, is what makes a swipe feel immediate. The
failure path then restores it. This applies to htmx requests, which are the requests the page
can observe failing. A full-page form or link leaves the page, so there is nothing to restore.

**ADR:** none — local to this feature, nothing downstream inherits it

## D7: Swiping can be switched off for one list, from one script interface

The reorder feature (https://github.com/django-mvp/django-mvp/issues/689) drags rows by a handle,
and a row that opened under that drag would break it. It needs swiping off for the list being
reordered and any open row shut. The reorder feature announces on the list's element
when reordering starts and ends, and this feature answers those announcements itself: it shuts
the open row and switches swiping off, then back on. That keeps the swipe's behaviour in the
feature that owns the swipe and leaves neither feature waiting on the other. A developer's own
script switches swiping off and shuts a row through one named, documented script object.

**ADR:** docs/adr/0045-reordering-announces-its-start-and-end-on-the-list.md

## D8: The 60% point and the 20-pixel edges are specified

These two numbers decide what a gesture does, not how anything looks, and they are what the
agreed design was approved with. 60% is far enough that a partial swipe never runs the main
action by accident, and 20 CSS pixels keeps clear of the back-gesture area on both phone
platforms. They are in the requirements so the build does not choose different ones.

**ADR:** none — two numbers local to this feature, nothing downstream inherits them

## D9: The row is a "list row"

`CONTEXT.md` already uses *row* for a formset's related row. This feature's row is called a
*list row* throughout, with *row action*, *main action* and *row menu* as its new terms. They are
added to `CONTEXT.md` when the feature is built.

**ADR:** none — vocabulary, recorded in CONTEXT.md

## D10: The menu is drawn once per row

A menu drawn twice, once as a dropdown and once as a sheet with one hidden, puts every id and
form hook on the page twice: a label points at the wrong control and a script finds the hidden
copy. The requirement is that each id appears once. How the one menu becomes a dropdown or a
sheet is for planning.

**ADR:** docs/adr/0046-a-rows-actions-are-declared-once-and-drawn-as-its-menu.md

## D11: The actions are drawn once, as the menu. The swipe's buttons are built from them

A developer declares each action once. The template draws it once, as a menu item, and the row's
script builds the swipe's buttons from those items and presses the item when a button is pressed.
No id, form hook or htmx attribute is ever duplicated, and a page whose script fails keeps the
whole menu. Drawing the actions twice and giving the id to one copy would make an id depend on
which copy a script reads.

**ADR:** docs/adr/0046-a-rows-actions-are-declared-once-and-drawn-as-its-menu.md

## D12: The one menu moves between the dropdown and the sheet

The dropdown's panel holds the menu where the page is served. When the sheet opens, the script
moves that one list into the sheet and moves it back when the sheet closes. A page with no script
opens the dropdown on every device. The pointer decides which control is shown, in CSS.

**ADR:** none — covered by D11's ADR, which states the whole arrangement

## D13: A second main action is a template error

A template cannot raise, so one small filter counts the main marks in the rendered actions and
raises `ImproperlyConfigured` naming the row. A system check cannot see rendered rows and a
console message is missed.

**ADR:** none — local to this feature, nothing downstream inherits it

## D14: The row pauses by state on the announcing list, never by a shared count

A drag and a button move each fire a start and an end, and a reorder mode fires one pair around
the whole mode. A single flag would switch swiping back on at the end of the first drag inside a
mode. A list replaced during a mode hands the mode on without a new start, so a count kept across
elements would never come back down. The row therefore pauses on the list's own state: it is off
while the list carries the reordering state or a pause written for the announcing element, and the
developer's own off switch is a separate attribute that the announcements never touch.

**ADR:** none — local to this feature, nothing downstream inherits it

## D15: One global, `mvpRows`

The developer's script switches swiping off and shuts a row through `window.mvpRows`. It is the
only name the script writes to the page. The reorder announcements are answered by the row itself,
so no other code needs to find it.

**ADR:** none — local to this feature, nothing downstream inherits it
