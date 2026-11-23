# ADR 0046 — A row's actions are declared once and drawn as its menu

**Status:** accepted

## Decision

A developer writes each action of a list row once, as a `c-mvp.list.row.action`. The row draws it once, as an item of its menu. The row's script builds the swipe's buttons from those items, and pressing a button presses the item. No `id`, `form` or `hx-*` attribute is ever drawn twice.

The one menu moves between two places: it sits in the dropdown's panel where the page is served, and the script moves it into the row's sheet when the sheet opens, then back when it closes. A page whose script does not run keeps the whole menu in the dropdown.

The layer under the row is hidden from the keyboard and from assistive technology while the row is shut, so the menu is the way a keyboard user reaches the actions.

## Why

Drawing the actions twice, once as the swipe's buttons and once as the menu, would mean an `id` or a form hook given to one copy and not the other. Which action ran would then depend on which copy a person reached, and every change to an action would have to be made in two places.

Building the buttons from the menu's items makes the menu the single source. It is drawn by the server, so it is present before any script runs and stays present when a script fails. The swipe is an addition to it for the touch screen, never a second place to find the actions.

## Revisit if

An action needs a different face as a swipe button than as a menu item, such as its own colour or its own words, which the items cannot carry.
