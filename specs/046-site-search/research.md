# Research: Search the whole site from the navbar

This is the survey the specification rests on: which Django search package django-mvp supports.
The rest of the research (how the interface is built on it) belongs to planning and answers the
notes in `planning-notes.md`.

## What the package has to suit

The package is chosen for every kind of project built on django-mvp, checked against their
settings on 2026-11-13 rather than assumed:

| Kind of project | Database | What it searches |
|---|---|---|
| django-mvp itself, its family packages and their demos | SQLite | the demo's own models |
| Research-data portals built on FairDM | PostgreSQL with PostGIS, already using `django.contrib.postgres` | datasets, samples, measurements, contributors, literature |
| A site with mounted documentation and its own catalogue of records | SQLite | documentation pages from a Sphinx build, and its own records |
| Smaller apps | SQLite in development, PostgreSQL in production, through `DATABASE_URL` | their own records |

So the package must:

1. search both SQLite and PostgreSQL well, with no search server to run,
2. work on Django 5.2, 6.0 and 6.1, the versions django-mvp supports,
3. search a queryset the developer has already narrowed to what a request may see,
4. return a count and a slice cheaply, for a group's total and its first few results,
5. leave room beside it for a source it cannot index, such as a documentation index built by
   Sphinx, which is already searchable through django-mvp-sphinx's own search,
6. be well maintained and widely used.

## The candidates

Measured on 2026-11-13 from PyPI, pypistats and GitHub.

| Package | Latest release | Activity | Downloads last month | Django 6 | SQLite | PostgreSQL | Needs a server |
|---|---|---|---|---|---|---|---|
| **modelsearch** 1.3.2 | 2026-08-11 | commits 2026-09-11, Wagtail team | 525,104 | tested on 6.0 and Django main | FTS5 | full-text search | no (Elasticsearch and OpenSearch optional) |
| django-watson 1.6.3 | 2023-01-14 | last push 2024-08-14 | 131,947 | not declared (classifiers stop at Python 3.10) | `LIKE` only, no full-text | full-text search | no |
| django-haystack 3.4.0 | 2026-06-04 | commits 2026-11-04, 585 open issues | 259,839 | tested on 6.0 and 6.1 | none | none | yes: Solr, Elasticsearch below 8, Whoosh or Xapian |
| `django.contrib.postgres.search` | ships with Django | Django | – | yes | no | full-text search | no |
| django-elasticsearch-dsl 9.0 | 2025-07-23 | last push 2025-07-23 | 335,518 | not declared (stops at 5.2) | no | no | yes: Elasticsearch |
| django-opensearch-dsl 0.8.0 | 2025-11-24 | – | – | not declared (stops at 5.2) | no | no | yes: OpenSearch |
| Others found (django-pg-search, django-simple-search, django-search-views) | 2017 to 2018 | abandoned | – | – | – | – | – |

### modelsearch

Wagtail's search, used in Wagtail since 2014 and extracted into its own package in March 2025.
Wagtail 8.1 (2026-11-02) depends on it (`modelsearch>=1.3.2,<1.4`), so it is maintained for
Wagtail's whole user base. BSD-3-Clause.

- **Indexing**: a model inherits `modelsearch.index.Indexed` and lists `search_fields`
  (`SearchField` with a boost, `AutocompleteField`, `FilterField`, `RelatedFields`). Signals keep
  the index current, and `rebuild_modelsearch_index` rebuilds it.
- **Querying**: `.search()` and `.autocomplete()` on any queryset of the model, through
  `SearchableQuerySetMixin`. Results support `count()` and slicing, and work with Django's
  paginator and django-filter.
- **Backends**: chosen from `DATABASES["default"]`: PostgreSQL full-text search, SQLite FTS5,
  MySQL and MariaDB full-text search, with a `LIKE` fallback. Elasticsearch 7 to 9 and OpenSearch
  2 and 3 by the `MODELSEARCH_BACKENDS` setting. A FairDM portal's PostGIS engine reports the
  `postgresql` vendor, so it gets the PostgreSQL backend.
