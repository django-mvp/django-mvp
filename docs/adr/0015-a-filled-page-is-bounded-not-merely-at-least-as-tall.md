# 0015 — A filled page is bounded, not merely at least as tall as the viewport

**Status:** accepted

**Date:** 2026-08-17

## Context

`<c-page fill>` shipped with issue #247 to let a page take the shell's height rather than its
content's. Its rule gave `.drawer-content:has(.mvp-page-fill)` a flex column and
`min-height: 100dvh`.

A floor is the right guarantee for the case that motivated it. The demo it was built for is a map,
which is as tall as it is told to be and never taller, so a floor and a ceiling are the same number
and the difference never showed.

The first consumer whose content overflows is a table, and there the difference is the whole
behaviour. `min-height` says the page is *at least* the viewport tall. A hundred rows make it
taller, the shell grows to fit, and the window scrolls — which is precisely the thing a filled page
exists to prevent. The mechanism was doing what it said and not what it meant.

Stating the ceiling is not sufficient on its own. A flex item's `min-height` computes to `auto`, so
`<main>` refuses to shrink below its content and overflows the container that was meant to bound
it. The height stops at the top of the chain and never reaches the content that asked for it.
`<c-page.content>` already carried `min-h-0`; the two rungs above it did not.

## Decision

A filled page is bounded by the viewport. The rule states `height` as well as `min-height`, and
both rungs between the shell and the page content release their automatic minimum height so the
bound can actually propagate.

A filled page therefore clips, and hands scrolling to whatever inside it asks for the overflow.
That is what `fill` always promised.

## Consequences

Any page already using `fill` whose content is shorter than the viewport is unaffected — floor and
ceiling agree there, which is why this went unnoticed. A page whose content is taller now clips
instead of growing the window, and has to nominate a scroll container. That is a behaviour change,
and it is in the changelog.

The rule stays scoped by `:has()` to pages carrying the mark. A page that never asked to be filled
computes exactly as it did before.

## The general form

A promise implemented as a floor is not a promise. `min-height: 100dvh` and `height: 100dvh`
describe the same layout for every input the original author tried, and different layouts for the
first input they did not. Where a mechanism's name states a bound — fill, fit, cover — the rule
implements the bound in both directions, and a case whose content overflows belongs in its test set
from the start.
