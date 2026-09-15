# 0023 — The sidebar footer is a fixed composition

**Status:** accepted

**Date:** 2026-09-15

## Context

`MVP_CONFIG["layout"]["sidebar"]["footer"]` was a list of Cotton component names, rendered in
declaration order inside a centered, wrapping flex row. It read exactly like the navbar's own
widget lists, so a project reached for it the same way: name a component, it appears.

The two are not the same kind of decision. A navbar's trailing edge really does vary by project —
which widgets belong there, and in what order, is a call the package cannot make for you. The
sidebar footer's *composition* is not that kind of call. Every project needs the same thing in it:
a way to sign in or reach the account menu, and the controls that only make sense once, for the
whole shell — a theme switch, a language switch. The setting's real job was never choosing *which*
components to include; it was giving a project a way to change how a fixed set of components sit
next to each other, and a list of names is a poor tool for that. Reordering meant editing a Python
list. Changing a wrapping, centered row to something else meant a template override regardless,
because no attribute or setting controlled the row's layout — it was hard-coded in
`templates/cotton/app/sidebar/footer.html`. So a project that actually wanted a different
footer was already overriding the template. The setting only ever satisfied the case where the
default row's layout was fine and only the guest list changed, and even that case still needed a
custom component's dotted-path name, resolved by convention rather than declared.

The package's own constitution already answers where a decision like this belongs. Article XII
reserves Python-level configuration for structural concerns — one that changes what a project's
pages *can do* — and requires the narrower mechanism wherever a component attribute or a slot
override already expresses the same thing completely. Article XI says the same thing from the
consumer's side: where a project needs more control than an attribute gives, the answer is a
template override, not a wider configuration surface. A footer's composition is presentation. A
template override at `templates/cotton/app/sidebar/footer.html` already expresses "what goes in
this row, and in what layout" completely, with none of the constraints the setting carried — real
component attributes reach through, an unguarded `is_authenticated` pair can sit side by side
instead of two dotted-path strings, and the layout is ordinary Cotton markup instead of a fixed
wrapping-row template the setting could not touch. The setting was configuration where a template
override was already the sufficient, and available, mechanism — the case both articles ask to be
resolved in the template's favor.

## Decision

`templates/cotton/app/sidebar/footer.html` composes its four children directly: the signed-in
user's menu or a log-in button (each already guards on `request.user.is_authenticated`, so both
sit in the template unconditionally), a theme control, and a language control. The setting is
gone. `MVP_CONFIG["layout"]["sidebar"]["footer"]` no longer has any effect; a project that still
sets it gets an `MVPDeprecationWarning` naming the replacement, and the value is discarded before
any template can read it.

Changing what the footer shows, or how its children are arranged, means overriding that one
template — the mechanism Article XI already names for this, and the one a project reaching for
anything beyond the default list was already using.

## Consequences

A project that configured the footer must move to a template override on upgrade. The deprecation
warning is what tells it to, rather than a silently unchanged footer.

A project that never touched the setting gains a footer with sensible, working defaults it did not
have to assemble: a way to sign in or reach the account menu, and the theme and language controls,
without listing any of the three.

The tradeoff Article XII accepts everywhere it applies is accepted here too: a project wanting a
narrow change — a different order, or a fourth component — writes a template rather than a Python
list. The setting could reorder its three names by reordering the list, but it could never change
the row itself to anything but the wrapping, centered layout hard-coded in the template underneath
it. The template that replaces it can do both, so projects lose nothing the setting actually
offered.
