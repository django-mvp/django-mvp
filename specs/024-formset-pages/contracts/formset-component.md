# Contract: `<c-form.formset>` and `<c-form.formset.row>`

The rendering half of the feature. Both components are public API under Article XI: named for
their domain role, overridable by placing a template at the same path in the consuming project,
and customisable through attributes rather than utility classes.

---

## `<c-form.formset>`

**Template**: `mvp/templates/cotton/form/formset/index.html`

Renders a whole Django formset: the bookkeeping Django needs to read the submission back, any
error belonging to the set as a whole, one row per form, and the controls that add a row.

### Attributes

| Attribute | Default | Meaning |
|---|---|---|
| `formset` | — | The formset to render. Required in practice; absent renders nothing. |
| `title` | model in plural | Heading in the divider that opens the set. Falls back to `formset.title`, then to the set's model's plural name. |
| `description` | — | Help text under the heading. Falls back to `formset.description`. Omitted entirely when unset. |
| `add-label` | `"Add row"` | Text on the add control, which also carries a plus icon. |
| `remove-label` | `"Remove"` | Accessible name for each row's remove control, passed through to rows. |
| `class` | — | Merged onto the root element. Declared so the caller's classes are not dropped. |

Unrecognised attributes pass through to the root element, as with every packaged component.

### Rendered contract

1. The formset's management form is present. Without it Django rejects the submission outright,
   and FR-005 requires it.
2. `formset.non_form_errors` renders **above** the rows, inside `<c-alert variant="error">`,
   and only when non-empty. It is visually and structurally distinct from a row's error, which
   renders inside the row (FR-017).
3. One `<c-form.formset.row>` per form in `formset`, in formset order. Blank extra rows are
   presented identically to populated ones (US2 scenario 3).
4. `formset.empty_form` is rendered exactly once inside an inert `<template>` element. It is not
   part of the submitted document and contains the literal prefix `__prefix__`.
5. The root element carries the Alpine state for the set, as **two** counters rather than one:
   - `total` — monotonic. It seeds `__prefix__` substitution and `TOTAL_FORMS`, and is never
     decremented, because Django reads submitted rows by contiguous index.
   - `visible` — the number of rows not marked for removal.

   `total` is seeded from `{{ formset.total_form_count }}`, an integer Django has already
   clamped to `absolute_max`. It is **never** read from the management-form input's DOM value:
   that is a string the server re-emits verbatim after an invalid submission, and substituting it
   into cloned markup is an injection seam.
6. The add control compares **`visible`** against `formset.max_num`, so removing a row on a
   capped set frees its slot rather than forfeiting it. It is present when the formset permits
   another row, disabled at the cap (FR-026), and never submits the form. The control is
   presentation only — the cap is enforced on the server by the view, per
   `contracts/inline-view.md`.
7. Rendering with no `formset` in context produces no error. This is not defensive style — it is
   the contract `tests/test_components/test_render_all.py` enforces on every packaged component.

### What it does not do

It does not render the `<form>` element, the CSRF token, or the submit buttons. Those belong to
`<c-form>` and the page template. A formset renders inside a form, never as one.

---

## `<c-form.formset.row>`

**Template**: `mvp/templates/cotton/form/formset/row.html`

Renders one form of a formset as a row.

### Attributes

| Attribute | Default | Meaning |
|---|---|---|
| `form` | — | The individual form. Absent renders nothing. |
| `first` | `False` | Suppresses the leading rule. Set by the parent from `forloop.first`; a row cloned from the empty-form template is never first. |
| `label` | the object | Heading for the row. Defaults to the instance's string once saved, and to `New <model>` before that, since `str()` on an unsaved model reads `Thing object (None)`. Empty for a non-model form. |
| `remove-label` | `"Remove"` | Accessible name for the remove control, which renders as a trash icon with no visible text. |
| `can-delete` | `False` | Whether to offer a remove control. Set by the parent from `formset.can_delete`. |
| `class` | — | Merged onto the root element. |

### Rendered contract

1. Every hidden field of the form is rendered. For an inline formset that includes the primary
   key, without which Django cannot match a submitted row to its record.
2. Every visible field **except `DELETE`** is rendered through crispy's field template, so a
   row's field is presented identically to the same field on a single form — same control, same
   label, same help text, same error placement (FR-004, FR-016, SC-008).
3. `DELETE` is rendered as a hidden input rather than a visible checkbox, and its value is
   driven by the row's removed state. It is never presented to the user as a field.
4. The form's own non-field errors render inside the row, above its fields.
5. The remove control appears only when `can-delete` is set. It carries an accessible name,
   never submits the form, and decrements the set's `visible` counter.
6. A removed row is hidden, not detached. Its inputs stay in the document with their submitted
   values, which is what keeps the formset's indices contiguous and what makes a removal
   survive an invalid submission (R2).

---

## Where a formset reaches the page

`mvp/templates/form_view.html` gains, inside the `<c-form>` body and above the actions:

```django
{% block formset %}
  {% if formset %}<c-form.formset :formset="formset" />{% endif %}
{% endblock formset %}
```

Any packaged form view that puts `formset` in its context therefore renders it in the right
place with no further configuration, which is how FR-006 and US2 scenario 4 are satisfied
without a second view.

`<c-form>` gains an optional `formset` attribute, consulted alongside `form_obj.is_multipart`
when deciding the form's `enctype`. A file field on a row would otherwise submit without the
multipart encoding.

The page template also emits `formset.media` alongside `form.media`, so a row's widget can
carry its own assets.
