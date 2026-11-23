# List rows with actions

A list row can offer its actions once and have them reached the way the device suits:
from a menu with a mouse and from a sheet on a touch screen. You write each action one
time, as a `c-mvp.list.row.action`, and the row draws it as an item of its menu.

## Write an action

```django
<c-mvp.list.row.action text="Rename" icon="edit"
                       href="{% url 'item-update' item.pk %}" />
<c-mvp.list.row.action text="Remove" icon="delete" danger leaves
                       hx-post="{% url 'item-delete' item.pk %}"
                       hx-target="closest [data-mvp-row]" hx-swap="outerHTML" />
```

An action is a link when it has an `href` and a button otherwise. It is built on
`c-mvp.sheet.menu.item`, so an `id`, a `form` or any `hx-*` attribute you give it lands
on that link or button, and appears once in the row.

### Properties of `c-mvp.list.row.action`

| Property | What it does |
| --- | --- |
| `text` | The action's words. Required |
| `icon` | The icon's name, drawn before the words |
| `href` | Link address. Without it the action is a button |
| `danger` | Marks the action as destructive |
| `main` | Marks the action a long swipe runs. At most one per row |
| `leaves` | Pressing it takes the row out of the list, so the row folds away |
| `label` | The action's accessible name, for when the words alone do not name the row, such as "Remove Quarterly report" |
| `type` | The button's type for an action without an `href`. Default `button` |
| `class` | Extra classes added to the link or button |

Every other attribute, and `:attrs`, reaches the link or button.

## Mark the main action

A long swipe runs one action without the person choosing it. Give that action `main`. When
a swipe goes past 60% of the row's width the face slides out and the main action runs, as
if its button had been pressed. A row with no main action has no long swipe: the swipe
resists past the buttons and settles open.

## Take the row out of the list

An action that removes its row from the list takes `leaves`. When it is pressed the row
folds away at once, before the answer arrives.

- If the action sends an htmx request and the request fails or times out, the row unfolds
  and is shown again, so the person can see the action did not happen.
- If the person declines an `hx-confirm` question, the row is not folded.
- If the request succeeds, your swap replaces or removes the row as you wrote it. Target
  the row itself with `hx-target="closest [data-mvp-row]"` and `hx-swap="outerHTML"`.
  `closest li` finds the action's own menu item, not the row.

The demo site's List row page (`components/list-row/`) has one action that succeeds and one
that fails, so both can be seen.

## One main action at most

A row has at most one action marked `main`. A row's actions pass through the
`single_main_action` filter, which returns them unchanged when they carry no more than
one main action and raises `ImproperlyConfigured` naming the row's `id` when they carry
two. It also raises when the row's `id` is empty.

```django
{% load mvp %}
{{ actions|single_main_action:row_id }}
```

## Write a row

`c-mvp.list.row` builds on `c-list.row`. Its content is the default slot and its
actions go in the `actions` slot.

```django
<c-mvp.list.row id="item-{{ item.pk }}" label="{{ item.name }}" lead="Edited yesterday">
  <div>{{ item.name }}</div>
  <c-slot name="actions">
    <c-mvp.list.row.action text="Open" icon="view" href="{{ item.get_absolute_url }}" main />
    <c-mvp.list.row.action text="Remove" icon="delete" danger leaves
                           hx-post="{% url 'item-delete' item.pk %}"
                           hx-target="closest [data-mvp-row]" hx-swap="outerHTML" />
  </c-slot>
</c-mvp.list.row>
```

With actions, the row draws its content with a "more" control at its end. The control is
a dropdown holding the menu for a mouse, and a button that opens the row's sheet,
`{id}-sheet`, for a touch screen. The menu is drawn once and moves between the two. A
page that runs no scripts shows the dropdown everywhere, so the menu stays reachable.

With no actions the row is a plain `c-list.row`: no menu control, no sheet and no script.

### Properties of `c-mvp.list.row`

| Property | What it does |
| --- | --- |
| `id` | Names the row's sheet and menu. Required when the row has actions |
| `label` | The row's name: the sheet's title and the control's accessible name, "More for" followed by the label |
| `lead` | The line under the sheet's title |
| `face_class` | Classes of the face, the part that holds the content |
| `class` | Extra classes added to the row |

Slots: the default slot is the row's content and `actions` holds the row's actions.

