# Research: Reorder a list by dragging

Research and planning fill this file. Only the checks the specification depends on are here yet.

## Assumptions checked

- **Alpine and htmx ship with the package.** `package.json` bundles `alpinejs` 3.16.1 and
  `htmx.org` 2.0.10 into `mvp/static/js/django-mvp.js`, loaded by `mvp/templates/mvp/base.html`.
  A drag library joins the same bundle, which keeps goal G14.
- **Alpine's Sort plugin matches the bundled Alpine.** `@alpinejs/sort` is published at 3.16.1,
  the version the package bundles.
- **`c-mvp.form.formset` does nothing with `ORDER` today.** Neither the row set's templates
  (`mvp/templates/cotton/mvp/form/formset/index.html`, `row.html`) nor `mvp/static/js/formset.js`
  refer to `ORDER` or `can_order`. `row.html` renders every visible field except `DELETE` through
  crispy, so an ordered formset shows `ORDER` as a number field today. That is the behaviour
  FR-021 keeps for a page without scripts, and the field FR-001 fills.
- **Rows are never re-indexed.** `formset.js` keeps a monotonic counter and hides removed rows
  rather than detaching them (ADR 0004). Reordering moves rows in the document and writes `ORDER`
  values, so it changes neither the counter nor any row's index.
