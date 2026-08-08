# ADR 0003 — The packaged component owns formset structure; crispy renders only fields

**Status:** accepted

## Decision

`<c-form.formset>` renders the set's structure itself: the management form, one row per form,
set-level errors above the set, the blank-row template and the add control. Each row's individual
fields go through crispy's `|as_crispy_field`, one field at a time.

The `|crispy` filter is never applied to a formset, and `tailwind/uni_formset.html` is not
overridden.

## Why

crispy's own formset template is four lines and never renders `formset.non_form_errors`. Rendering
through it would silently drop every error belonging to the set as a whole, which is the specific
failure this feature exists to prevent. Its sibling error templates also emit raw Tailwind utility
colours rather than the DaisyUI semantic classes used everywhere else in the package, so the result
would not match the packaged look.

Overriding the vendored template at `tailwind/uni_formset.html` was the other option. It was
rejected because the override would have to reintroduce the errors, the controls, the blank-row
template and the client-side state — at which point it is a component wearing a vendored
template's path: invisible to the render-smoke floor, not overridable by a consumer at a `cotton/`
path, and in breach of the rule that reusable markup is a Cotton component.

Delegating per field is what makes a row indistinguishable from a single form. `as_crispy_field`
renders through the same `tailwind/field.html` that a single form's fields go through, including
this repository's own `help_text.html` override and the per-field error block. Row-level error
placement therefore comes for free rather than being reimplemented.

## Revisit if

crispy-tailwind's `uni_formset.html` grows non-form-error rendering and DaisyUI-compatible error
markup, or the package stops rendering forms through crispy at all.
