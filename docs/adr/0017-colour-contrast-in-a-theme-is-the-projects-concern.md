# 0017 — Colour contrast in a theme is the project's concern, not the package's

**Status:** accepted

**Date:** 2026-08-25

## Context

[ADR 0016](0016-branded-themes-belong-to-the-demo-site.md) took this package's two themes out of
the distribution, which returned the applied default to one of DaisyUI's. On that theme
`text-error` is 2.87:1 against the page background, below the WCAG AA floor for text, and that is
the pairing a form validation message is drawn in. The same is true of most of the prebuilt set:
at least one brand colour below the floor against its own page background.

That left an open question the codebase had two contradictory answers to. Roadmap item R11
promised "a theme shipped and applied by default, meeting WCAG AA contrast", which is what the
themes ADR 0016 removed were built to satisfy. Doing it again would mean shipping a theme again.

## Decision

**The package meets accessibility requirements in what it controls, and colour is not in that
set.** The stock DaisyUI themes ship as they are, the applied default is one of them, and their
contrast is not something this package undertakes to fix.

The reasoning is about who the work would be for. A theme is the first thing a project replaces —
it is the surface their brand lives on, and almost nobody ships an application in their
dependency's colours. Effort spent perfecting a palette that is documented as the thing to change
buys an accessible result for the small number of projects that change nothing, and buys nothing
at all for the rest. Neither group is helped by a compliant theme they do not use.

**What remains squarely in scope, because it is what the package actually emits:** semantic
markup, heading structure, focus order and visible focus, labels and accessible names, ARIA where
a component's role is not carried by an element, keyboard reachability of every control, and
motion and target-size behaviour. Those are the package's output regardless of which theme is
applied, and a project cannot fix them from a CSS file. They are held to the standard.

**What is out of scope:** the contrast ratios of any theme's colour values, including the applied
default. `docs/theming.md` says so where someone choosing a theme will read it, and points at the
mechanism — a project with a contrast obligation writes a theme to it, which costs one CSS file
and one setting.

## Consequences

**Roadmap R11 is rejected** rather than left standing as work nobody intends to do. A roadmap item
that contradicts a decision is worse than an absent one, because the next person to read it treats
it as a commitment. R18 loses its dependency on it.

**Issue #136 stays fixed only for projects that act on it.** It reported unreadable form
validation errors on the stock light theme. That report was accurate and remains accurate. What
changes is the answer: the remedy is a theme the project writes, documented in the theming guide,
rather than a theme this package maintains.

**The demo keeps its contrast gate,** and it is the boundary of this decision rather than an
exception to it. The demo's two themes are output we control and ship nobody else's application
on, so `tests/test_demo/test_demo_themes.py` holds them to the floor. It costs one test module
that already exists and it keeps the site a developer judges the package on readable.

**A theme is not reintroduced by the back door.** If a future change wants a packaged palette for
some other reason, ADR 0016 is the decision it has to argue with, and contrast is not an argument
this one leaves available.
