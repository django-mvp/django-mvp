# Reorder a list

A list a person can put in their own order needs two things: a way to move the
rows, and somewhere to keep the result. `<c-mvp.reorder>` gives the person the
rows to move, by dragging a handle, by pressing an up or a down button or by
using the arrow keys on the handle.
`mvp.ordering.save_order` takes the order your view received and writes it to a
position field.

The demo site's Reorder page (`components/reorder/`) shows four working lists: a
row set, a list in a form, a list that posts as it changes and a list with an
on-demand mode.

## Make a list reorderable

Use this when a person should be able to put a list of items in their own order.

1. Draw the list with `<c-mvp.reorder>` and one `<c-mvp.reorder.row>` for each
   item. A row's `value` is the identifier of the item and its `label` names the
   item in the row's controls.

    ```html
    <c-mvp.reorder id="steps" label="Steps">
      {% for step in steps %}
        <c-mvp.reorder.row value="{{ step.pk }}" label="{{ step.title }}">
          {{ step.title }}
        </c-mvp.reorder.row>
      {% endfor %}
    </c-mvp.reorder>
    ```

2. Open the page. Each row shows its position number, its title, an up and a down
   button and a handle. Dragging a row by the handle moves it, and the rows it
   passes make room. Dragging from anywhere else on the row starts nothing,
   so a row can hold links and fields. The buttons swap a row with its neighbour.

## Move rows with a finger, the keyboard or a screen reader

A finger dragging a handle moves the row and the page does not scroll. A finger
dragging anywhere else on the row scrolls the page as usual. A second finger on a
handle, and a right click, start no drag. The start of a drag calls
`navigator.vibrate` on devices that have it. Holding a row near the top or the
bottom of the screen scrolls the page while the row stays under the pointer. A row
let go outside the list stays where the gap was.

Pressing Escape during a drag returns the row to where it started. Nothing is
posted and nothing is announced. The key does not reach an open dialog around
the list, so the dialog stays open.

A handle can be used from the keyboard. Tab reaches it, and while it has focus
the up and down arrows move its row one place, Home moves it to the top and End
to the bottom. A press that would move the row past an end does nothing. Focus
stays on the moved row's handle, and the same "Moved to position 2 of 3"
announcement follows each move. The handle is a button named "Drag" followed by
the row's `label`.

The up and down buttons are reached with Tab, and Enter or Space uses them. The
first row's up button and the last row's down button are marked
`aria-disabled="true"` and do nothing. Focus stays on the button that was used.
After each move a visually hidden `role="status"` region says "Moved to position
2 of 3", translated with the rest of the page. A list with one row, or none, shows
no handle and no buttons. Under `prefers-reduced-motion: reduce` the rows do not
slide.

The icons are named `chevron-up`, `chevron-down` and `drag`. The package ships
no icon set, so your icon configuration has to define them. The
[Icons](icons.md) page lists the packaged definitions.

Two lists on one page move independently. A row added to the list after the page
loaded, by a script or by an htmx swap of the list's contents, can be dragged and
has working buttons.

## Send the order to the server

A list with neither `form` nor `url` reorders on the page and sends nothing. It
suits a page that reads the rows itself. Pick one of the two destinations to keep
the result.

### Submit the order with a form

Use this when the list sits inside a form that has other fields too.

1. Put the list inside the form and add `form`. Give each row its `value`.

    ```html
    <form method="post">
      {% csrf_token %}
      <c-mvp.reorder id="steps" label="Steps" form name="order">
        {% for step in steps %}
          <c-mvp.reorder.row value="{{ step.pk }}" label="{{ step.title }}">
            {{ step.title }}
          </c-mvp.reorder.row>
        {% endfor %}
      </c-mvp.reorder>
      <button type="submit">Save</button>
    </form>
    ```

