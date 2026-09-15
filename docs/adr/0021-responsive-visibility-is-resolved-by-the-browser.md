# 0021 — Responsive visibility is resolved by the browser, not by the page's scripts

**Status:** accepted

**Date:** 2026-09-15

## Context

Several regions of the shell exist twice, once for narrow viewports and once for wide ones: the
header's trailing actions, the sidebar toggle and site icon the sidebar header also draws, and the
Account Center's navigation. Which copy a person sees depends on a project setting, so for a long
time the classes that expressed it were assembled per request by template tags.

Assembling a class at render time has a real cost in a Tailwind package. The stylesheet build
scans source for literal class names, and a name that only ever exists as the result of an
expression is never found — so the markup comes out correct and the styling comes out missing. The
package compensated with safelist entries and a test that checked the entries still covered
everything the tags could produce. That is a mechanism, a list and a guard standing in for a rule
that could simply be written down.

The obvious alternative, and the one proposed when the cost was first raised, is to let the page's
own scripts decide: hold the layout state in a store and show or hide each region from an
expression. It reads well and it removes the tags.

It also reintroduces a defect this package has already paid for. The shipped bundle is deferred, so
nothing it registers exists until the document has finished parsing. Visibility decided by script
is applied after the first paint, which means both copies of every region are briefly on screen, on
every load and again on every navigation that swaps the body. The sidebar carries a blocking inline
script for exactly this reason: resolving its remembered state after paint turned a correction into
a visible animation, and the only fix was to resolve it before.

## Decision

Responsive visibility is expressed in CSS and resolved by the browser. No region of the shell is
shown or hidden by an expression the page's scripts evaluate.

Where a rule depends on a project setting, the setting reaches the stylesheet as an attribute the
shell renders, and the stylesheet carries one static rule per supported value. The regions
themselves carry a stable class naming what they are, not a class describing when they appear.

The attributes go on an element a component renders, never on the document body. Replacing the
base template is a documented extension, and a project that does so writes its own body — a rule
keyed off an attribute there would be lost silently, and the failure would only show at some
viewport widths.

## Consequences

The classes involved are literals the stylesheet build can see, so the safelist entries that
covered them are gone and so is the test that guarded them. A project generating its own CSS from
the packaged preset gets the rules without naming anything.

Visibility now survives JavaScript being unavailable, costs nothing on resize, and behaves the same
on a boosted navigation as on a full load. It is also expressed the same way as every other
responsive decision in the library, so the shell's regions stop being a special case.

The cost is that a rule which depends on a setting is written once per supported value of that
setting rather than once in total. That is a fixed, visible cost in one file, and it replaces a
variable, invisible one spread across a tag, a safelist and a guard.

Client-side state is still worth having, and the shell publishes it — see
[ADR 0022](0022-the-layout-store-mirrors-state-it-does-not-own.md). What it is not used for is
deciding what is on screen at first paint.
