# ADR 0009 — A rows-only page touches the parent rather than saving it

**Status:** accepted

## Decision

An update page configured with no fields of its own — `fields = []` — renders none of the parent
record's fields and shows only its related sets, attached to the record the URL names.

On that page the parent's form is **never saved**. The record's own field values are not written.

By default the page still updates the record's `auto_now` fields, so the record shows as having
changed when its rows changed. That write names those fields explicitly and touches nothing else.
It happens inside the same transaction as the rows, and a view can switch it off.

Where the model has no `auto_now` field there is nothing to write and the page writes nothing.

A create page configured with no fields is a configuration error, as is an update page with neither
fields nor sets.

## Why

**Editing a record's rows should show up on the record.** A project whose description changed has
changed, and a page that leaves no trace anywhere is the surprising outcome rather than the careful
one — especially where the related rows carry no timestamps of their own, which is the ordinary
case for the small typed rows this shape suits.

**But not by saving the empty form, which loses data.** A model form with no fields is always
valid, and saving it issues a full update of every column from the values read when the page was
opened. Measured against this project's database:

| What was done | Result |
|---|---|
| write only the `auto_now` fields | timestamp updated |
| the same, after another writer changed a different field | that change survived |
| save the field-less form | **that change was lost** |

The third row is the argument. The risk is highest on exactly this page: a long-lived editing
screen for a record other people also edit. Naming the fields to write removes it, and costs
nothing, so the surgical write is not a trade-off against the obvious one — it is strictly better.

**The default is on because it cannot misfire.** A model with no `auto_now` field has nothing to
write, so the behaviour only ever acts where the developer has already declared, by putting such a
field on the model, that they care when the record last changed.

**Creation is excluded** because a page that never shows a record's fields has nothing to build one
from, and would have to save an empty record to give the rows something to belong to — which is
precisely the record nobody asked for.

## Consequences

The touch fires the model's save signals and any lifecycle hooks attached to them. That is how a
change to a record's rows becomes observable at the record level, and it is not a silent write.

"Does not change the parent's field values" and "does not write the parent at all" are different
statements, and the difference is the whole of this decision. The test that holds it in place is
the concurrency one: another writer changes a field while the page is open, and their change has
to survive the submission.
