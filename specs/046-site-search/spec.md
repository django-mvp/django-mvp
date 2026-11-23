# Feature Specification: Search the whole site from the navbar

**Feature Branch**: `046-site-search`

**Created**: 2026-11-13

**Status**: Draft

**Serves**: G10 (a consistent UI around the third-party packages projects already rely on,
without extending or replacing them), G1 (a complete, responsive application shell that a project
configures rather than builds)

**Roadmap**: none. No roadmap item covers a search across the whole site. This may be a gap in the
roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/666

**Input**: A project built on django-mvp usually holds several kinds of thing a reader looks for:
documentation pages mounted with django-mvp-sphinx, and records from the project's own models.
Today the only search in the navbar is django-mvp-sphinx's, which searches the documentation and
appears only on documentation pages, and django-mvp's own `c-mvp.actions.search` is an input wired
to nothing. A reader on any other page has no search, and a search on a documentation page never
finds a record.

After this feature, a reader opens one search from the navbar on any page and finds every kind of
thing the site holds, grouped by kind. A developer decides what those kinds are: records of their
own models, made searchable with modelsearch, the established Django search package django-mvp
supports, and any other source that can answer a query, such as a documentation index.
django-mvp provides the interface on top of the search package. It does not become a search
engine. The choice of modelsearch, and the survey behind it, is recorded in `research.md` and
`decisions.md`.

The look is agreed and comes from a prototype: a search field in the navbar on a wide screen, a
button on a phone, a dialog that answers as the reader types, and a results page. How it is built
is left to research and planning, with the notes in `planning-notes.md`.

## Clarifications

### Session 2026-11-13

All answered from the issue, its comment and the prototype hand-over. The reasoning for each is in
`decisions.md`.

- Q: Which search package does django-mvp support? → A: modelsearch, extracted from Wagtail and
  maintained by its team. It searches SQLite and PostgreSQL with their own full-text search, needs
  no search server, and can move to Elasticsearch or OpenSearch by setting alone (D1).
- Q: Is a source the package cannot index, such as a documentation index, a second-class kind? →
  A: No. A kind is anything that answers a query for a request. A model kind is one ready-made way
  to build one (D2).
- Q: Who decides what a reader may see? → A: Each kind, from the request it is given. A model kind
  searches only the records the developer's request-aware queryset returns (D3).
- Q: Are results ranked across kinds? → A: No. Results are grouped by kind in the order the
  settings give, and each kind keeps its own order (D4).
- Q: How many results does one kind show on the results page when the reader narrows to it? → A:
  All of them, a page at a time (D5).
- Q: What happens when the settings name a kind nobody registered, or the search is placed with no
  kinds? → A: Start-up reports it as an error (D6).
- Q: What becomes of the inert `c-mvp.actions.search`? → A: The navbar's search becomes the way
  to open the site search. Nothing is left that looks like a search and does nothing (D7).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer offers the kinds of thing their site's search finds (Priority: P1)

A developer building on django-mvp makes their site searchable. They register each kind of result
once, with a label, an icon and an optional line describing what it covers. A kind is either a
model they have made searchable with modelsearch, together with how to get the records a request
may see, or any function that takes the query and the request and returns results, each with a
title, an address, a short line saying where it sits and an optional passage. A package can ship
a ready-made kind, such as a documentation index, and the developer chooses whether their site
uses it. In settings they choose which kinds the navbar search uses and in what order. They mount
the search's addresses and place its components in the navbar, the way they place the other
navbar actions.

**Why this priority**: Nothing can be searched until a kind exists. This is also where every
safeguard on what a reader may see is decided.

**Independent Test**: In a test project, register a model kind and a function kind, name them in
settings, and call the search with a query and a request: the results come back grouped in the
settings' order, each limited to what that request may see.

**Acceptance Scenarios**:

1. **Given** a model made searchable with modelsearch and registered as a kind, **When** the
   search runs a query that matches some of its records, **Then** those records are returned
   under that kind, each with its title, its address and its where line.
2. **Given** a model kind whose queryset for a request holds only the records that request may
   open, **When** a reader whose request excludes a matching record searches, **Then** that record
   is neither listed nor counted.
3. **Given** a kind registered as a function of the query and the request, **When** the search
   runs, **Then** the function's results are returned as one group beside the model kinds, with
   the same parts as any other result.
4. **Given** a kind shipped by an installed package, **When** the developer does not name it in
   settings, **Then** the site's search never runs it.
5. **Given** settings that name three registered kinds in an order, **When** the search runs,
   **Then** the groups come back in that order, and a registered kind the settings leave out is
   not run.
6. **Given** no setting naming kinds, **When** the search runs, **Then** every registered kind is
   used, in the order they were registered.
7. **Given** settings that name a kind nobody registered, **When** the project starts, **Then** a
   system check reports the unknown name as an error.
8. **Given** the search placed in the navbar and no kind registered, **When** the project starts,
   **Then** a system check reports that the search has nothing to search.
