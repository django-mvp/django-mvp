# ADR 0001 — Detail views do not take a field list

**Status:** Accepted (2026-08-03)

## Context

`MVPCreateView` and `MVPUpdateView` take `fields = [...]` and hand it to Django's
`modelform_factory`. `MVPDetailView` has no equivalent, and its packaged template rendered a
placeholder, so every project wrote the whole page body itself. The obvious symmetry is to give
the detail view its own `fields` list and render each entry through `c-data-field`, taking the
label from the field's `verbose_name`.

That symmetry was proposed and rejected.

## Decision

`MVPDetailView` takes no field list, and the package renders no field markup on its behalf. The
packaged template supplies the page heading and the edit and delete links, and leaves the body to
the project.

## Rationale

- The symmetry with the form views is superficial. A form is a plumbing problem — widgets,
  validation, error display, the POST round-trip — and `fields` buys a project all of it. A list
  page is one uniform row repeated. A detail page is neither. It is layout, and layout is where an
  application's design lives, so it is the page a project writes itself.
- Django ships `DetailView` with no template of its own. Across the wider ecosystem, generic
  renderers exist for forms and for tables, and not for detail pages. That asymmetry tracks where
  the repetition actually is.
- A field list is public API with a queue of follow-on requests behind it: fields that are not
  concrete model fields, fieldsets, per-field label overrides, choice display, relation rendering,
  ordering, and a configurable empty value. Each is reasonable alone, none can be withdrawn once
  shipped, and all of them would arrive after 1.0.0.
- Article XI already answers the general form of this question. Where a consumer needs more control
  than component attributes give, the answer is a template override, not a wider attribute surface.
  A detail page body is that case.

## Consequences

- A project that wants field-by-field presentation composes it from `c-data-field` inside its own
  `page.content` override. `demo/templates/demo/product_detail.html` is the worked example.
- The packaged detail page is deliberately empty below the heading. That is the finished behaviour,
  not a placeholder awaiting a renderer.
- Requests to add `fields`, `fieldsets`, or an equivalent to a detail view are declined by reference
  to this record. Reopening it needs a case that defeats the reasoning above, not a restatement of
  the symmetry argument.
