# Feature Specification: A list page's search, sort and filters come from one filterset

**Feature Branch**: `041-list-filters-from-a-filterset`

**Created**: 2026-10-19

**Status**: Draft

**Serves**: G10 (a consistent UI around the third-party packages projects already rely on, without
extending or replacing them), G3 (a short path from a Django model to a working set of pages,
configured declaratively rather than written by hand), G7 (customization that never dead-ends,
from view configuration through component override to a project's own CSS)

**Roadmap**: R16 (integrations with the packages projects already use). This feature reverses the
item's promise that django-filter never becomes a required dependency.

**Issue**: #536

**Input**: A list page has three separate ways to narrow or order what it shows: a search box
configured on the view, a sort menu configured on the view, and optional django-filter filters
shown in a modal. This feature puts all three behind one django-filter filterset. The package
ships a search filter and a sort filter, and the view settings for search and sort are removed. A
developer names which of the filterset's fields appear in the list toolbar. Every other field goes
into a filter modal opened by the Filter button, and when no field is left over there is no Filter
button. Someone using the page changes a dropdown or a toggle in the toolbar and the list updates.
A multi-select dropdown shows how many values are chosen. A table page places fields the same way
and ignores a sort field, so one filterset can serve both kinds of page.

## Clarifications

### Session 2026-10-19

The coverage scan found five ambiguities. Each was resolved from the intake discussion on #536
and its sibling issues #535 and #541, and from how the list page behaves today. Longer rationale
is in `decisions.md`.

- **Q: What does the package's search filter match?**
  A: The same as the search box today. Each word of the term is matched against every field the
  filter names, ignoring case, and a record matching any word in any field is shown, once. Only
  the first ten words are searched. Recorded as FR-003.

- **Q: What happens to the page number when the reader changes a filter, the search or the sort?**
  A: The list goes back to its first page, because the new result may have fewer pages. Recorded
  as FR-012.

- **Q: What do the two clear actions remove?**
  A: The modal's clear action removes the values of the fields in the modal and keeps the
  toolbar's. The refinements row's clear-all action removes the search and every filter, wherever
  it is drawn. Neither removes the sort. Recorded as FR-016 and FR-017.

- **Q: What does the Filter button's count include?**
  A: Only the applied filters that sit in the modal. A value chosen in the toolbar is already
  visible beside the button, so counting it again tells the reader nothing. Recorded as FR-015.

- **Q: What happens when the address carries a value a filter cannot accept, such as a sort option
  that no longer exists or a choice that was removed?**
  A: That one value is ignored and the list is shown as if it were absent. The other filters still
  apply. The list is never emptied because of a bad value. This is how an unknown sort value is
  treated today. Recorded as FR-009.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer declares a list page's search, sort and filters on one filterset (Priority: P1)

A developer building a product catalogue writes one filterset for their product list. On it they
declare a search over the name, description and category name, a sort with three options, a
status choice, a category multi-select and a date range. They point their list view at the
filterset. The list page now offers all of it: every field appears in the filter modal behind the
Filter button, the list narrows and orders by what the reader picks, and the refinements row shows
what is applied. The view carries no separate search or sort settings, because those no longer
exist.

**Why this priority**: This is the change every other story builds on. It replaces three
mechanisms with one, and a page that never places a field in the toolbar is already complete.

**Independent Test**: Declare a filterset with the package's search filter, the package's sort
filter and two ordinary filters, and point a list view at it. Request the page with values for
each and confirm the list is narrowed and ordered accordingly, the refinements row lists the
search and the two filters but not the sort, and the modal holds every field.

**Acceptance Scenarios**:

1. **Given** a list view whose filterset declares the package's search filter over several fields,
   **When** the page is requested with a search term, **Then** the list shows exactly the records
   in which some word of the term appears in some named field, each record once.
2. **Given** a filterset that declares the package's sort filter with a set of options, **When**
   the page is requested with one option, **Then** the list is in that option's order. **Given**
   an option that names more than one column, **Then** the extra columns decide between records
   that tie on the first, so no record appears on two pages or on none.
3. **Given** the same filterset, **When** the page is requested with a sort value that is not one
   of the options, **Then** the list is shown in its default order and the other filters still
   apply.
4. **Given** a filterset with a search, a sort and two ordinary filters, all set, **When** the page
   renders, **Then** the refinements row lists the search and the two filters, and the sort is not
   among them.
5. **Given** a list view with no filterset, **When** the page renders, **Then** it shows the list
   with no search, sort or filter controls, and the page works as before for everything else.
6. **Given** a list view that still declares one of the removed search or sort settings, **When**
   the project starts, **Then** it is refused with an error that names the setting and says to
   move it into a filterset.
7. **Given** a filterset built by django-filter from a list of model field names, rather than
   declared by hand, **When** it is used on a list view, **Then** its fields behave like any other
   filterset's.

---

### User Story 2 - A developer chooses which filters appear in the toolbar (Priority: P1)

The same developer wants the search, the status choice and the sort in reach without opening
anything, and the rest out of the way. They list those three field names on the view. The toolbar
now draws the search, the status choice and the sort, in that order, beside the result count. The
category and date range stay in the filter modal behind the Filter button. On another list with
only a search and a status choice, the developer lists both, and that page has no Filter button
and no modal, because nothing is left over.

**Why this priority**: This is what #536 asks for, and it is the half of the feature someone using
the site sees first. It depends only on Story 1.

**Independent Test**: With Story 1's filterset, list three field names on the view and render the
page. Confirm those three are drawn in the toolbar in the listed order and are not in the modal,
and the other fields are in the modal. List every field and confirm there is no Filter button and
no modal.

**Acceptance Scenarios**:

1. **Given** a view that lists some of its filterset's fields for the toolbar, **When** the page
   renders, **Then** those fields are drawn in the toolbar in the order listed and every other
   field is drawn in the filter modal.
2. **Given** the same page, **When** it renders, **Then** each field is drawn exactly once, in the
   toolbar or in the modal, and a submitted value is sent once.
3. **Given** a view that lists every field of its filterset for the toolbar, **When** the page
   renders, **Then** there is no Filter button and no filter modal.
4. **Given** a view that lists no fields for the toolbar, **When** the page renders, **Then** every
   field is in the filter modal, as in Story 1.
5. **Given** a view that lists a name its filterset does not have, **When** the page is first
   requested, **Then** it fails with an error that names the field and the filterset.
6. **Given** a view that lists a field the toolbar cannot draw in its compact form, **When** the
   page is first requested, **Then** it fails with an error that names the field and says it
   belongs in the modal.
7. **Given** a narrow screen, **When** the page renders, **Then** the toolbar fields are in the
   toolbar, wrapping onto further rows as needed, and none of them moves into the modal.
8. **Given** a toolbar field, **When** the page renders, **Then** the field carries its filter's
   label as its accessible name, whether or not a label is shown.

---

### User Story 3 - A user narrows a list from the toolbar and the filter modal (Priority: P2)

A person looking for an archived product changes the status dropdown in the toolbar, and the list
updates straight away to archived products. They type a word into the search box and press
Enter, and the list narrows further. They open the filter modal, look at the categories, change
their mind and close it with the close button, and nothing about the list changes. They open it
again, pick a date range and apply it, and the Filter button now shows that one filter in the
modal is applied. The modal's clear action removes the date range and keeps the archived status
and the search. The refinements row's clear-all action removes all three, and the list keeps the
sort they had chosen.

**Why this priority**: It is the experience the first two stories exist for, but a page built
with Stories 1 and 2 already works with a submit button. This story makes it immediate and
predictable.

**Independent Test**: In a browser, on a list page with a toolbar choice field, a toolbar search
and two modal fields, change the toolbar choice and confirm the list updates without pressing
anything else. Open the modal and close it by its close button, by the backdrop and by Escape,
and confirm the list did not change. Apply a modal filter and check the button's count, then use
each clear action and check what remains.

**Acceptance Scenarios**:

1. **Given** a toolbar field that offers a fixed set of values, such as a single choice or a
   toggle, **When** the reader changes it, **Then** the list updates to the new value without any
   further action.
2. **Given** a toolbar field the reader types into, **When** they press Enter in it, **Then** the
   list updates to what they typed.
3. **Given** the filter modal is open with values changed but not applied, **When** the reader
   closes it by its close button, by clicking outside it or by pressing Escape, **Then** the modal
   closes and the list is not updated.
4. **Given** the filter modal, **When** the reader applies it, **Then** the list updates to every
   value in the modal and in the toolbar together.
5. **Given** one applied filter in the modal and one in the toolbar, **When** the page renders,
   **Then** the Filter button's count is one.
6. **Given** applied filters in both places and a chosen sort, **When** the reader uses the
   modal's clear action, **Then** the modal's filters are removed and the toolbar's filters, the
   search and the sort remain.
7. **Given** the same state, **When** the reader uses the refinements row's clear-all action,
   **Then** the search and every filter are removed and the sort remains.
8. **Given** the reader is on a later page of the list, **When** they change a filter, the search
   or the sort, **Then** the list shows its first page.
9. **Given** a page that shows an alert, such as a flash message or the warning on a delete page,
   **When** it renders after this feature, **Then** the alert carries an icon wherever it carried
   one before.

---

### User Story 4 - A user picks several values from a toolbar filter (Priority: P3)

A person wants products from two categories. The category filter sits in the toolbar as a
dropdown button. They open it, tick two categories, and close it, and the list updates to products
in either. The button now tells them that two values are chosen, without their opening it again.

**Why this priority**: It is the control #536 describes for multi-select filters. Without it, a
multi-select filter stays in the modal, which works, so it comes last.

**Independent Test**: List a multi-select filter for the toolbar. In a browser, open its dropdown,
choose two values and close it. Confirm the list updates to records matching either value and the
button reports two chosen. Reload the page and confirm it still reports two.

**Acceptance Scenarios**:

1. **Given** a multi-select filter listed for the toolbar, **When** the page renders, **Then** it
   is drawn as a button that opens a list of its values to choose from.
2. **Given** that dropdown, **When** the reader chooses values and closes it, **Then** the list
   updates to records matching any chosen value.
3. **Given** a multi-select toolbar filter with values chosen, **When** the page renders, **Then**
   the button states how many values are chosen. **Given** none chosen, **Then** it states none.
4. **Given** the dropdown is open, **When** the reader closes it without changing anything,
   **Then** the list is not updated.

---

### User Story 5 - A developer uses one filterset on a list page and a table page (Priority: P2)

A developer has a card list of products for customers and a table of the same products for staff.
They point both views at the same filterset, which declares a sort. On the card list, the sort is
drawn and applied as in Story 1. On the table page, the table's column headers sort the rows, and
the filterset's sort is neither drawn nor applied, with no error. The table page places toolbar
fields the same way the list page does, in its own toolbar panel.

**Why this priority**: Reusing one filterset is the natural thing to do once everything is a
filterset, and a table page that refused a sort field would force a developer to keep two copies.

**Independent Test**: Point a list view and a table view at one filterset that declares a sort, a
search and one filter, listing the search for the toolbar on both. Confirm the list view draws
and applies the sort and the table view does neither, raises nothing and still sorts by its
column headers, and both draw the search in the toolbar and the filter in the modal.

**Acceptance Scenarios**:

1. **Given** a table view whose filterset declares the package's sort filter, **When** the page
   renders, **Then** no sort control is drawn and no error is raised.
2. **Given** the same table view, **When** the page is requested with a value for that sort filter,
   **Then** the value is ignored and the rows follow the table's own ordering.
3. **Given** a table view that lists the sort filter for the toolbar, **When** the page renders,
   **Then** the sort is not drawn there either, and no error is raised.
4. **Given** a table view that lists some filterset fields for the toolbar, **When** the page
   renders, **Then** those fields are drawn in the table's toolbar panel and the rest are in the
   filter modal, as in Story 2.
5. **Given** the same filterset used by a list view, **When** that page renders, **Then** the sort
   is drawn and applied as in Story 1.

---

### Edge Cases

- A filterset whose only field is the sort, with the sort listed for the toolbar: the toolbar
  draws the sort, there is no Filter button, and nothing appears in the refinements row.
- A filterset with no search filter: no search box is drawn anywhere.
- Two search filters on one filterset: each is an ordinary filter with its own field and its own
  refinement. The package treats neither as special.
- A list that is empty with nothing applied: the toolbar is not drawn, as today, and the empty
  state carries its own add action.
- A list emptied by its filters: the toolbar stays, so the reader can change what they applied.
- A field listed twice for the toolbar: it is drawn once, at its first position.
- A value in the address for a field the filterset no longer has: it is ignored.

## Requirements *(mandatory)*

### Functional Requirements

**One filterset (Story 1)**

- **FR-001**: A list view MUST take every search, sort and filter it offers from one django-filter
  filterset. django-filter MUST be a dependency of the package rather than an optional one.
- **FR-002**: The view settings for search and for sort MUST be removed, along with the separate
  filtered list view and the optional django-filter integration module. A view that still
  declares a removed setting MUST be refused when the project starts, with an error that names the
  setting and points to the filterset.
- **FR-003**: The package MUST provide a search filter that matches each word of the term against
  every field it names, ignoring case, shows a record matching any word in any field once, and
  searches only the first ten words.
- **FR-004**: The package MUST provide a sort filter that offers a fixed set of named options with
  labels. An option MAY name several columns, the later ones deciding ties. A value that is not
  one of the options MUST NOT reach the database.
- **FR-005**: The sort MUST NOT count as an applied filter, appear in the refinements row, or be
  removed by either clear action.
- **FR-006**: A list view with no filterset MUST render the list with no search, sort or filter
  controls.
- **FR-007**: A filterset generated by django-filter from model field names MUST work as a declared
  one does.
- **FR-008**: The search, when applied, MUST appear in the refinements row like any other applied
  filter, with its own remove action.
- **FR-009**: A value the address carries that a filter cannot accept MUST be ignored for that
  filter alone. The other filters MUST still apply and the list MUST NOT be emptied because of it.

**Placement (Story 2)**

- **FR-010**: A view MUST be able to name which of its filterset's fields are drawn in the toolbar.
  They MUST be drawn in the order named. Every other field MUST be drawn in the filter modal.
  Each field MUST be drawn once.
- **FR-011**: When no field is left for the modal, the page MUST draw no Filter button and no
  filter modal.
- **FR-012**: Changing a filter, the search or the sort MUST return the list to its first page.
- **FR-013**: A view that names a field its filterset lacks, or a field the toolbar cannot draw in
  compact form, MUST fail on the first request with an error naming the field.
- **FR-014**: Toolbar fields MUST stay in the toolbar at every screen width, wrapping as needed,
  and MUST carry their filter's label as their accessible name.

**Using the page (Story 3)**

- **FR-015**: The Filter button's count MUST include only the applied filters drawn in the modal.
- **FR-016**: The modal's clear action MUST remove the values of the modal's fields and keep the
  toolbar's values, the search and the sort.
- **FR-017**: The refinements row's clear-all action MUST remove the search and every filter and
  keep the sort.
- **FR-018**: A toolbar field with a fixed set of values MUST update the list as soon as it is
  changed. A toolbar field the reader types into MUST update the list when Enter is pressed in it.
- **FR-019**: Closing the filter modal by its close button, by clicking outside it or by Escape
  MUST NOT update the list. Applying it MUST update the list with the modal's and the toolbar's
  values together.
- **FR-020**: Every alert in the package that carried an icon before this feature MUST still carry
  one. The upgrade of the component library this feature needs stops alerts choosing an icon on
  their own.

**Several values (Story 4)**

- **FR-021**: A multi-select filter named for the toolbar MUST be drawn as a button that opens its
  values to choose from, and MUST update the list when it closes with a changed choice.
- **FR-022**: That button MUST state how many values are chosen.

**Table pages (Story 5)**

- **FR-023**: A table view MUST neither draw nor apply the package's sort filter, wherever it is
  placed, and MUST raise no error for it. The table's own column sorting MUST be unaffected.
- **FR-024**: A table view MUST place filterset fields between its toolbar panel and the filter
  modal as FR-010 and FR-011 describe.

### Requirement coverage

| Story | Requirements |
|---|---|
| US1 | FR-001 to FR-009 |
| US2 | FR-010 to FR-014 |
| US3 | FR-012, FR-015 to FR-020 |
| US4 | FR-021, FR-022 |
| US5 | FR-023, FR-024 |

### Key Entities

- **Filterset**: the developer's django-filter class for one model's list. It declares every way
  the list can be narrowed or ordered.
- **Search filter**: a filter the package ships. Matches the words of a term across named fields.
- **Sort filter**: a filter the package ships. Orders the list by one of a fixed set of options.
  Never counts as a filter.
- **Toolbar filters**: the filterset fields a view names for the toolbar.
- **Filter modal**: the dialog behind the Filter button, holding every field not in the toolbar.
- **Refinement**: one applied search or filter, shown in the refinements row with its own remove
  action. The sort is never a refinement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer gets a search, a sort and three filters on a list page, with two of them
  in the toolbar, by writing one filterset and naming two fields on the view, with no template.
- **SC-002**: One filterset class, unchanged, serves a list view and a table view of the same
  model, and neither raises an error.
- **SC-003**: Every way a list can be narrowed or ordered is declared in exactly one place, the
  filterset. The package's public list API has no second place to declare search or sort.
- **SC-004**: On every list and table page in the demo, closing the filter modal without applying
  it leaves the list unchanged, by each of the three ways to close it.
- **SC-005**: Every list page in the demo that offered search or sort before this feature offers
  the same search and sort after it, declared on a filterset.

## Assumptions

- The default size and the Add button's place at the end of the toolbar come from #535 and #541,
  which merge before this feature is built. This feature builds on that toolbar.
- The size of the table page's pager is out of scope and tracked in #547.
- Moving toolbar fields into the modal on narrow screens is out of scope. A field drawn in two
  places would send its value twice.
- Field types the toolbar cannot draw compactly, such as a date range, stay in the modal. Which
  types the toolbar can draw is settled in planning. At least the search, a single choice, a
  toggle, the sort and, with Story 4, a multi-select are among them.
- The removal of the search and sort view settings is a breaking change with no transition
  period. The package is before 1.0, and no package built on it in this organisation uses them.
- The component library the package builds on is upgraded to the release whose dialog closes
  without a form of its own, which a modal inside a filter form needs. That release changes how
  alerts choose icons and drops the space around some inline components.
- A decision record replaces R16's statement that django-filter is never a required dependency.
