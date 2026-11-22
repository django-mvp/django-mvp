# Reorder a list

A list a person can put in their own order needs two things: a way to move the
rows, and somewhere to keep the result. This page covers keeping the result.
`mvp.ordering.save_order` takes the order your view received and writes it to a
position field.

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
