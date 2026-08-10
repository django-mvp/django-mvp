# Phase 1 Data Model: Formset Pages

**Feature**: `024-formset-pages` | **Date**: 2026-08-05

The package ships no models and this feature adds none. It does add field metadata to one demo
model, which generates a single migration — see Demo models at the end. What follows is the
runtime shape of the data the page carries, which is what the spec's Key Entities describe.

## Entities

### Parent record

The single object the page is about. Edited through one `ModelForm`, exactly as the packaged
single-form pages edit it. Supplied by the view's `model` attribute; on a create page it does
not exist until the submission is saved.

### Related row

One record belonging to the parent, reached through a foreign key. Supplied by the view's
`inline_model`. Rows are created, edited and removed on the parent's page and are persisted only
when that page is submitted. Django's `inlineformset_factory` derives the foreign key from the
two models; where more than one relation exists between them, `fk_name` is supplied through
`get_formset_factory_kwargs()`.

### Row set

The collection of rows shown on the page, together with the bookkeeping that lets the submission
be read back. In Django terms this is a `BaseInlineFormSet` instance, reaching the template as
the context variable `formset`.

## The bookkeeping, and who owns each part

Nothing here is invented by this feature. Every field is Django's, and the page's job is to keep
them consistent.

| Field | Owner | Role on the page |
|---|---|---|
| `<prefix>-TOTAL_FORMS` | Django | How many rows the submission carries. **Incremented when a row is added; never decremented.** |
| `<prefix>-INITIAL_FORMS` | Django | How many rows already existed. Never touched by the page. |
| `<prefix>-MIN_NUM_FORMS` / `-MAX_NUM_FORMS` | Django | The configured bounds. Read by the add control, and enforced on the server through `validate_max`. |
| `<prefix>-<n>-id` | Django | The primary key of an existing row. Rendered as a hidden field; without it a submitted row cannot be matched to its record. |
| `<prefix>-<n>-DELETE` | Django | Whether this row is removed. Rendered hidden and driven by the row's state, never shown as a checkbox. |
| `__prefix__` | Django | The literal index in `formset.empty_form`, substituted with the new row's index when a row is added. |

## State a row can be in

| State | `id` present | `DELETE` | On submission |
|---|---|---|---|
| Existing, unchanged | yes | unset | Left alone |
| Existing, edited | yes | unset | Updated |
| Existing, removed on the page | yes | set | Deleted |
| Added on the page, filled in | no | unset | Created |
| Added on the page, then removed | no | set | Nothing — `save_new_objects` skips it |
| Blank extra row, untouched | no | unset | Nothing — `has_changed()` is false |

The two rows that persist nothing take different routes to the same outcome, and both are
Django's, not this feature's. That is the whole reason removal is uniform: the page sets one
flag and Django decides what it means.

## Validation rules

| Rule | Where it lives | Where its message renders |
|---|---|---|
| A row's field is invalid | The row's form | Inside that row, beside the field (FR-016) |
| A row is internally inconsistent | The row form's `clean()` | Inside that row, above its fields |
| Rows conflict with each other | The formset's `clean()` | Above the set (FR-017) |
| Too few rows | Django, when `validate_min` | Above the set |
| Too many rows | Django, when `validate_max` — which the view sets whenever `inline_max_num` is configured. `absolute_max` stays at Django's default and is never derived from the cap | Above the set |
| Management form missing or tampered with | Django | The submission is rejected rather than partly processed |
| Parent and rows valid together | The view | Neither is persisted unless both pass (FR-010) |

A row marked for deletion is excluded from validation by Django itself — `is_valid()` skips
forms `_should_delete_form()` returns true for — so removing an invalid row is a way of fixing
the page, which is the behaviour a user expects.

## Demo models

The worked example uses the demo application's existing pair, unchanged:

- `demo.Product` — the parent.
- `demo.OrderLine` — the row. Foreign key to `Product`, `on_delete=PROTECT`,
  `related_name="order_lines"`, plus `quantity`.

No field is added and no relation changes. Article IX is engaged all the same: neither of
`OrderLine`'s fields carries `verbose_name` or `help_text`, both are mandatory, and the article
says explicitly that it applies to `demo/`. They are added, with `gettext_lazy`, which generates
one migration — squashed with the branch's others at convergence. This is not incidental
conformance work: the worked example renders `quantity`, and a page demonstrating that a row's
field gets the same label and help text as a single form's field cannot demonstrate it with a
field that has neither.
