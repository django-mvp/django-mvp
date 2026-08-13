# 0010 — Every prebuilt theme ships in the package

**Status:** accepted

**Date:** 2026-08-13

## Context

django-mvp shipped two themes, light and dark. Reaching any of the others meant either a Tailwind
build of your own or a `<link>` to a third-party CDN, which the documentation recommended.

Both routes conflict with goals the package already holds. It promises that no front-end build
tooling is required, and that every asset the front end needs is shipped and versioned with the
package rather than fetched from a third party at page load. A project wanting `dracula` had to give
up one of the two.

The reason recorded for shipping only two was size. `docs/styling.md` said that including the rest
"would bloat the stylesheet for every project regardless of which theme it actually uses", and a
test asserted the other themes were absent. Neither statement rested on a measurement.

## Decision

The stylesheet build enables every theme DaisyUI publishes, so all of them ship inside the package.
A project selects one by name through `MVP_CONFIG` with nothing to install and nothing to fetch.

The package ships whatever set the pinned DaisyUI version publishes. It does not curate that list.

## Consequences

The compressed stylesheet grows from 41,670 to 46,532 bytes, an increase of 4,862. That is the whole
cost, because a theme is a block of custom properties and adds no component or utility rules. The
earlier concern was real in kind and wrong in size by roughly an order of magnitude.

Shipping each theme as its own file and linking only the configured one was considered. It would
save about 4.8 KB for a project on the default theme, and cost a second request, a config-dependent
asset path, thirty-five static files, and a failure mode where a mistyped name returns a 404 instead
of falling through. The saving does not pay for the moving parts.

A test now asserts the themes are present, which is the exact inverse of the guard it replaced. The
original guard's reasoning is left beside it rather than deleted, because it was correct for the
change that introduced it.

Default appearance does not change. With no configuration, the theme that applies and the way the
switcher behaves are what they were before.

## Alternatives considered

- **Curate a shorter list.** Rejected. It trades about 4 KB for a judgement the package has no basis
  to make about which themes a project might want.
- **Keep the CDN instruction.** Rejected. It is the specific thing the shipped-assets goal forbids,
  and it makes a project's appearance depend on a third party staying up.
