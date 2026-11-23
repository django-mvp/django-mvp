# ADR 0044 — Reordering a row set moves the rows and writes `ORDER`

**Status:** accepted

## Decision

A formset built with `can_order` is reordered by moving each row's element in the page and writing Django's `ORDER` field to match. A row is never given a new index: its field names, `TOTAL_FORMS` and the position of a removed row in the document stay as they were, so [ADR 0004](0004-row-removal-uses-the-delete-flag-and-never-reindexes.md) holds.

Three rules go with it.

- **A blank extra row keeps a blank `ORDER`.** The browser numbers `1..n`, in the order shown, only the rows Django would read: a saved row, and a row with a field that has changed. The server marks the rows that need a number with a `data-` attribute (a row below `initial_form_count`, or one whose form `has_changed()`), and the browser adds any row whose fields differ from their defaults. Every other row is cleared.
- **`ORDER` is held twice.** Each row carries a hidden `ORDER` input that the browser writes. Next to it, inside a `noscript` element, the row carries the typed `ORDER` field Django built. The typed field comes later in the row, so with scripts off the typed number wins, and with scripts on only the hidden one exists on the page.
- **A bound set is drawn in the submitted order.** The `formset_rows` filter sorts the forms of a bound set that can order by their submitted `ORDER`. A blank or unreadable value sorts last, and rows that tie keep their places. Every other set is drawn as it is.

## Why

Django reads a submitted row by its index and then orders the valid ones by `ORDER`. Moving the element and writing one field is the whole change a reorder needs. Renumbering the rows instead would rewrite every `name`, `id` and `for` attribute in the moved rows, and is the off-by-one defect ADR 0004 already declines.

Django's own `ordered_forms` skips an extra row that has not changed, so a blank extra row must still look unchanged after rows are moved. A number written into it makes the row look filled in, fails its required fields and turns a valid page into an invalid one. Leaving it blank keeps the set valid without asking the person to do anything.

A number is also needed on a row the person filled in and the server then returned for correction. The page shows that row's saved field values as defaults, so the browser cannot tell the row was filled in. The server can, which is why it marks the row.

Keeping the typed field in a `noscript` element lets the page offer a number input only to a person who has no controls to use. The set is then still reorderable without scripts, through the field Django already validates.

An invalid submission drawn in its first order would undo the person's moves on every error. Sorting by the submitted value puts the rows back where they left them, with every value kept.

## Revisit if

Django changes how `ordered_forms` treats an extra row, or a set needs to be reordered across pages, where a row's place can no longer be decided from the rows on the page.