- **What a request may see**: the developer narrows the queryset first and searches it.
  Every field the narrowing filters on must be indexed as a `FilterField`, or the search raises
  `FilterFieldError`.
- **A source it cannot index**: none of its own. It indexes Django models only. The
  documentation index is searched by django-mvp-sphinx, so django-mvp's interface must take a
  plain function as a kind (D2).
- **Costs**: depends on `django-tasks` (`>=0.7,<0.13`), the backport of Django's tasks framework,
  used to offload index updates. Its default backend runs them immediately. A model from a package
  the developer does not own cannot be indexed without changing that model.

### django-watson

The closest in shape to what the issue describes: models are registered from outside
(`watson.register(Model, fields=...)`), every model is held in one table, and `watson.search()`
takes querysets to limit what is searched. It ran on Django 6.1 against SQLite in the check below.
It is not chosen because it is no longer maintained: no release since January 2023, no push since
August 2024, 26 open issues, and it declares no Django version newer than its 2023 release
supported. On SQLite, the database most of these projects develop on, it falls back to `LIKE`
with no full-text search. A dependency of the shell that is already unmaintained breaks
the condition the issue sets, "well supported".

### django-haystack

Well established and still released, but it needs a separate search engine for every project.
It has no backend for the database a project already has, so every small app and every demo
would need Solr, Elasticsearch below version 8, Whoosh (unmaintained since 2016) or Xapian. That
rules it out for the smaller apps and the family's demos.

### `django.contrib.postgres.search`

Good full-text search with nothing to install, but PostgreSQL only. The family's demos and the
documentation site run on SQLite. modelsearch's PostgreSQL backend is built on the same
PostgreSQL features, so a portal loses nothing by going through modelsearch.

### django-elasticsearch-dsl and django-opensearch-dsl

Each needs a search server and neither declares Django 6. modelsearch reaches the same servers by
setting, for a project that outgrows its database's search.

## Choice

**modelsearch.** It is the only maintained package that searches both SQLite and PostgreSQL with
their own full-text search and no server, it is tested on the Django versions django-mvp
supports, it searches a queryset already narrowed to a request, and a project that outgrows its
database moves to Elasticsearch or OpenSearch by settings alone. It is carried by Wagtail. What
it cannot index, such as a documentation build, plugs into django-mvp's interface as a function
kind. Recorded as D1 in `decisions.md`.

## Assumptions checked

Run on 2026-11-13 in throwaway environments.

| Assumption | Result |
|---|---|
| modelsearch indexes and searches on SQLite with FTS5 on Django 5.2, 6.0 and 6.1 | Holds. 5.2.19, 6.0.10 and 6.1.3 each chose `SQLiteSearchBackend`. |
| modelsearch indexes and searches on PostgreSQL | Holds on PostgreSQL 17 (PostGIS image) with Django 6.1.3: `PostgresSearchBackend`. |
| A queryset narrowed first is searched within the narrowing, and its count and slice work | Holds. Of seven matching records, four were public: `filter(public=True).search(...)` counted four and sliced the first three, and the unfiltered search counted seven. |
| `.autocomplete()` finds the beginning of a word | Holds. "hea" found the four public "Heat flow" records. |
| Narrowing on a field not indexed as a `FilterField` | Raises `FilterFieldError`. This is a real constraint on visibility querysets, handed to research in `planning-notes.md`. |
| django-watson runs on Django 6.1 | Holds on SQLite: register, search and queryset limit all worked. Not chosen for maintenance reasons. |
| The installed daisy-cotton's `c-modal` takes a `placement` of `top`, as the prototype's dialog uses | Holds: `placement` accepts top, middle, bottom, start and end. |
| `c-mvp.actions.search` exists and is the inert navbar input the issue describes | Holds: it draws an input with no name, no form and no handler, and `docs/configuration.md` says so. |
| django-mvp-sphinx's documentation search answers a query on its own | Holds: `mvp_sphinx.search.DocsSearch(build).results(query)` returns each hit's title, path, anchor and passage, and the prototype used it as one group. |
