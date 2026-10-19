# Planning notes: FS-041

Suggestions from the intake discussion on #536 (2026-10-19), for the build to answer one by one.
They are inputs, not instructions.

Sam's design for the markup. One form wraps the toolbar fields, the Filter button and the filter
modal. The Add button and its create modal sit outside that form, next to it, so the create form
is never inside the filter form. Every field inside the form submits with it, with no `form=`
attribute on each input. Sam's pseudo code shows the shape only. The names in it are not to be
used.

The filter form sits in the middle of the toolbar's flex row. `display: contents` on the form
lets its children take part in the toolbar's layout as if the form were not there, so the result
count can still sit between the toolbar fields and the controls.

The filter modal sits inside a form, so the dialog component must close without a form of its
own. daisy-cotton 0.2.0 does that: its close button and backdrop are now buttons that call the
dialog's `close()`. Rebuild `c-mvp.modal` on daisy-cotton's `c-modal` rather than keep its own
copy of the dialog markup, so it picks up that fix and the dialog's accessible name. ADR 0032 says
how calls to daisy-cotton components are made.

daisy-cotton 0.2.0 is a breaking release. `c-alert`'s `variant` no longer chooses an icon, and
seven alerts in this package rely on it: the flash messages, the login error, the development
notice, the delete page's two alerts and the related-objects alert, and the formset's non-form
errors. Each needs an explicit `icon`. The release also drops the whitespace around `link`,
`badge`, `kbd`, `status`, `icon` and `button`, so check any template that relied on that space.
The pin moves from `>=0.1.3,<0.2` to `>=0.2,<0.3`.

Fields drawn inside the filter form must not draw a `<form>` of their own. `c-mvp.form` draws one,
and `form/render.html` already says a crispy helper needs `form_tag = False`.

Write the search and sort filters on django-filter's public Filter interface. django-filter's
`OrderingFilter` takes comma-separated keys and has no tiebreak, so a thin sort filter that takes
`(key, label, columns)` options keeps today's whitelist and tiebreak guarantees.

django-filter's `FilterView` has a `strict` mode that empties the list when the form is invalid.
Setting `strict = False` should give the "ignore the bad value" behaviour the spec asks for.
Check it against django-filter 26.

Name the fields `q` and `o` in the documentation's examples, so addresses people already saved
keep working when a project moves to a filterset.

The compact toolbar field templates, and the multi-select dropdown button, may belong in
django-mvp-forms, the template pack forms render with, rather than here. Decide where they live.

The table view refuses `order_by` today in `__init_subclass__`. That check becomes "drop the sort
filter from the table's filterset", silently.

A demo page for each shape: a list with two or three toolbar filters and no modal, and a list with
a large modal form.

A migration note in the documentation and the CHANGELOG for moving `search_fields` and `order_by`
into a filterset.

An ADR replacing R16's "never a required dependency" for django-filter, alongside 0006 and 0031,
which record the other runtime dependencies.
