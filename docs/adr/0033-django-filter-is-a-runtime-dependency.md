# ADR 0033 — django-filter is a runtime dependency

**Status:** accepted; reverses the part of R16 that kept django-filter optional

## Decision

`django-filter` is declared in `[project].dependencies` with the range `>=26.1,<27`. A project
adds `django_filters` to its own `INSTALLED_APPS`. The package never edits a project's settings.

A list view takes every search, sort and filter it offers from one django-filter filterset
(FS-041). The search and the sort are the package's own filters, `mvp.filters.SearchFilter` and
`mvp.filters.SortFilter`, and the list view builds the filterset itself. The guarded module
`mvp.integrations.django_filters` and its `MVPFilteredListView` are removed: there is nothing
left to guard.

## Why

Before this, a list page had three ways to narrow or order what it shows: `search_fields` and
`order_by` on the view, and an optional filterset shown in a modal. Each had its own settings,
its own controls and its own rules for what a bad value does. Putting all three behind one
filterset gives one place to declare them, and that place is django-filter's, which projects
already know.

The justification Article VII asks for is that the core list view builds on it. A list view
without django-filter would have no search and no sort, so there is no fallback to degrade to
and no import to guard.

The project lists the app itself because django-filter's range widgets render from its own
templates, and Django finds an app's templates only when the project names the app. This is the
same arrangement as `daisy_cotton` in [ADR 0031](0031-daisy-cotton-is-a-runtime-dependency.md).

The upper bound stops a new major version arriving unannounced. Moving it is a decision made when
that release is tested with this package.
