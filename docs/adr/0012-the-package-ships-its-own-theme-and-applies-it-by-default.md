# 0012 — The package ships its own theme and applies it by default

**Status:** accepted

**Date:** 2026-08-13

## Context

django-mvp shipped no theme of its own. With nothing configured it rendered in `light`, one of
DaisyUI's prebuilt themes, so the package's out-of-the-box appearance was a default nobody had
chosen and nobody could defend.

That is a problem for a package whose pitch is that a developer hands over the UI decisions they
would rather not make. Visible design care is the credential, and a default drawn from someone
else's framework makes no claim at all. It was also visibly poor in one specific place:
`text-error` on `light`'s page background is 2.87:1, so the packaged form field's validation
message was hard to read (issue #136), and forms are the surface these applications are mostly
made of.

A brand palette now exists, with a light and a dark set drawn in their own right.

## Decision

The package ships two themes of its own, `mvp` and `mvp-dark`, and applies `mvp` when a project
configures nothing. They are declared in the shared Tailwind preset rather than in this repository's
build entry, so a project generating its own entry with `mvp_tailwind` gets them without doing
anything.

`MVP_CONFIG["theme"]` gains a `dark` key naming the theme the packaged toggle switches to. The
toggle is built from `default` and `dark` rather than from the literal strings `light` and `dark`,
so a project that replaces the pair keeps a working switch.

## Consequences

**No prebuilt theme is replaced.** The names are the package's own, so all thirty-five themes
DaisyUI publishes remain available and reachable by name, and ADR 0010 stands unchanged. The
alternative, publishing our palette under the names `light` and `dark`, would have overridden two of
them and made correctness depend on which block the build emitted last.

**A project's appearance changes on upgrade.** Anything that was rendering the prebuilt `light`
theme by default now renders `mvp`. Pinning `MVP_CONFIG["theme"]["default"] = "light"` restores the
previous appearance exactly, and that is the whole of the migration.

**A returning visitor is not moved.** The applied theme is read from `localStorage` before the
configured default is consulted, so someone who has already used a site and has `light` persisted
keeps seeing it. Two clicks of the toggle reaches `mvp`, because the toggle now names the packaged
pair. Rewriting a stored preference on the visitor's behalf was rejected: the stored value is a
choice the person made, and a package upgrade is not a reason to discard it.

**The contrast floor applies to these two themes and to nothing else.** `text-error` is 8.19:1 in
`mvp` and 5.05:1 in `mvp-dark`, against 2.87:1 on the prebuilt `light`. The prebuilt themes are
DaisyUI's files and are not ours to edit, so most of them still put at least one brand colour below
the text floor against their own page background.

That is deliberate rather than an outstanding task. The package does not undertake to deliver an
accessible interface, because it cannot: a theme is one input to a page, and the markup, the
copy and the images around it are the project's. A project carrying a contrast obligation writes
a theme to it, which costs one CSS file and nothing else. `docs/theming.md` says so where someone
choosing a theme will read it.

**Our own palette is gated rather than asserted.** `tests/test_brand_theme.py` computes every
contrast ratio from the theme source and fails below the floor, and the check was verified by
reinstating a failing colour and watching it go red. The design document's figures are evidence for
the palette. They are not what the build trusts.

## Alternatives considered

- **Publish the palette as `light` and `dark`.** Rejected. It reaches a returning visitor's stored
  preference without asking, which is the one real advantage, but it removes two prebuilt themes,
  contradicts ADR 0010, and leaves two definitions of each name in one stylesheet where only
  emission order decides the winner. A correctness that depends on import order is one that stops
  being true silently.
- **Ship the themes and leave `light` as the default.** Rejected. It makes the brand an opt-in that
  nobody would find, and it leaves the package's own appearance as an unchosen default, which is the
  exact thing this decision exists to end.
- **Derive the dark theme from the light one.** Rejected. The hardest reader this package has is
  someone debugging in a dark editor at the end of a day, on a dependency they did not choose. Dark
  is designed and audited in its own right for that reason, not generated as a courtesy.
