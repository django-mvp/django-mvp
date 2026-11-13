# Decisions: Search the whole site from the navbar

Rationale for the ambiguities settled while writing the specification, each resolved from the
issue, its comment and the prototype hand-over. How the feature is built is not settled here:
that is research and planning, with the notes in `planning-notes.md`.

## D1: django-mvp supports modelsearch

The issue's comment asks for a survey and one package that suits every kind of project built on
django-mvp. `research.md` holds the survey. modelsearch is the only maintained candidate that
searches both SQLite and PostgreSQL with their own full-text search and no server, is tested on
Django 6, and searches a queryset already narrowed to a request. It is maintained by the Wagtail
team and Wagtail depends on it. django-watson fits the shape of the issue best but has had no
release since January 2023. django-haystack needs a search server for every project.
`django.contrib.postgres.search` is PostgreSQL only.

**ADR:** docs/adr/0042-modelsearch-is-the-supported-search-package.md

## D2: A kind is anything that answers a query for a request

The issue asks for django-mvp-sphinx's documentation search to be one group among the others, and
modelsearch cannot index a Sphinx build. So the unit is a kind that takes the query and the
request and returns results with a total. A model kind is the ready-made way to build one on
modelsearch, and a function kind is everything else. The documentation search then needs no
special case, and a package can ship a kind the way it ships a mounted app.

**ADR:** none — the shape of the kind API, documented in docs/developer/search.md

## D3: Each kind decides what a request may see

The issue says each source decides what the request may see. A model kind takes a queryset
derived from the request and searches within it, so a record the request may not open is never
listed and never counted. A count that included hidden records would itself leak that they exist.

**ADR:** none — a requirement of the kind API, documented in docs/developer/search.md

## D4: No ranking across kinds

The agreed look groups results by kind. Ranking across kinds would need scores comparable between
a database's full-text search and a documentation index, which do not exist, and the grouped
design has no place to show it. The groups follow the settings' order and each kind keeps its own
order. The prototype's hand-over left this to this specification and expected the same answer.

**ADR:** none — local to this feature's presentation

## D5: Narrowing to one kind pages through all of it

In the prototype, narrowing to one kind listed every result at once. A research-data portal can
hold tens of thousands of matching records, so the narrowed page uses the package's existing
pagination instead.

**ADR:** none — local to this feature's results page

## D6: A misconfigured search fails at start-up

A setting naming a kind nobody registered is a typo the developer wants to hear about once, at
start-up, rather than as a search that silently covers less. A search placed with no kinds would
show a field that can never find anything. Both are system check errors.

**ADR:** none — system checks, documented in docs/developer/search.md

## D7: The navbar's search component opens the site search

`c-mvp.actions.search` draws an input wired to nothing today. Once a site search exists, a search
field that does nothing would be a trap, so the navbar's search becomes the way to open it.
Whether the component keeps its name or is replaced, with a breaking entry in the CHANGELOG, is
planning's to decide.

**ADR:** none — a component change recorded in the CHANGELOG

## D8: A kind that fails is not hidden

A kind that raises while searching could be skipped so the other groups still show. That would
hide a broken source from the developer in production, where nobody reads the page closely. The
error goes to Django's error handling like any other view error. A source that is merely empty,
such as a documentation build not yet made, returns no results, which is its own business.

**ADR:** none — local to this feature

## D9: Kinds carry an optional description, and results carry no colour

The prototype's hints before typing describe each kind in a line ("by title or by a sentence in
them"), so a kind has an optional description. The prototype also tinted one kind's results with
the record's own colour. That is one project's look, so it is left to that project's override of
the result component, not added to the result.

**ADR:** none — local to this feature

## D10: A query is shortened, not refused

A very long query is cut to a limit before it is searched, as the prototype's field limited it.
Refusing it would show an error for something a reader did by pasting. The limit itself is
planning's.

**ADR:** none — local to this feature

## D11: modelsearch is a runtime dependency, not a guarded integration

A guarded integration would spare a site whose only kind is a documentation index one install.
That install is small and harmless: modelsearch is pure Python, needs only `django-tasks`, and
creates no tables unless a project lists it in `INSTALLED_APPS`, which only a project with a
model kind does. A guarded module would add an import guard, a second documentation path and an
error a developer meets the first time they write a model kind. ADR 0033 made the same call for
django-filter.

**ADR:** docs/adr/0042-modelsearch-is-the-supported-search-package.md

## D12: A model kind narrows by primary key

modelsearch searches a narrowed queryset only when every field it filters on is indexed as a
`FilterField`, and a visibility queryset from a permission package filters on fields the
developer may not even know about. The model kind therefore searches
`model.objects.filter(pk__in=visible.values("pk"))`: one `FilterField` on the primary key covers
every visibility rule. A system check reports a model kind whose model lacks it, or is not
indexed, or a model kind registered without `modelsearch` installed. Checked on SQLite and
PostgreSQL (`research.md`, note 6).

**ADR:** docs/adr/0043-a-model-kind-narrows-by-primary-key.md

## D13: Completion is the fallback, whole-word search the default

modelsearch's completion searches only the fields marked `AutocompleteField` and does not stem.
Using it always would stop a record being found by its body. The model kind runs whole-word search
first and, when that finds nothing and the model has completion fields, runs completion on the
same query. A partly typed last word then still finds a record by its title (FR-009).

**ADR:** none — a behaviour of the model kind, documented in docs/developer/search.md

## D14: Kinds are registered from `AppConfig.ready()`, never autodiscovered

`mvp.search.register()` is called where Django documents registration, in an app's `ready()`.
Autodiscovering a `search` module in every installed app would import modules that already exist
for other reasons, such as django-mvp-sphinx's `mvp_sphinx.search`. A package ships a kind class
and the host registers an instance of it, as it mounts a mounted app.

**ADR:** none — follows the existing mounted-app pattern, documented in docs/developer/search.md

## D15: PostgreSQL is checked by hand, SQLite by the suite

The test suite runs on SQLite, as the package's CI does. The model kind's queries are run against
PostgreSQL by hand at convergence and recorded in the pull request, and modelsearch's own CI runs
every backend. A PostgreSQL service in CI for one feature would cost every pull request a database
start.

**ADR:** none — local to this feature's verification

## D16: A kind's label and description are public

Every reader sees every active kind's label and description in the hints, and its name with a
count on the results page, including a kind whose records that reader may never open. Records are
scoped by the request (D3), so this discloses only that a kind exists. A kind that hides itself
from a request would be a change to the specification, and nothing in the request asks for one.
`docs/developer/search.md` says a kind's label is public.

**ADR:** none — local to this feature, documented in docs/developer/search.md

## D17: Design review outcome

One verified high finding, a query holding a double quote crashing the SQLite search, is fixed in
the plan: the model kind removes double quotes before searching. The model kind's visibility method
lost its default, so a kind cannot list every record by omission. The narrow button follows
`mvp-mobile-only`, the registry is one class, the PostgreSQL run is a task, and the test settings,
fixtures and smoke test are planned for. The disclosure of kind names is accepted as D16.

**ADR:** none — a record of this feature's design review
