# Sketch: FS-041

The prototype for the spec's screens, built on this branch before planning. Nothing in it is
tested. Everything marked `SKETCH (FS-041)` in the code is prototype code that the build replaces
test-first.

## What exists

- **Data.** The demo's `Product` has what every filter on screen needs: a name and description to
  search, a status and a priority with fixed choices, a category (a foreign key, 8 categories in
  the seeded data), a price, a stock count, a release date, and featured and available flags.
  32 products are seeded.
- **Views.** `MVPListViewMixin` already composes with django-filter's `FilterView`, and
  `FilterContextMixin` already reads the filterset from the context, works out which filters are
  applied, what each one is called and how to show its value, and builds the address without a
  given filter. The refinements row and the clear-all link are built from that. Search
  (`SearchMixin`) and sort (`OrderMixin`) are separate mixins reading `?q=` and `?o=`.
- **Table view.** `MVPTableViewMixin` refuses `order_by` when the class is defined. Its toolbar
  panel draws search and the Filter button; column headers sort the table.
- **Components.** The toolbar row (`c-mvp.page.list.toolbar`) and the sort control's dropdown
  (`c-mvp.dropdown`, focus-driven daisyUI) are the pattern the toolbar fields follow. The filter
  modal (`c-mvp.modal`) closes with two `<form method="dialog">` elements, so it cannot sit inside
  a form as it stands. `c-button` writes no `type`, so inside a form every button submits.
- **Planning notes that bear on the screen.** Sam's form design (one form around the toolbar
  fields and the modal, Add outside it) is what the sketch is built on. daisy-cotton 0.2.0 is
  the fix for the modal; the sketch patches `c-mvp.modal` instead of upgrading.

## What the screens need from the code

- Every filterset field, sorted into the ones the view names for the toolbar, in the order named,
  and the rest for the modal.
- For each toolbar field: what kind of control it is (search, text, single choice, toggle,
  several values, sort), its label, its current value, and for choices the list of values with
  which are chosen and the label of the current one.
- How many of the modal's filters are applied, for the Filter button's count.
- The address with only the modal's filters removed, for the modal's clear action.
- The sort left out of the applied filters, the refinements row and both clear actions.
- A table page's filterset with its sort filter taken out before anything is drawn or applied.
- A filterset whose bad values are ignored one by one (`strict = False` on the demo views).
- django-filter's own templates available, because its range widgets render from them
  (`django_filters` in `INSTALLED_APPS`). The README's install steps will need to say so.
- A dialog that closes without a form of its own, and buttons that say `type="button"` wherever
  they sit inside the filter form: the Filter button and every dropdown's trigger.
- The modal's fields put back as they were when it is closed without applying, so a later
  toolbar change does not send them.

## What the sketch faked

- `SearchFilter` and `SortFilter` in `mvp/filters.py` are prototype code with no tests.
- `describe_toolbar_field()` in `mvp/views/list.py` and the placement code in
  `FilterContextMixin.get_context_data` are prototype code with no tests.
- The old `SearchMixin`, `OrderMixin`, `MVPFilteredListView` and the optional integration module
  are still there. The demo's converted pages just don't use them. Removing them, and refusing a
  view that still declares them, is not sketched.
- The unknown toolbar field error and the "can't draw this field" error are raised, but never
  shown on a page.
- `c-mvp.modal` is patched in place to close by script. It is not rebuilt on daisy-cotton's
  `c-modal`, and daisy-cotton is still at 0.1.x, so the alerts' icons are untouched.
- `list_view.html` and `table_view.html` keep their old toolbar beside the new one, chosen by
  whether the view has a filterset. The old `page.search` and `page.controls` blocks only exist
  on the old path.
- The custom-toolbar table page (`/django-tables2/custom-toolbar/`) still uses
  `filterset_fields` and its old `search_fields`. It was not converted.
- The modal's reset-on-close is an inline script in the component.
- The demo's sample data is the existing seed. No product has a very long name and no category
  list is long enough to scroll.

## What was ruled by eye

Taste calls made while drawing it, for Sam to overrule:

- **Every choice filter is a dropdown button, like the sort control.** A native `<select>` was the
  other option; the button matches the sort control that was already on the page.
- **A single choice applies the moment it is picked.** Several values apply when the dropdown
  loses focus with a different set chosen.
