# ADR 0002 — Formset rendering is generic; the configured view is not

**Status:** accepted; partly superseded by [ADR 0007](0007-a-row-set-is-declared-as-its-own-class.md)

> **Superseded 2026-08-11, in part.** The paragraph below limiting the configured view to one
> parent and one related set no longer holds: a view now lists as many row set declarations as it
> needs. The rest of this decision stands — rendering is still generic, and no configured view is
> packaged for a standalone formset. The original text is kept because it records why the first
> pass was scoped to one set.

## Decision

`<c-form.formset>` and `<c-form.formset.row>` render any Django formset, anywhere the packaged
form components render. They require nothing but the formset itself, and they know nothing about
parents, foreign keys or saving.

~~`MVPInlineCreateView` and `MVPInlineUpdateView` cover exactly one shape: one parent record with
one related set. A page needing two related sets composes the rendering components and drives the
extra set itself.~~ *(Superseded by ADR 0007.)* No configured view is packaged for a standalone formset, because rendering
already covers that case.

## Why

The two halves have different amounts of decision in them. Rendering a formset has one right
answer that holds everywhere, so it generalises for free. Saving a parent alongside its rows does
not: it needs an order, a transaction boundary, and a rule for attaching new rows to a parent that
did not exist when the page was rendered. That is where a developer benefits from having the
decision made for them, and it is also where a wrong generalisation would be expensive.

Designing a collection API against a page with several related sets was considered and rejected.
Neither the roadmap item nor the tracking issue raised that case, and an abstraction built for a
second implementation that does not exist is the kind this repository's constitution forbids
outright.

## Revisit if

A real page needs two or more related sets and composing the rendering components turns out to be
materially harder than a packaged collection API would be. The shape to reach for then is a list
of formsets on the existing view, not a second view class.
