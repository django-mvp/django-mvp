# ADR 0007 — A row set is declared as its own class, named after Django's admin inlines

**Status:** accepted

**Supersedes:** [ADR 0002](0002-formset-rendering-is-generic-the-configured-view-is-not.md), in the
half that limited the configured view to one related set. The other half of 0002 — that rendering
is generic and no configured view is packaged for a standalone formset — still holds.

## Decision

A related set is configured by a declaration class, and a view lists as many of them as it needs:

```python
class OrderLineInline(InlineFormSet):
    model = OrderLine            # the related model
    fields = ["quantity", "unit_price"]
    extra = 2


class OrderUpdateView(MVPInlineUpdateView):
    model = Order
    fields = ["reference", "customer"]
    inlines = [OrderLineInline, ShippingAddressInline]
```

The names come from `django.contrib.admin`. `model` is the related model and keeps that meaning for
the object's whole life. `extra`, `min_num`, `max_num`, `can_delete` and `fk_name` are admin's
attribute names, which are also `inlineformset_factory`'s parameter names, so they agree twice
over. `form` and `formset` name the form class and the base formset class, again as admin does.
Two attributes have no admin equivalent and keep their own names: `title`, the heading rendered
above the set, and `description`, the help text beneath it. `title` defaults to the related model's
`verbose_name_plural`, so a set you say nothing about is headed the way admin would head it.

Configuration that no attribute covers goes in one of two dictionaries, split by the stage it
reaches: `factory_kwargs` shape the generated formset class, `formset_kwargs` shape the instance.
Where an attribute and a dictionary key set the same thing, the dictionary wins. Anything decided
per request is reached by overriding the method that assembles the group.

Two hooks on the declaration go further than configuration:

- `get_form_kwargs(index)` gives each form in the set its own keyword arguments. It takes Django's
  signature, so `index` identifies the form and is `None` for the blank template form the browser
  clones to add a row.
- `sort_forms(forms)` decides the order forms are displayed in. It affects display only and never
  the order rows are validated or saved in.

Each set gets its own prefix, defaulting to the one Django derives from the relation. Two
declarations that resolve to the same prefix raise `ImproperlyConfigured` when the page is built.

`can_order` is deliberately absent. It is a different feature — a field on every form so a person
can reorder rows — and nothing needs it yet. It remains reachable through `factory_kwargs`.

## Why

Configuration had lived in six `inline_*` attributes on the view, which allowed exactly one related
set because there was nowhere for a second set's values to go. Moving it onto an object per set is
what makes more than one possible at all, and it is the same move Django admin made for the same
reason.

The names are Django's rather than invented because that is the vocabulary a Django developer
already has. The main alternative surface, django-extra-views, solved this problem first and its
split between the two kwarg dictionaries is a good idea taken directly from it. Its naming is not
followed: it drops the shorthand attributes that Django itself defines, and it rebinds `model` to
the parent after construction, which its own documentation has to warn readers about.

The prefix default comes from the relation rather than the model, because
`BaseInlineFormSet.get_default_prefix()` derives it from the reverse accessor. Two sets over the
same model through different foreign keys therefore differ with nothing declared, and only two
declarations over the *same* relation collide. Making that collision an error rather than letting
it through matters: two sets sharing a prefix parse the same submitted fields and share one
management form, and nothing about the resulting page looks wrong.

`get_form_kwargs` takes an index because sets exist whose forms are not interchangeable — one form
per permitted kind, or a form that must know what its siblings hold. A single dictionary shared by
every form cannot express either, and a project that needs it otherwise has to reach around this
surface and subclass Django's formset directly.

## Consequences

The `inline_*` attributes are gone, with no compatibility shim: the two surfaces never coexisted.
The package was pre-1.0, so the removal shipped in the same release as its replacement, with the
changelog mapping each removed attribute to what replaces it.

The view class names did not change. An upgrading project rewrites configuration, not imports.

A set declared with `exclude` on a model that reaches its parent through more than one relation
will render the sibling relation as a chooser over every parent record, because Django only
replaces the set's own foreign key. Name `fields` explicitly on that shape.
