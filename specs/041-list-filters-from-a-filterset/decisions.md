# Decisions: FS-041

Rationale for the choices the specification makes that the intake discussion on #536 did not
settle in so many words.

## D1 — The search keeps today's matching

**Ambiguous:** whether the shipped search filter should match the way the search box does now,
or follow some other rule (all words rather than any word, whole words, no word limit).

**Chosen:** today's rule. Any word in any named field, ignoring case, each record once, the first
ten words only.

**Why:** the feature changes where search is declared, not what it finds. A project moving its
`search_fields` into a filterset should get the same results it had. The ten-word limit is a
safeguard, not a taste call: the expression grows with words times fields, and an unbounded term
lets the requester decide how deep the query gets.

**ADR:** none — keeps existing behaviour; the search filter's docstring and docs/views.md state the rule

## D2 — Changing anything returns the list to its first page

**Ambiguous:** whether a filter change keeps the page number.

**Chosen:** it goes back to the first page.

**Why:** the new result can have fewer pages, and a page number past the end is answered with a
404. The remove links in the refinements row already drop the page number for the same reason.

**ADR:** none — a behaviour of this feature's list page, stated in docs/views.md

## D3 — Two clear actions, two different reaches

**Ambiguous:** once some filters live in the toolbar and some in the modal, what the modal's
clear action should clear.

**Chosen:** the modal's clear removes the modal's fields only. The refinements row's clear-all
removes the search and every filter. Neither touches the sort.

**Why:** the modal's action sits inside the modal, so a reader expects it to act on what the modal
shows. Clearing a toolbar value from inside the modal would change something they can't see from
there. The refinements row lists everything applied, so its clear-all removes everything listed.
The sort was never a refinement, and clearing filters has never reset it.

**ADR:** none — a behaviour of this feature's list page, stated in docs/views.md

## D4 — The Filter button counts only the modal's filters

**Ambiguous:** what the count on the Filter button includes once some filters are in the toolbar.

**Chosen:** only the applied filters in the modal.

**Why:** the count tells the reader that something hidden is applied. A toolbar value is on
screen next to the button.

**ADR:** none — a behaviour of this feature's list page, stated in docs/views.md

## D5 — A bad value is ignored, not fatal

**Ambiguous:** django-filter's own view, by default, shows an empty list when any field fails to
validate.

**Chosen:** the invalid value is ignored for its own filter, the other filters apply, and the list
is not emptied.

**Why:** addresses outlive the options they were built from: a bookmark made before a sort option
was renamed, a link to a status that was retired. Today an unknown sort value is ignored, and an
empty "nothing matches" page for a stale bookmark would look to the reader like the data had
gone. Keeping today's behaviour for the sort and extending it to every filter is the consistent
choice.

**ADR:** none — extends the existing handling of a stale sort value; stated in docs/views.md

## D6 — A table page ignores the sort without an error

Sam's ruling at intake (2026-10-19). The table view today refuses a view-level ordering when the
class is defined, because the table has its own column sorting. Sam asked that a sort filter on a
table page's filterset be ignored silently, so one filterset can serve a list page and a table
page. Refusing it would make a developer keep two copies of the same filterset.

**ADR:** none — local to the table view, stated in its docstring and docs/views.md

## D7 — Toolbar fields do not move into the modal on small screens

**Ambiguous:** #536 suggests the filter modal stays for narrow screens.

**Chosen:** toolbar fields stay in the toolbar at every width and wrap.

**Why:** a field hidden by a style is still submitted, so a field drawn in both places would send
its value twice. Moving it properly needs a screen-width check in the page, and ADR 0021 leaves
responsive visibility to the browser. Agreed with Sam at intake as out of scope.

**ADR:** none — follows ADR 0021 rather than changing it

## Design review outcome (S3R, 2026-10-19)

One reviewer, three lenses, one round: `request_changes`, 1 high, 7 medium, 9 low, no security
finding. Every finding was applied to `plan.md`, `tasks.md` or `research.md`; each edit names the
finding it answers. The orchestrator checked each remedy against the finding's evidence.

## D8 — A widget's own media is not a package asset

**Ambiguous:** FR-027 says the package loads no asset a developer's widget needs, and
`list_view.html` writes `{{ filter.form.media }}`, which loads a widget's declared script.

**Chosen:** keep writing the form's media.

**Why:** a widget's `Media` is the widget's contract with Django's forms, the same as on any page
that renders a form. The package names no library and ships nothing for it. The project still
loads the library the widget depends on (Tom Select, for django-mvp-forms), as the widget's own
documentation says. **Revisit if** Sam reads FR-027 as excluding form media.

**ADR:** none — Django's own form-media contract, nothing new to record

## D9 — No per-field grow or shrink setting

**Chosen:** the search grows to fill the toolbar row; every other field keeps its width. No
setting for it.

**Why:** Sam called it a nice-to-have, and nothing in the spec asks for it. A setting would be a
new view or filterset option with no case yet. **Revisit if** a project needs a second field to
grow.

**ADR:** none — a decision not to build something; nothing downstream inherits it

## D10 — The table view's order_by message

**Chosen:** on a table view, the import-time refusal of `order_by` points to the table class's own
`order_by`, not to a `SortFilter` (design review SPEC-010). FR-002 asks for an error that points to
the filterset, and a table view drops a `SortFilter` (FR-023), so pointing there would send the
developer to something that does nothing. This is a change of message only.