9. **Given** a model kind with a field marked for completion, **When** the query holds only the
   beginning of a word in that field, **Then** records whose field has a word starting that way
   are among the results.
10. **Given** a kind that names its own page for the rest of its results, such as the model's list
    page searched for the same words, **When** a group has more results than are shown, **Then**
    the link to the rest goes to that page instead of the results page narrowed to the kind.
11. **Given** a project on SQLite and a project on PostgreSQL, **When** each searches the same
    records, **Then** both find them with no search server running.

---

### User Story 2 - A reader searches the whole site from any page (Priority: P1)

A reader on any page of the site opens the search from the navbar, or from the keyboard with
Ctrl K, ⌘ K on a Mac, or `/`. Before they type, the search says what kinds of thing it can find.
As they type, results arrive grouped by kind, each group with its count and a link to the rest of
it, and a link to every result. They move through the results with the arrow keys, open one with
Enter, and close the search with one press of Esc. When nothing is highlighted, Enter opens the
results page, which lists every group and can be narrowed to one kind to see all of its results.

**Why this priority**: This is what the feature is for. Without it the kinds a developer
registers reach nobody.

**Independent Test**: In the demo, on a page that is not a documentation page, press Ctrl K, type
a word that matches records of two kinds, move to a result of the second kind with the arrow keys
and press Enter: that record's page opens.

**Acceptance Scenarios**:

1. **Given** any page drawn by the app shell with the search placed in its navbar, **When** the
   reader activates the navbar's search, **Then** the search dialog opens with its field focused,
   at every screen width.
2. **Given** any page with the search placed, **When** the reader presses Ctrl K, or ⌘ K on a
   Mac, **Then** the search dialog opens, including while focus is in another field.
3. **Given** focus is not in a text field, **When** the reader presses `/`, **Then** the search
   dialog opens. **Given** focus is in a text field, **When** they type `/`, **Then** the
   character is typed and the dialog stays closed.
4. **Given** the dialog is open with an empty field, **When** the reader looks at it, **Then** it
   lists each kind the search covers, with its label and its description when it has one.
5. **Given** the reader types a query, **When** they pause, **Then** the dialog shows the matching
   results grouped by kind, without a page load, each group with the total it holds, a few of its
   results and, when it holds more, a link to the rest.
6. **Given** the reader keeps typing, **When** an earlier answer arrives after a later one,
   **Then** the dialog shows the results for what is in the field now.
7. **Given** results in the dialog, **When** the reader presses the down and up arrows, **Then**
   the highlight moves through every result and link in order, and the field keeps focus.
8. **Given** a highlighted result, **When** the reader presses Enter, **Then** that result's
   address opens. **Given** nothing highlighted, **When** they press Enter, **Then** the results
   page opens for the query.
9. **Given** the dialog is open with text in its field, **When** the reader presses Esc once,
   **Then** the dialog closes and focus returns to where it was before it opened.
10. **Given** a query that matches nothing, **When** the dialog answers, **Then** it says that
    nothing was found for that query.
11. **Given** the results page for a query, **When** it loads, **Then** it lists every kind with
    its count, shows the groups holding results, and offers a way to narrow to each kind and back
    to every kind.
12. **Given** the results page narrowed to one kind, **When** that kind holds more results than
    one page shows, **Then** the reader moves through all of them with the package's pagination.
13. **Given** the results page with an unknown kind in its address, **When** it loads, **Then**
    it shows every kind, as if none was named.
14. **Given** a reader who is not signed in, **When** they search, **Then** the search works, and
    each kind shows them only what a reader who is not signed in may open.
15. **Given** a title, where line or passage holding markup, **When** it is shown, **Then** it is
    shown as text and never interpreted as markup.
16. **Given** the dialog and the results page, **When** they are read by assistive technology,
    **Then** the field, the list of results and the highlighted result carry the roles and states
    of the WAI-ARIA combobox and dialog patterns.

---

### Edge Cases

- A query of only spaces is treated as empty: the dialog shows the kinds it covers and the
  results page shows its field with no results.
- A very long query is shortened to the package's limit before it is searched, rather than
  refused.
- A kind whose results are empty for a query is left out of the dialog. The results page still
  lists it, with a count of nought, so the reader can see it was searched.
- A kind that raises an error while searching is not hidden: the error reaches Django's error
  handling like any other view error, so the developer learns of it (D8).
- A model the developer cannot change, from a package they do not own, cannot be indexed by
  modelsearch. It can still be a kind, through a function that searches it another way.
- The search works the same on a page of a mounted app as on any other page of its host.
- A documentation index that is missing or not yet built gives no results for its kind, without
  stopping the other kinds. That is the documentation package's behaviour and is not specified
  here.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A developer MUST be able to register a kind of result under a name, with a label,
  an icon and an optional description, all translatable. (US1)
