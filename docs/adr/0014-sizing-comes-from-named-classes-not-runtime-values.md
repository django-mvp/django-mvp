# 0014 — Sizing comes from named classes, never a value supplied at runtime

**Status:** accepted

**Date:** 2026-08-17

## Context

The column styling helpers needed a way to cap how wide a column may get. The obvious shape is to
let the table author state the number — `max_width="20ch"` — and put it in the element's `style`
attribute. The table component already did exactly that with a `min_height` attribute, so there
was a precedent in the package to copy.

Three separate things are wrong with it, and they are wrong independently.

The first is Article V. A value interpolated into rendered markup by hand is the pattern the
article exists to refuse, and the value's origin does not change the shape of the mechanism. A
table class is project code today; the same attribute is one refactor away from carrying something
a request supplied.

The second is Article XI. An arbitrary width is a raw utility with a different spelling. The
article's position is that a component's attributes are the supported surface and that a consumer
needing more reaches for a template override, not a wider attribute.

The third is mechanical and decides the question on its own. The stylesheet is built by scanning
templates for class names. A class assembled from a value known only at render time is never seen
by that scan, so it is never emitted, so it does not exist in the shipped CSS. The only versions
that work are a named set the scan can find or a safelist entry per possible value, and the second
is the first with extra steps.

## Decision

Sizing the package exposes comes from a fixed set of named classes. No dimension reaches markup as
a value supplied at runtime, in a `style` attribute or interpolated into a class name.

The table component's `min_height` attribute is removed rather than reproduced. It was the same
pattern, and a height floor inside a container that now takes its height from its parent
contradicts itself anyway.

## Consequences

An author who wants a width outside the named set writes their own CSS, which is the escape hatch
Article VII of the docs model already points at and which does not require the package to support
an unbounded surface.

Removing `min_height` is a public API change. The package is pre-1.0, Article XVI allows it
between minor versions, and it is in the changelog.

## Alternatives considered

**Safelisting a range of widths.** Emits dozens of rules nobody uses to serve a case a named set
already covers, and still caps the range — so it buys nothing over naming the set, and costs bytes
in every consumer's stylesheet.

**Passing the value through a CSS custom property** set in a `style` attribute. Sidesteps the
build-scan problem but not Article V, since it is still author data interpolated into markup by
hand. Worth revisiting only if a case appears where the set genuinely cannot be enumerated.