**ADR:** none — the wording of one error message

## D11 — get_filterset takes an optional class (US-1, T006)

**Decision:** `MVPListViewMixin.get_filterset(filterset_class=None)` builds and caches the
request's filterset; the argument defaults to `get_filterset_class()`.

**Why:** it is the shape of django-filter's own `FilterMixin.get_filterset(filterset_class)`, so a
project's override written for django-filter keeps working, and the table mixin's override (and
every view still composing `FilterView` until T007 refuses them) calls it with the class. The table
mixin's override was changed to that signature and to drop the sort filters only when the
filterset is first built, since the cache now hands the same instance to every caller; T023
still rebuilds it.

**Revisit if:** no caller ever passes the class once US-5 lands.

**ADR:** none — mirrors django-filter's own signature, local to the list mixin

## D12 — The table's own order_by refusal goes with the mixins (US-1, T007)

**Decision:** T007 removes `MVPTableViewMixin.__init_subclass__`'s refusal of `order_by` and
converts the demo's list and table views off `FilterView` and `search_fields`, instead of
leaving those to T023 and T011.

**Why:** once `OrderMixin` is gone no class carries `order_by`, so the table's check
(`if cls.order_by`) raised `AttributeError` for every table view; and `demo/views.py` is imported
by the URLconf, so a demo view the new refusal rejects would fail every request in the suite. The
list mixin's refusal already gives a table view the table-specific `order_by` message, which is
what T023 asked for. The custom-toolbar table page loses its search box until T026 rebuilds it,
because its template draws every filterset field as a select.

**Revisit if:** T023 or T026 needs either back in another shape.

**ADR:** none — an ordering of the build's tasks

## D13 — The custom-toolbar table page reuses the product filterset (US-5, T026)

**Decision:** `CustomToolbarTableView` takes the demo's `ProductFilter` with
`toolbar_filters = ["q", "status", "priority"]`, and its Columns and Export buttons move to
`page.actions`. The page's test, `TestCustomToolbarDemoPage`, sits in
`tests/test_table_layout.py` beside the other demo table page's test.

**Why:** the page's own filters (status, priority) and the search it lost at T007 come back in
the panel without a new filterset outside the task's files (`demo/filters.py` is not one), and
the page shows the list's filterset serving a third page unchanged (SC-002). The block the page
used, `page.controls`, went with T024, and `page.actions` is the documented place for a
project's own buttons on a table page. The page now has a filter modal for the rest of the
filterset, where before it had none. No demo test existed for the page; the one file in the
story's scope that already tests a demo table page is `tests/test_table_layout.py`.

**Revisit if:** Sam wants the page to keep exactly two filters and no modal, which needs a
filterset of its own in `demo/filters.py`.

**ADR:** none — local to one demo page

## D14 — T027 and T028 built by the orchestrator, not dispatched

**Decision:** the orchestrator wrote T027 and T028 itself.

**Why:** the sketch had already built the two demo pages, their menu entries and the Tom Select
loading, so T027 came down to one test file and one seeded name, and the stylesheet rebuild for
T028 changed nothing. A dispatch would have cost more than the work.

**Revisit if:** either task turns out to need more than a test and a line, which would be design
work for an implementer.

**ADR:** none — about how this feature was built, not the code

## D15 — Two pre-existing tests changed outside the retirement table

**Decision:** `tests/test_components/test_icon.py` and `tests/test_components/test_sidebar_boost.py`
are changed. The other six tests the feature changes or deletes are in the plan's retirement table.

**Why:** both changes keep what the test checks. daisy-cotton 0.2's alert draws an icon only
when it is given one, so the icon test now passes `icon`, and it still checks that the icon is
drawn through this package. The language-switcher browser test found its trigger by the label
"Select a language", which the dialog now carries as well since `c-mvp.modal` names its dialog.
It now finds the button by its role. Neither assertion is weaker.

**Revisit if:** daisy-cotton goes back to picking an alert's icon from its variant.

**ADR:** none — about two tests, nothing downstream inherits it

## D16 — Every review finding fixed, not only the blocking ones

**Decision:** the code review returned no critical or high findings, four medium and five low.
All nine are fixed in this pull request (T034–T042). `test_it_offers_no_empty_choice` in
`tests/test_filters.py` is replaced, because it pinned the defect T034 fixes.

**Why:** the maintainer asked for the review's findings to be fixed. Two of the medium findings
break FR-015 and FR-017 on the demo, and one leaves `filter.qs` unscoped where the view scopes
its records.

**Revisit if:** never; it records what this review did.

**ADR:** none — about how this feature was reviewed, nothing downstream inherits it

## D17 — A list view with a filterset no longer overrides `get_queryset()`

**Decision:** `MVPListViewMixin.get()` builds the filterset over `self.get_queryset()` and sets
`object_list` to `filterset.qs`, as django-filter's `BaseFilterView` does. It no longer runs
`ListView`'s `allow_empty` check on a filtered page.

**Why:** building the filterset inside `get_queryset()` over `super().get_queryset()` meant a
view that scoped its own records published an unscoped `filter.qs` to its templates.

**Revisit if:** a consumer needs `allow_empty = False` on a filtered list.

**ADR:** none — follows django-filter's own view, nothing new to record