## Switch swiping off for a list

A page can stop the rows of one list from swiping while its menus keep working, for
instance while a modal tool is in use.

1. Find the list element, the element that holds the rows.
2. Call `mvpRows.off(list)`. Rows in that list stop moving under a finger or a
   trackpad, and a row that is open in it shuts. Each row's menu still offers every
   action.
3. Call `mvpRows.on(list)` to let the rows swipe again.

```js
const list = document.querySelector("#items");
mvpRows.off(list);
// later
mvpRows.on(list);
```

`off` writes `data-mvp-rows-off` on the list element and `on` removes it, so the same
attribute can be put in the markup of a list that should start switched off.

## Shut the open row

Call `mvpRows.shut()`. The row that stands open, if any, closes. Only one row is open at
a time.

## Rows that arrive by htmx

A row added by an htmx swap swipes and opens its menu with no further work: the row sets
itself up as it enters the page, whichever element the swap replaces.

## Swiping and reordering

A list built with `c-mvp.reorder` announces on its own element when reordering starts and
ends, with the window events `mvp:reorder-start` and `mvp:reorder-end`, which bubble. Rows
inside it follow the announcements with no work by you:

- When reordering starts, an open row in that list shuts, a swipe under way in it is let
  go, and its rows stop swiping.
- When reordering ends, they swipe again.

A list in the on-demand reorder mode also keeps its rows still for as long as the mode is
on, including across an answer that replaces the list. Your own code can raise the same
two events on any element holding rows to get the same behaviour.

### The script interface

| Name | What it does |
| --- | --- |
| `mvpRows.off(list)` | Stops the rows of `list` swiping and shuts an open row in it |
| `mvpRows.on(list)` | Lets the rows of `list` swipe again |
| `mvpRows.shut()` | Shuts the open row |

### Attributes the rows read and write

| Attribute | On | Meaning |
| --- | --- | --- |
| `data-mvp-rows-off` | A list element | Rows inside do not swipe. Written by `mvpRows.off` and removed by `mvpRows.on` |
| `data-mvp-rows-paused` | An element that announced a reorder start | Rows inside do not swipe until it announces the end. Written and removed by the rows |
| `data-reordering` | The root of an on-demand reorder list in its mode | Rows inside do not swipe |
| `data-mvp-row-action` | A link or button of a row's menu | Written by `c-mvp.list.row.action`. The swipe's buttons are built from the elements that carry it |
| `data-mvp-row-main` | An action | Written by `main`. A long swipe presses it |
| `data-mvp-row-leaves` | An action | Written by `leaves`. Pressing it folds the row |

A list element must not carry `data-mvp-rows-paused` in your markup: the rows own it.

## How a row is swiped

A row moves under a finger on a touch screen and under a two-finger sideways swipe on a
trackpad. It does not move under a mouse: a mouse reaches the actions from the menu.

- The row moves towards the start of the line, to the left on a left-to-right page and to
  the right on a right-to-left page. A swipe the other way moves it a few pixels and
  settles.
- A swipe past half the width of the buttons, or a quick flick, leaves the row open. A
  short one shuts it.
- Only one row is open at a time. A touch elsewhere, a scroll of the page, a tap on the
  open row and Escape shut it.
- A touch that starts within 20 pixels of the screen's edge is left to the browser, so
  the back gesture still works. A mostly vertical movement scrolls the page.
- The first time a person with a touch screen sees a list of rows, the first row opens a
  little and shuts, once, to show that it moves. Reduced motion makes the row jump
  instead of slide.

## Why the menu is the keyboard path

The swipe is a shortcut for the touch screen, not a second place to find the actions. The
buttons the swipe shows are built by script from the items of the row's menu, and pressing
one presses the item. This has three results.

- An action is written once, and its `id`, `form` and `hx-*` attributes appear once. No
  copy of an action can drift from the one that runs.
- The layer under the row is hidden from the keyboard and from assistive technology while
  the row is shut, so a keyboard user does not meet every action twice.
- A page whose script fails still has the whole menu, because the menu is drawn by the
  server.

A keyboard user reaches the actions through the more button at the row's end. It opens the
dropdown with a mouse or keyboard, and the sheet on a touch screen. Escape inside a row
shuts the row and returns focus to the first control of its content.