- **FR-002**: A kind MUST be either a model made searchable with modelsearch, with a way to get
  the records a request may see, or a function that takes the query and the request and returns
  results. (US1)
- **FR-003**: Every result MUST carry a title, an address and a where line, and MAY carry a
  passage. (US1)
- **FR-004**: A kind MUST return the total it holds for a query as well as the results asked
  for, so a group can show its count and whether more exist. (US1)
- **FR-005**: A model kind MUST search only within the records its request-aware queryset
  returns, so a record the request may not open is never listed or counted. (US1)
- **FR-006**: An installed package MUST be able to ship a kind that a project's search uses only
  when the project names it. (US1)
- **FR-007**: A setting MUST choose which registered kinds the search uses and in what order. With
  no setting, every registered kind is used in registration order. (US1)
- **FR-008**: A system check MUST report as an error a setting that names an unregistered kind,
  and the search placed with no kind registered. (US1)
- **FR-009**: A model kind MUST find a record by the beginning of a word in a field the developer
  marks for completion. (US1)
- **FR-010**: A kind MAY name its own address for the rest of its results. Otherwise the rest is
  the results page narrowed to that kind. (US1)
- **FR-011**: The search MUST work on SQLite and PostgreSQL with no search server, and on any
  backend modelsearch supports by its settings alone. (US1)
- **FR-012**: The package MUST provide the search's addresses for a project to mount, and as
  components a navbar field for wide screens, a navbar button for narrow ones, the dialog and the
  results page, for the project to place. (US1, US2)
- **FR-013**: The search dialog MUST open from the navbar's search, from Ctrl K or ⌘ K anywhere
  on the page, and from `/` when focus is not in a text field. (US2)
- **FR-014**: With an empty field, the dialog MUST list the kinds the search covers. (US2)
- **FR-015**: As the reader types, the dialog MUST show results grouped by kind in the settings'
  order, each non-empty group with its total, a few results, a link to the rest when there are
  more, and a link to the results page, always for the field's current text. (US2)
- **FR-016**: The arrow keys MUST move a highlight through the dialog's results and links while
  the field keeps focus. Enter MUST open the highlighted one, or the results page when none is.
  (US2)
- **FR-017**: One press of Esc MUST close the dialog and return focus to where it was. (US2)
- **FR-018**: The dialog and the results page MUST say when a query found nothing. (US2)
- **FR-019**: The results page MUST list every kind with its count, show the groups that hold
  results, narrow to one kind and back, page through all of one kind's results, and treat an
  unknown kind as none. (US2)
- **FR-020**: The search MUST be available to readers who are not signed in, each kind deciding
  what they see. (US2)
- **FR-021**: Every part of a result MUST be escaped by Django's template layer. (US2)
- **FR-022**: The dialog and the results page MUST follow the WAI-ARIA combobox and dialog
  patterns for roles, states and focus. (US2)
- **FR-023**: Results MUST NOT be ranked across kinds. Each kind keeps its own order. (US1, US2)
- **FR-024**: The navbar's existing search component MUST open the site search rather than draw an
  input wired to nothing. (US2)
- **FR-025**: The documentation and the demo MUST show a model kind and a function kind in use,
  and how a package ships a kind. (US1, US2)

### Key Entities

- **Kind**: one group of results a search can return. Has a name, a label, an icon, an optional
  description and optionally its own address for the rest of its results. Either a model kind or a
  function kind.
- **Result**: one thing a reader can open. Has a title, an address, a where line and an optional
  passage.
- **Group**: one kind's answer to one query for one request: its results, the total it holds and
  the address of the rest.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the demo, a reader on any page reaches records of two different kinds from the
  same search, without first going to another page.
- **SC-002**: Across the acceptance tests, no result is listed or counted for a request that may
  not open it.
- **SC-003**: A developer makes one of their models a kind with one registration and one settings
  entry, writing no template and no view.
- **SC-004**: A reader opens the search, reaches any result and opens it, or closes the search,
  with the keyboard alone, and closes it with a single Esc.
- **SC-005**: The same search runs on SQLite and on PostgreSQL with no search server installed.
- **SC-006**: A source modelsearch cannot index, such as a documentation index, is a kind with no
  change to django-mvp.

## Assumptions

- modelsearch is the search package django-mvp supports. A developer indexes their models the way
  modelsearch documents, and django-mvp provides the interface. The survey is in `research.md`.
- The records a reader may see are expressed by the developer as a queryset derived from the
  request. Object-level permission packages that produce querysets fit this. How a visibility
  queryset that filters on fields modelsearch has not indexed is handled is a question for
  research (`planning-notes.md`).
- django-mvp-sphinx's side, offering its documentation search as a kind, is
  https://github.com/django-mvp/django-mvp-sphinx/issues/127 and is not part of this
  specification. This specification defines how a source plugs in.
- Results are not cached and nothing is stored beyond what modelsearch keeps in its own index.
- The look, the wording and the hints come from the prototype and are ported, not specified here.