2. In the view, read `request.POST.getlist("order")`. The identifiers arrive in
   the order the rows had when the form was sent, because each row holds a hidden
   input that moves with it. Pass them to [`save_order`](#save-a-received-order).

The field is named by `name`, which defaults to `order`. The input takes its
name when the script runs, so a form sent without scripts carries no order.

### Post the order to an address

Use this when each move should be stored at once.

1. Add `url`, and an `id` that is unique on the page. Do not render the list
   with `only`, because the CSRF token comes from the surrounding context.

    ```html
    <c-mvp.reorder id="steps" label="Steps" url="{% url 'step-order' project.pk %}">
      ...
    </c-mvp.reorder>
    ```

2. Write the view that receives the post. The order arrives in the field named by
   `name`. Answer with the list drawn again, with the same `id`, because the
   answer replaces the list.

    ```python
    @require_POST
    def step_order(request, project_id):
        steps = Step.objects.filter(
            project_id=project_id, project__owner=request.user
        )
        try:
            save_order(steps, request.POST.getlist("order"))
        except InvalidOrder:
            return HttpResponseBadRequest()
        return render(request, "steps/list.html", {"steps": steps.all()})
    ```

A move that leaves the rows as they were posts nothing. The up and down buttons
get ids built from the list's `id` and the row's `value`, so focus returns to the
button that was used after the answer arrives.

## Leave out the up and down buttons

Use this when the rows are moved by dragging and from the handle's arrow keys, and
the buttons would only crowd the row. Add `hide_buttons` to the list:

```html
<c-mvp.reorder id="steps" label="Steps" hide_buttons>
  ...
</c-mvp.reorder>
```

The rows keep their handles and their position numbers. A list without
`hide_buttons` draws the buttons as before. The demo site's Reorder page shows a
list without buttons.

## Reorder only on request

Use this when a list is read most of the time and a person should move rows
only after pressing an Edit control.

1. Set `mode="on-demand"` on the list and give it an `id`. Until the mode
   starts, the list shows no handles and no buttons and cannot be dragged.

    ```html
    <c-mvp.reorder id="steps" label="Steps" mode="on-demand" url="{% url 'step-order' project.pk %}">
      ...
    </c-mvp.reorder>
    ```

2. Place a control that starts the mode, and one that ends it, anywhere on the
   page, for example in the page's actions. Each names the list's `id` in its
   `data-mvp-reorder-start` or `data-mvp-reorder-end` attribute.

    ```html
    <c-mvp.page.title title="Steps">
      <c-slot name="actions">
        <button type="button" class="btn" data-mvp-reorder-start="steps">Edit order</button>
        <button type="button" class="btn btn-primary" data-mvp-reorder-end="steps">Done</button>
      </c-slot>
    </c-mvp.page.title>
    ```

3. Press the start control. The handles and the buttons appear and the list's
   root carries `data-reordering`, which your CSS can use. The end control, or
   Escape, ends the mode and they go again.

A control placed anywhere on the page works for any list with that `id`,
including one the server draws again after a post. Escape does not end the mode
while a drag is under way, where it cancels the drag, and does not end it for a
list inside an open dialog, where the dialog takes the key.

## Listen for a list being reordered

Use this when something else on the page should react while a list is being
moved, for example to pause a refresh or to dim a panel.

1. Listen on the list or on any element around it. The list's root dispatches
   `mvp:reorder-start` and `mvp:reorder-end`, and both bubble.

    ```js
    document.addEventListener("mvp:reorder-start", (event) => {
      document.body.classList.add("is-reordering");
      console.log(`${event.target.id} started, by ${event.detail.source}`);
    });

    document.addEventListener("mvp:reorder-end", (event) => {
      document.body.classList.remove("is-reordering");
    });
    ```

2. Read `event.detail.source`, which tells the three kinds of move apart.

| `detail.source` | Fired |
| --- | --- |
| `drag` | Around one drag: the start when the row is picked up, the end after it is dropped or cancelled. |
| `button` | Around one use of an up or a down button. A button that does nothing fires nothing. |
| `mode` | Once around the whole mode of an `on-demand` list. Drags and button moves inside the mode fire their own pairs. |

The start arrives before the rows change and the end after they have changed.
The server's answer replacing a list is not a move and fires nothing, and the
mode carries over to the list that replaces it.

## When a post fails

A list with a `url` shows the order the server last drew. When the server
answers with an error status, or the request cannot be sent, the rows go back to
that order, a visible message says the change was not saved, and the same
sentence is announced to a screen reader. The message stays until the next move.

A new move, or the start of a drag, drops a post still in flight. The latest
order is the one shown and sent, and a late answer for an older order is
ignored. A drag that ends where it began sends the current order again.

## Reorder inside a dialog

Use this when a person moves rows in a dialog and either confirms the change or
walks away from it.

1. Put the list, with `form`, inside a form inside the `dialog`, with a button
   that submits the form.

    ```html
    <dialog id="steps-dialog">
      <form method="dialog">
        <c-mvp.reorder id="steps" label="Steps" form name="order">
          ...
        </c-mvp.reorder>
        <button type="submit">Confirm</button>
        <button type="button" onclick="this.closest('dialog').close()">Cancel</button>
      </form>
    </dialog>
    ```

2. Close the dialog with the cancel button, with Escape or by any other means
   than submitting the form. The rows go back to the order they had when the
   dialog opened. Submitting the form keeps the new order, and the next time
   the dialog is closed without submitting, the list returns to that order.

A list with `mode="on-demand"` inside a dialog ends its mode when the dialog
closes. Escape closes the dialog and is not taken by the list, except during a
drag, where it cancels the drag and leaves the dialog open.

## Use the list without scripts

A page loaded with JavaScript switched off shows each list in its saved order,
with no handle and no up or down button, because the controls stay hidden until
the script has run. Nothing can be dragged, and a list with `form` sends no
order.

A row set built with `can_order` shows the typed `ORDER` field of each row
instead. Type the numbers, submit the form, and the server reads the rows in
that order through the formset's `ordered_forms`.

## Save a received order

Use this when a request arrives carrying the identifiers of a list's records in
the order the person left them.

1. Give the model an integer field to hold the position, and order by it.

    ```python
    # models.py
    class Task(models.Model):
        project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
        title = models.CharField(max_length=200)
        position = models.PositiveIntegerField(default=0)

        class Meta:
            ordering = ["position", "pk"]
    ```

2. In the view that receives the order, build the queryset of records the
   current user may reorder, and pass it with the identifiers.

    ```python
    # views.py
    from django.http import HttpResponse, HttpResponseBadRequest
    from django.views.decorators.http import require_POST

    from mvp.ordering import InvalidOrder, save_order


    @require_POST
    def save_task_order(request, project_id):
        tasks = Task.objects.filter(project_id=project_id, project__owner=request.user)
        try:
            save_order(tasks, request.POST.getlist("order"))
        except InvalidOrder:
            return HttpResponseBadRequest()
        return HttpResponse(status=204)
    ```

3. Check the result: the records now read `0, 1, 2, ...` in the order sent, and
   records outside the queryset are unchanged.

The queryset is the access rule. Only its records can be named, and only they
are written, so filter it to what the current user may change.

## Reference

### `<c-mvp.reorder>`

The list. It draws an ordered list inside a root element that carries the
script.

| Attribute | Meaning |
| --- | --- |
| `id` | The list's id. |
| `label` | The list's accessible name. |
| `name` | The field name that carries the order. Defaults to `order`. |
| `form` | Each row's identifier is submitted by the surrounding form under `name`. |
| `url` | An address the order is posted to on every change. Needs an `id`. |
| `hide_buttons` | Draw no up and down buttons. The handle still moves its row, by dragging and from the keyboard. |
| `mode` | `always` (the default) or `on-demand`. An `on-demand` list needs an `id`. |
| `class`, other attributes | Pass to the root element. |

### `<c-mvp.reorder.row>`

One row. Its content is the row's title.

| Attribute | Meaning |
| --- | --- |
| `value` | The identifier of the item. |
| `label` | The item's name, used in the accessible names of the row's buttons and handle. |
| `class` | Extra classes on the row. |

A list's root dispatches `mvp:reorder-start` and `mvp:reorder-end`, and
carries `data-reordering` during the mode of an `on-demand` list. An element
with `data-mvp-reorder-start="<id>"` or `data-mvp-reorder-end="<id>"` starts or
ends that list's mode when clicked.

Every row carries `data-mvp-reorder-row` and, when it has a value,
`data-mvp-reorder-value`. The buttons carry `data-mvp-reorder-up` and
`data-mvp-reorder-down`, and the handle carries `data-mvp-reorder-handle`.
The buttons and the handle stay hidden until scripts have run. A list with
`hide_buttons` carries `data-mvp-reorder-hide-buttons` on its root.

### `mvp.ordering.save_order(queryset, ids, *, field="position")`

Numbers the queryset's records `0, 1, 2, ...` in the order of `ids`, in one
database transaction, and returns the records in that order.

| Argument | Meaning |
| --- | --- |
| `queryset` | The records the order covers. Records outside it are never read or written. |
| `ids` | The primary keys in their new order. Each is converted with the primary key field's `to_python`, so strings from a request are accepted. |
| `field` | The integer field that receives the numbers. Defaults to `"position"`. |

The order is refused whole, and nothing is saved, when it:

- names a record more than once,
- names a record that is not in the queryset,
- leaves out a record of the queryset,
- contains an identifier the primary key cannot convert.

### `mvp.ordering.InvalidOrder`

A subclass of `ValueError`, raised by `save_order` for each refusal above.
