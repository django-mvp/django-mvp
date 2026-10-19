# Research: FS-041

Investigated on 2026-10-19, against `origin/main` at 0e097f5 (after #546) and the approved sketch
at df4d6ec. django-filter 26.2, daisy-cotton 0.2.0, django-mvp-forms 0.5.0, Django 6.1.

## Planning notes, answered

Each of Sam's planning notes (`planning-notes.md`), in his words, then adopted or not, and why.

**One form wraps the toolbar fields, the Filter button and the filter modal; Add sits outside
it.** Adopted, with one change the sketch found: the Filter button only opens the modal, so it
sits outside the form too, next to Add, and the two wrap together at the end of the row. The form
holds the toolbar fields and the dialog. Add's create dialog is never inside the filter form. The
sort's control sits outside the form as well (FR-010 puts it at the end of the row); its one input
names the form with the `form` attribute.

**`display: contents` on the form.** Adopted. The sketch confirmed that the form's children take
part in the toolbar's flex row, at 1440, 1200 and 390 pixels.

**Rebuild `c-mvp.modal` on daisy-cotton 0.2.0's `c-modal`.** Adopted. 0.2.0's `c-modal`
(`daisy_cotton/templates/cotton/modal.html`) closes with `type="button"` buttons that call
`close()`, holds no form, and names the dialog with `aria-labelledby`. `c-mvp.modal` keeps its
props (`id`, `size`, `position`, `closable`, `class`) and its slots (`actions`, `footer`,
`footer_end`) and draws its card inside `c-modal`'s box. ADR 0032 governs the call: isolated,
`only`, with every value passed explicitly.

**daisy-cotton 0.2.0 is breaking: `c-alert`'s variant no longer picks an icon.** Adopted. The
seven alerts that relied on it are in `mvp/account/login.html`, `mvp/account/_development_notice.html`,
`cotton/mvp/messages.html`, `cotton/mvp/form/formset/index.html` and `delete_view.html` (three).
Each passes the icon the variant used to choose: daisy-cotton 0.1.3's alert drew
`<c-icon name="{{ variant }}">` when no icon was given, so each alert passes `icon` equal to its
variant (the messages alert passes the mapped variant it already computes). The whitespace change around `link`, `badge`,
`kbd`, `status`, `icon` and `button` is checked by rendering every demo page in the suite that
already does so; no template relies on that space in a way a test pins. Pin becomes
`daisy-cotton (>=0.2,<0.3)`.

**Fields drawn inside the filter form must not draw a `<form>` of their own.** Adopted. The modal
draws each field with `{{ field|as_crispy_field }}`, which writes no form tag. `c-mvp.form` is not
used inside the filter form.

**Search and sort filters on django-filter's public Filter interface; a thin sort filter taking
`(key, label, columns)`.** Adopted. `SearchFilter(CharFilter)` and `SortFilter(ChoiceFilter)` in a
new public module, `mvp/filters.py`, each overriding only `filter()`. django-filter's own
`OrderingFilter` was rejected: it accepts comma-separated keys, so a reader can combine orders the
developer never offered, and it has no tiebreak.

**`FilterView`'s `strict` mode; `strict = False` should give "ignore the bad value".** Not adopted
as written. `FilterView` is not used at all (see "The list view and its filterset" below), so
`strict` does not arise. `BaseFilterSet.qs` validates the form and then filters by
`form.cleaned_data`, which holds only the fields that validated, so an invalid value is already
dropped for its own field alone. That is FR-009 with no setting.

**Name the fields `q` and `o` in the documentation's examples.** Adopted.

**The compact toolbar field templates and the multi-select dropdown may belong in
django-mvp-forms.** Not adopted. They draw a filterset field in django-mvp's toolbar, read the
toolbar's own description of the field, and submit django-mvp's filter form. django-mvp-forms
draws a field inside a crispy form and knows nothing of the toolbar. A developer who wants a
django-mvp-forms control in the toolbar gives the filter that widget, and the toolbar draws it as
it is (FR-027). The toolbar's templates are components under `cotton/mvp/page/list/filters/`.

**The table view's `__init_subclass__` check becomes "drop the sort filter", silently.** Adopted,
with Sam's ruling at intake. `MVPTableViewMixin.get_filterset()` removes every `SortFilter` from
the instance's `filters` before the form is built. The `__init_subclass__` refusal of `order_by`
goes, because `order_by` is gone from every view.

**A demo page for each shape.** Adopted. The sketch's three list pages stay: the full product
list, `/products/quick/` (everything in the toolbar) and `/products/modal-only/`.

**A migration note in the documentation and the CHANGELOG.** Adopted. `docs/views.md` gains a
section "Moving search_fields and order_by into a filterset", and the CHANGELOG's breaking entry
points to it.

**An ADR replacing R16's "never a required dependency".** Adopted: `docs/adr/0033-django-filter-is-a-runtime-dependency.md`.
R16's line and the README's "Optional integrations" section are changed to say django-filter is
required and django-tables2 and htmx stay optional.

**Sam, sketch round 3: say which toolbar fields grow and which keep their size.** Not adopted in
this feature. The search grows; every other field keeps its size. A per-field choice is a new
setting nobody has a case for yet, and the existing-first list stops at "does it need to exist?".
Recorded in `decisions.md` with what would revisit it.

**Sam, sketch round 3: django-mvp does not support or load Tom Select.** Adopted. Nothing in the
package names Tom Select. The toolbar draws any widget that is not its field's default as it is
(FR-027) and applies it when focus leaves it changed. The demo's `base.html` loads Tom Select and
`mvp_forms/tomselect.css`, as django-mvp-forms' README tells a project to.

**Upstream django-mvp-forms#215 and #216.** Noted. Neither blocks this feature. The demo keeps the
counted Category control and django-filter's range inputs until they ship.

## What the sketch asks of the code

From `sketch.md`, each a requirement the plan meets:

| The screens need | Met by |
|---|---|
| Fields sorted into toolbar (in order) and modal | `toolbar_placement()` in `mvp/views/list.py` (plan, "Placement") |
| Per toolbar field: kind, label, value, choices | the same, one dict per field |
| Count of the modal's applied filters; address with only the modal's filters removed | `FilterContextMixin` |
| Sort out of applied filters, refinements, clear actions | `get_active_filters()` skips `SortFilter` |
| A table's filterset without its sort | `MVPTableViewMixin.get_filterset()` |
| Bad values ignored one filter at a time | `BaseFilterSet.qs` already does it |
| django-filter's templates available | `django_filters` in `INSTALLED_APPS`, documented in the README's install steps |
| A dialog with no form of its own; `type="button"` inside the form | `c-mvp.modal` on `c-modal`; every toolbar button names its type |
| Modal fields restored on close | `mvp/static/js/list_view.js` |
| Untouched fields left out of the address | `mvp/static/js/list_view.js`, on `formdata` |

| The sketch faked | Becomes |
|---|---|
| Prototype filters and placement | T004–T006, T013–T015, test-first |
| Old mixins and module still present | T007–T009 remove them |
| Config errors never shown | tests in T013 |
| `c-mvp.modal` patched in place | T002 |
| Old toolbar beside the new | T010 removes the old path |
| Custom-toolbar table page not converted | T026 |
| Inline modal-reset script | T018 moves it to `list_view.js` |
| Sample data with no long names | T027 adds a long-named product to the demo seed |

## The list view and its filterset

`django_filters.views.FilterView` is not used. Its `get()` replaces `object_list` after
`get_queryset()` and empties it on an invalid form in strict mode, and its `FilterMixin`
defaults `filterset_fields` to every field, so a bare `MVPListView(model=...)` would sprout a filter
for every model field. The list view needs neither.

`MVPListViewMixin` instead gains a small filterset hook built from django-filter's public pieces:
`filterset_class` (default `None`) and `filterset_fields` (default `None`). When either is set, it
builds the filterset class with `django_filters.filterset.filterset_factory`, instantiates it once
per request with `data=request.GET or None`, `request` and the view's base queryset, and
`get_queryset()` returns `filterset.qs`. When neither is set there is no filterset, no `filter` in
the context, and the toolbar draws only Add (FR-006). The filterset is in the context as `filter`
(the name the components and `FilterContextMixin` already read) and as `filterset`.

`MVPFilteredListView` and `mvp.integrations.django_filters` are deleted; `MVPListView` is the one
list view.

## The removed settings

`SearchMixin`, `OrderMixin` and `SearchOrderMixin` are deleted. A class that still sets
`search_fields` or `order_by` to anything truthy is refused in `MVPListViewMixin.__init_subclass__`
with `ImproperlyConfigured` naming the class, the setting and `SearchFilter`/`SortFilter` (FR-002),
so the error happens at import, as the table view's `order_by` check does today.

## What already exists

One line per new piece of code: where the search stopped.

| New piece | Stopped at | Found |
|---|---|---|
| Search filter | 3. installed package | `django_filters.CharFilter`; only `filter()` is new |
| Sort filter | 3. installed package | `django_filters.ChoiceFilter`; only `filter()` is new. `OrderingFilter` rejected above |
| Building the filterset | 3. installed package | `django_filters.filterset.filterset_factory`, `BaseFilterSet.qs` |
| Applied filters, labels, display values, params, clear URLs | 2. this repo | `FilterContextMixin` (`mvp/views/list.py`), extended |
| Toolbar placement | 7. new code | Nothing here or in django-filter decides which fields go where |
| Dialog that closes without a form | 3. installed package | daisy-cotton 0.2.0 `c-modal` |
| Dropdown for choices | 2. this repo | `c-mvp.dropdown`, as the current sort control uses it |
| Toggle, checkbox, input, join | 3. installed package | daisy-cotton `c-form.input`, `c-join`; native checkboxes for the toggle and list, as daisy-cotton's own toggle template writes |
| Field rendering in the modal | 3. installed package | crispy `as_crispy_field` with the django-mvp-forms pack |
| Submit on change, on close, on focus leaving | 5. the browser | `HTMLFormElement.requestSubmit()`, `focusout`, `change`; Alpine is already on every page |
| Dropping empty values from the address | 5. the browser | the form's `formdata` event |
| Restoring modal fields on close | 5. the browser | `defaultValue`, `defaultChecked`, `defaultSelected` |
| Page number reset on change | 5. the browser | the page number is not a field of the form, so a submit drops it |
| Count row | 2. this repo | `c-mvp.page.list.summary` and `c-mvp.page.list.refinements` |
