# ADR 0043 — A model kind searches only what the request may see, narrowed by primary key

**Status:** accepted

## Decision

`mvp.search.ModelKind.get_queryset(request)` has no default: a model kind must say which records a request may see, and one that does not raises `ImproperlyConfigured`. The kind then searches `model._default_manager.filter(pk__in=get_queryset(request).values("pk"))`, so a record the request may not open is never listed and never counted. The model needs one `index.FilterField` on its primary key's attribute name (`index.FilterField("id")` for the usual primary key), and the start-up check `mvp.E007` reports a model kind whose model lacks it.

## Why

modelsearch searches a narrowed queryset only when every field the narrowing filters on is indexed as a `FilterField`. A visibility rule, often from a permission package, filters on fields the developer may not know about, and it changes as the project changes. Narrowing by primary key means one filter field covers every visibility rule, now and later.

A default that searched every record would be safe only for a developer who remembered to override it, and its failure would show titles and counts to anonymous readers. Making the method required turns that mistake into an error the developer meets at once.

`FilterField("pk")` does not count: modelsearch compares filter fields by attribute name, and the primary key's attribute name is `id`, not `pk`.

## Revisit if

modelsearch learns to filter on fields it has not indexed, or a backend is added that cannot filter by primary key.
