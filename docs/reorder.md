# Reorder a list

A list a person can put in their own order needs two things: a way to move the
rows, and somewhere to keep the result. `<c-mvp.reorder>` gives the person the
rows to move, by dragging a handle or by pressing an up or a down button.
`mvp.ordering.save_order` takes the order your view received and writes it to a
position field.

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

The icons are named `chevron-up`, `chevron-down` and `drag`. The package ships
no icon set, so your icon configuration has to define them. The
[Icons](icons.md) page lists the packaged definitions.

Two lists on one page move independently. A row added to the list after the page
loaded, by a script or by an htmx swap of the list's contents, can be dragged and
has working buttons.

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
| `class`, other attributes | Pass to the root element. |

### `<c-mvp.reorder.row>`

One row. Its content is the row's title.

| Attribute | Meaning |
| --- | --- |
| `value` | The identifier of the item. |
| `label` | The item's name, used in the accessible names of the row's buttons and handle. |
| `class` | Extra classes on the row. |

Every row carries `data-mvp-reorder-row` and, when it has a value,
`data-mvp-reorder-value`. The buttons carry `data-mvp-reorder-up` and
`data-mvp-reorder-down`, and the handle carries `data-mvp-reorder-handle`.
The buttons and the handle stay hidden until scripts have run.

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
