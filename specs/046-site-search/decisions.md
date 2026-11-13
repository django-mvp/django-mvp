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

**ADR:** to be written at planning, when it is settled whether modelsearch is a dependency of the
package or a guarded integration.

## D2: A kind is anything that answers a query for a request

The issue asks for django-mvp-sphinx's documentation search to be one group among the others, and
modelsearch cannot index a Sphinx build. So the unit is a kind that takes the query and the
request and returns results with a total. A model kind is the ready-made way to build one on
modelsearch, and a function kind is everything else. The documentation search then needs no
special case, and a package can ship a kind the way it ships a mounted app.

## D3: Each kind decides what a request may see

The issue says each source decides what the request may see. A model kind takes a queryset
derived from the request and searches within it, so a record the request may not open is never
listed and never counted. A count that included hidden records would itself leak that they exist.

## D4: No ranking across kinds

The agreed look groups results by kind. Ranking across kinds would need scores comparable between
a database's full-text search and a documentation index, which do not exist, and the grouped
design has no place to show it. The groups follow the settings' order and each kind keeps its own
order. The prototype's hand-over left this to this specification and expected the same answer.

## D5: Narrowing to one kind pages through all of it

In the prototype, narrowing to one kind listed every result at once. A research-data portal can
hold tens of thousands of matching records, so the narrowed page uses the package's existing
pagination instead.

## D6: A misconfigured search fails at start-up

A setting naming a kind nobody registered is a typo the developer wants to hear about once, at
start-up, rather than as a search that silently covers less. A search placed with no kinds would
show a field that can never find anything. Both are system check errors.

## D7: The navbar's search component opens the site search

`c-mvp.actions.search` draws an input wired to nothing today. Once a site search exists, a search
field that does nothing would be a trap, so the navbar's search becomes the way to open it.
Whether the component keeps its name or is replaced, with a breaking entry in the CHANGELOG, is
planning's to decide.

## D8: A kind that fails is not hidden

A kind that raises while searching could be skipped so the other groups still show. That would
hide a broken source from the developer in production, where nobody reads the page closely. The
error goes to Django's error handling like any other view error. A source that is merely empty,
such as a documentation build not yet made, returns no results, which is its own business.

## D9: Kinds carry an optional description, and results carry no colour

The prototype's hints before typing describe each kind in a line ("by title or by a sentence in
them"), so a kind has an optional description. The prototype also tinted one kind's results with
the record's own colour. That is one project's look, so it is left to that project's override of
the result component, not added to the result.

## D10: A query is shortened, not refused

A very long query is cut to a limit before it is searched, as the prototype's field limited it.
Refusing it would show an error for something a reader did by pasting. The limit itself is
planning's.
