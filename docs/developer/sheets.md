# Sheets

A sheet is a dialog that rises from the foot of a phone's screen and is centred from
the `sm` breakpoint (640 px) up. It holds a menu of actions, a short form or a few
steps, and closes without changing anything when the person presses Escape, taps
outside it, drags it down or, on a wide screen, uses the close button at the right of its head. The component demo's sheet page shows each
example below running.

A sheet is four components:

| Component | What it is |
| --- | --- |
| `c-mvp.sheet` | The dialog: grab bar, head, body and foot |
| `c-mvp.sheet.view` | One panel of a sheet that has several steps |
| `c-mvp.sheet.trigger` | The button or link that opens a sheet |
| `c-mvp.sheet.menu` | The list of actions in a sheet |

## Open a sheet from a button

1. Draw the sheet with an `id` and a `title`.
2. Draw a trigger whose `for` is that id.

    ```django
    <c-mvp.sheet.trigger for="item_sheet" href="{% url 'item-detail' item.pk %}"
                         label="{{ item.name }}" />
    <c-mvp.sheet id="item_sheet" title="{{ item.name }}" lead="Edited yesterday">
      <c-mvp.sheet.menu>
        <c-menu.item text="Rename" icon="edit"
                   href="{% url 'item-update' item.pk %}" />
        <c-menu.item text="Delete" icon="trash" class="text-error"
                   href="{% url 'item-delete' item.pk %}" />
      </c-mvp.sheet.menu>
    </c-mvp.sheet>
    ```

3. Give the trigger an `href`. It is the page that offers the same actions, and the
   browser follows it where scripts do not run or the sheet is not on the page. A
   trigger with no `href` is a button and needs scripts: with none it does nothing.

A trigger with nothing between its tags is an icon-only button named "More for" and
its `label`. Words between its tags are the button's words, and `label` is added to
its accessible name.

A sheet's `title` is required. It is the dialog's accessible name, so a sheet
without one is announced as an unnamed dialog.

## Open a sheet from any element

A trigger is one way to send the event a sheet listens for. Any element opens a
sheet by dispatching `mvp-sheet-open` on the window with the sheet's id:

```django
<button type="button" x-data
        @click="$dispatch('mvp-sheet-open', { id: 'item_sheet', view: 'confirm' })">
  Delete
</button>
```

The event's `detail` takes three keys:

| Key | Meaning |
| --- | --- |
| `id` | The id of the sheet to open. Required. |
| `view` | The name of the view to open at. A name the sheet does not have opens its first view. |
| `returns` | The id of the element focus returns to when the sheet closes. |

Opening a sheet closes any other sheet that is open, so only one is ever showing.

## Move between steps

1. Put each step in a `c-mvp.sheet.view` with a `name`. Only the view whose name is
   current shows; the first shows when the sheet opens, and every opening starts
   there again.
2. Switch from any element inside the sheet with `show(name)`.

    ```django
    <c-mvp.sheet id="item_sheet" title="Project plan">
      <c-mvp.sheet.view name="menu">
        <c-mvp.sheet.menu>
          <c-menu.item text="Delete" icon="trash" class="text-error"
                                 @click="show('confirm')" />
        </c-mvp.sheet.menu>
      </c-mvp.sheet.view>
      <c-mvp.sheet.view name="confirm">
        <button type="button" @click="show('menu')">Keep it</button>
      </c-mvp.sheet.view>
    </c-mvp.sheet>
    ```

3. Open a sheet at a step other than the first by giving the trigger a `view`.

## Open a sheet from inside another sheet

Put a trigger inside the first sheet. It opens the second sheet and closes the first.
When the second sheet closes, focus goes to:

- the element named in the trigger's `returns`, if there is one;
- otherwise the element that opened the first sheet, because the trigger inside the
  first sheet is no longer showing and cannot take focus. A sheet opened by dispatching
  the event counts as opened by the element that had focus at that moment;
- for a trigger outside every sheet, the trigger itself.

## Choose a height

A sheet on a phone has two heights. The resting height is as tall as its content,
up to half the screen. The full height is the screen less a strip at the top, so the
page behind stays in view.

| Property | Effect |
| --- | --- |
| none | Opens at the resting height. A person can drag it taller or tap the grab bar. |
| `full` | Opens at the full height. A person can drag it shorter. |
| `fixed` | Stays at the resting height. It follows a drag up a little and settles back. |

On a phone, the grab bar at the top of the sheet:

- is a button that switches between the two heights, and says which one it is at to
  assistive technology (on a `fixed` sheet it is hidden from assistive technology and is
  not a button);
- can be dragged, as can the head, and so can a flick: a drag up makes the sheet
  taller, and a drag down makes it shorter and then closes it;
- offers no change of height on a `fixed` sheet, though dragging it down still closes it.

From 640 px wide the dialog is centred with no grab bar, ignores drags and keeps its
own height. `wide` gives that centred dialog the wide size.

While the on-screen keyboard is showing, the sheet lifts clear of it. People who
prefer reduced motion get no slide.

## Properties

### `c-mvp.sheet`

| Property | Meaning |
| --- | --- |
| `id` | The sheet's id, unique on the page. Required. A trigger names it in `for`. |
| `title` | What the sheet is about, shown in its head. Required. |
| `lead` | The line under the title. |
| `icon` | An icon's name, drawn before the title. |
| `full` | Open at the full height. |
| `fixed` | Keep the resting height. |
| `wide` | Give the centred dialog the wide size. |
| `class` | Extra classes added to the dialog. |

Its slots are the default slot, which is the body and scrolls under a pinned head;
`art`, small art drawn before the title and hidden from assistive technology;
`description`, text that becomes the dialog's accessible description; and `actions`,
the buttons in the foot. The foot is empty without them. A phone closes the sheet by the grab bar, dragging down, tapping outside or Escape, and a wide screen by the close button, an icon named "Close" in the head, so there is no worded Close button. A button in
`actions` that only closes the sheet has `type="button"`, so a sheet can sit inside a
form without submitting it.

### `c-mvp.sheet.view`

| Property | Meaning |
| --- | --- |
| `name` | The view's name. Required. |

### `c-mvp.sheet.trigger`

| Property | Meaning |
| --- | --- |
| `for` | The id of the sheet it opens. Required. |
| `href` | The page that offers the same actions, followed when the sheet cannot open. |
| `label` | What the item is called. |
| `view` | The name of the view to open at. |
| `returns` | The id of the element focus returns to. |
| `icon` | The icon of the icon-only button. Defaults to `more`. |
| `id` | The trigger's own id, so focus can return to it. |
| `class` | Extra classes added to the link or button. |

A click with Ctrl, Cmd or Shift held, or with a button other than the primary one, is
left to the browser, so a link can still open in a new tab.

### `c-mvp.sheet.menu`

`c-mvp.sheet.menu` takes `class`. It draws a large daisyUI menu (`menu-lg`) that fills the
width of the sheet, and its rows are daisy-cotton's `c-menu.item`, which takes `text`,
`icon`, `href` (a link; without it a button), `type` and `class`. Attributes the item does
not list, such as `@click`, land on the link or button. A destructive row is last and has
`class="text-error"`.

## Why a sheet's title is required

A sheet is a modal dialog, and a person using a screen reader hears its title when
focus moves into it. Without a title the dialog has no name and nothing says what it
is for. Leaving it out is the same mistake as an image with no `alt`.

## Why a trigger has an address

A trigger with an `href` is a real link before any script runs. A search engine can
follow it, a person who opens the link in a new tab gets the page that offers the same
actions, and the sheet is an improvement over that page, not the only way in.