- **A single-choice dropdown starts with "Any"**, which clears it. The sort has no such entry: no
  choice means the default order.
- **A boolean filter is a toggle with its label beside it**, and switching it off removes the
  filter rather than asking for "No".
- **The toolbar is the fields, then Filter and Add together at the end of the row.** Filter and
  Add wrap as one group.
- **The search keeps its Search button**, as the toolbar has today, though Enter also submits.
- **On a table page the toolbar fields sit in the collapsible panel, with Filter at its end**,
  where search and Filter are today. Add stays in the bar.

## Pages

| Page | What it shows |
|---|---|
| `/products/` | Search, Status, Category (several values), Featured only and Sort in the toolbar. Priority, price, stock, release date and Available in the modal |
| `/products/quick/` | A short filterset, everything in the toolbar: no Filter button, no modal |
| `/products/modal-only/` | The full filterset with nothing named for the toolbar: every field in the modal |
| `/products/many/` | The full list at three a page, to see a filter change return to page one |
| `/products/none/` | No products: the toolbar is not drawn |
| `/django-tables2/` | The same filterset on a table page. Its sort is dropped, and the columns sort |

## Round 2 (Sam, 2026-10-19)

| Sam asked | Done |
|---|---|
| Show a filter's value either in its control or as a chip, never both. He leans to chips, because a control that grows with its value makes the toolbar's width unpredictable | Chips only. No toolbar control shows its value. The sort, which has no chip, names its order beside the result count instead of on its button |
| What "never asks for No" means for the toggle | Answered in the session: switched off, the toggle removes the filter and shows everything. It never filters down to the products that are *not* featured |
| Search is good | Kept |
| The result count looked bad in the toolbar; find it a new place | The count now leads the row of chips, directly above the results, followed by the sort in use |
| Show django-mvp-forms widgets in the filter forms, in particular Tom Select with a count, for fields with many options that need their own search | Category in the toolbar is a counted `TomSelectMultiple`; it applies when its dropdown closes with a different choice. In the modal, SKU is a counted `TomSelectMultiple` over every SKU and Priority is a `TomSelect` with a clear button |

Found while doing it, for the plan:

- A toolbar control the developer gave a django-mvp-forms Tom Select widget is drawn by that widget
  rather than by the toolbar's own dropdown. The view gives it daisyUI's `select` class.
- Tom Select and its stylesheet come from a CDN in the sketch. G14 says the package ships every
  asset it needs, so the build has to carry them.
- The form's media has to be written on the page for the widgets' script to load.
- The filter form leaves untouched fields out of the address. Without it, every empty range and
  the "unknown" value of a yes/no select were written into the address on every submit.
- django-filter's range filters draw two stacked inputs with a "-" between them, and a yes/no
  filter in the modal draws a select reading "Unknown". django-mvp-forms has no min–max widget.
  The modal will need one, or the demo picks different filters.
- On a phone, five toolbar fields take four rows above the results.
- The counted control shows its empty text ("Category") in place of a label when nothing is
  chosen, and "2 selected" once something is. Its name is on the chip.

## Round 3 (Sam, 2026-10-19)

| Sam asked | Done |
|---|---|
| Chips only, and the result count above the results | Approved as they are |
| On phones, five toolbar fields taking four rows | Accepted as it is |
| Search could grow to fill the row, and a developer could say which toolbar fields grow and which shrink | The search now takes the room the row has left, at least 15rem from md. How a developer marks other fields to grow or shrink is left to planning (see `planning-notes.md`) |
| Move Sort to the right when it is present | Sort sits at the end of the row, before Filter and Add, wherever it is named in `toolbar_filters` |
| The counted Category control loses its name once something is chosen | Raised upstream as django-mvp/django-mvp-forms#215 (a counted control with no visible label that still names its field, for example with a joined label at its start). The sketch keeps the control as it is |
| Range filters matter on most list pages, and django-mvp-forms should have widgets for them | Raised upstream as django-mvp/django-mvp-forms#216. The modal keeps django-filter's stacked inputs until then |
| django-mvp does not support Tom Select; django-mvp-forms already tells projects to load it themselves | django-mvp no longer loads or knows about Tom Select. The demo's own base template loads Tom Select and `mvp_forms/tomselect.css`. A toolbar field whose filter has a widget of the developer's own is drawn by that widget, and applies when focus leaves it with a different value, whatever the widget is |
