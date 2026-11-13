# ADR 0042 — modelsearch is the supported search package, as a runtime dependency

**Status:** accepted

## Decision

The site search (`mvp.search`) is an interface on top of [modelsearch](https://github.com/wagtail/django-modelsearch), and django-mvp builds no search engine of its own. `modelsearch` is declared in `[project].dependencies` with the range `>=1.3.2,<2`. A project that registers a model kind adds `modelsearch` to its own `INSTALLED_APPS`, and the start-up check `mvp.E008` reports a model kind registered without it. A source modelsearch cannot index, such as a documentation build, is a kind of its own: a function, or a `Kind` subclass, that answers a query for a request.

## Why

Several Django search packages were compared before this was settled: modelsearch, django-watson, django-haystack, `django.contrib.postgres.search`, django-elasticsearch-dsl and django-opensearch-dsl. The search has to suit every kind of project built on django-mvp, from demos and small apps on SQLite to research-data portals on PostgreSQL. modelsearch is the only maintained candidate that searches both databases with their own full-text search and needs no search server, it is tested on the Django versions this package supports, and it searches a queryset already narrowed to what a request may see. It is maintained by the Wagtail team, and Wagtail itself depends on it. A project that outgrows its database moves to Elasticsearch or OpenSearch through modelsearch's own settings.

django-watson fits the shape of the search closely but has had no release since January 2023. django-haystack needs a search server for every project. Django's PostgreSQL search does nothing on SQLite.

modelsearch is a plain dependency rather than a guarded integration because the install is small and harmless: it is pure Python, its only other requirement is `django-tasks`, and it creates no tables unless a project installs the app. A guarded module would add an import guard and a second documentation path for no gain. [ADR 0033](0033-django-filter-is-a-runtime-dependency.md) made the same call for django-filter.

## Revisit if

modelsearch stops being maintained, or stops supporting a database or Django version this package supports.
