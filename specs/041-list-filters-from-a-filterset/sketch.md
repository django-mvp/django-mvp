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

- **Every choice filter is a dropdown button, like the sort control.** The button carries the
  filter's name and, once one is chosen, the chosen value in lighter text. A native `<select>`
  was the other option; the button matches the sort control that was already on the page.
- **A single choice applies the moment it is picked.** Several values apply when the dropdown
  loses focus with a different set chosen.
- **A single-choice dropdown starts with "Any"**, which clears it. The sort has no such entry: no
  choice means the default order.
- **The multi-select button shows the count as a small badge** after its name, with the words
  "2 chosen" for a screen reader.
- **A boolean filter is a toggle with its label beside it**, and switching it off removes the
  filter rather than asking for "No".
- **The toolbar's order is the fields, then the result count, then Filter, then Add.** The count
  takes the space that is left, which pushes Filter and Add to the end of the row.
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
