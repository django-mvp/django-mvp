# ADR 0004 — Row removal sets Django's DELETE flag and never re-indexes

**Status:** accepted

## Decision

Removing a row on a formset page hides it and sets its `DELETE` field. This is the same for a row
that exists in the database and one the user just added. The row's inputs stay in the document
with their submitted values, and `TOTAL_FORMS` is incremented when a row is added and **never**
decremented.

The client-side state is two counters, not one:

- `total` is monotonic. It seeds `__prefix__` substitution and `TOTAL_FORMS`.
- `visible` counts rows not marked for removal, and is what the add control compares against the
  cap.

`total` is seeded from `{{ formset.total_form_count }}`, never from the management form's input
value in the DOM.

## Why

Django already distinguishes a saved row from an unsaved one: `save_new_objects` skips extra forms
marked for deletion, and `save_existing_objects` deletes the saved ones. The page therefore sets
one flag and lets Django decide what it means, rather than tracking the distinction itself.

Not decrementing is the load-bearing half. Django reads submitted rows by contiguous index from
zero, so removing a row from the middle and decrementing the count silently shifts every later row
onto the wrong index. Re-indexing the survivors instead is the standard source of off-by-one
defects in hand-written formset pages: it requires rewriting every `name`, `id` and `for`
attribute, and it buys nothing the `DELETE` flag does not already give. Keeping the inputs in the
document is also what makes a removal survive a submission that comes back invalid.

The two counters exist because they answer different questions. With one, removing a row on a
capped set would permanently forfeit its slot — the page would refuse a replacement that the
submission would accept, since Django tests `total_form_count() - len(deleted_forms) > max_num`.

Seeding from the template variable rather than the DOM matters because the management form's
`TOTAL_FORMS` input is a string the server re-emits verbatim after an invalid submission.
Substituting it into cloned markup would put a user-supplied string into a new row's `name` and
`id` attributes.

## Revisit if

Django changes how it reads submitted forms by index, or the page grows a requirement to reorder
rows, which would need `can_order` and a different relationship between position and index.
