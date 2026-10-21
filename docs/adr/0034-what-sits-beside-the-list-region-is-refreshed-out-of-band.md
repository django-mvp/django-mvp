# ADR 0034 — What sits beside the list region is refreshed out of band

**Status:** accepted

## Decision

A list or table page updates in place by swapping one element, the list region (`list_region_id`, default `mvp-list`). Anything on the page that has to follow the response but sits outside that region is refreshed from the same response with htmx's `hx-select-oob`. It is not moved inside the region.

The filter panel is the first such element. Its root id is a view attribute, `filter_panel_id` (default `filters`), beside `list_region_id`. Every element that swaps the region carries `hx-select-oob="#<filter_panel_id>"`:

- the toolbar's filter form
- the filter chips
- the pager
- the empty state's Clear all
- the table's column headings
- the panel's own Clear

The attribute is always present. htmx skips an out-of-band selector that the response does not contain.

## Why

The filter panel sits beside the results, in the page layout's grid, not inside the region. Its Clear link and its field values must reflect the response, or the next Clear would restore a sort or filter the reader has already changed. Widening the region to hold the whole layout would put the page title and the grid inside every swap. The panel's open drawer would then be rebuilt on every keystroke in the search box.

The id sits on the panel component's root, not on its inner `<aside>`. The out-of-band swap therefore replaces the whole component, an open drawer and its Alpine state included, and the old component releases the page in `destroy()`.

## Revisit if

The list region is moved to wrap the whole page layout, or a second element beside the region needs refreshing and a list of selectors on every swapping element becomes hard to keep complete.
