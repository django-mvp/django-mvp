# 0016 — Branded themes belong to the demo site, not to the package

**Status:** accepted

**Date:** 2026-08-25

**Supersedes:** [0012 — The package ships its own theme and applies it by default](0012-the-package-ships-its-own-theme-and-applies-it-by-default.md)

## Context

ADR 0012 gave the package two themes of its own, `mvp` and `mvp-dark`, declared in the shared
Tailwind preset and applied whenever a project configured nothing. The reasoning was that an
unchosen default makes no claim, and that a package asking a developer to hand over their UI
decisions should answer for the result — including the contrast failure on the prebuilt `light`
theme that issue #136 recorded.

That reasoning holds for the design work. It does not hold for where the design work lived.

A theme is the entire visible surface of an application: its colours, its corner radius, its
weight. Naming one `mvp` and shipping it in the wheel puts this package's identity on a page it
does not own, and makes it the identity every project inherits by not deciding. The two themes
were also the only part of the distribution that was branding rather than mechanism, which is
what made the placement conspicuous. Everything else in `mvp/` is a component, a variant, a
safelist or a template.

They still earn their place somewhere. The demo is the site where django-mvp is the subject
rather than the dependency.

## Decision

The `mvp` and `mvp-dark` blocks move to `demo/static/css/themes.css`, loaded by the demo's own
base template. Only `mvp/` is distributed, so this removes them from the wheel: from the shared
preset every consumer build imports, and from the prebuilt stylesheet a project gets when it runs
no build at all.

`MVP_CONFIG["theme"]` returns to `{"default": "light", "dark": "dark"}` — two of DaisyUI's own,
which is what the package applied before ADR 0012.

`demo/settings.py` names its pair in `default` and `dark`, the same two settings any project pairs
with its own theme file.

The demo's file is plain CSS rather than a Tailwind build. `@plugin "daisyui/theme"` emits exactly
the properties it is given and derives nothing, so running these values through a build would copy
them — `docs/theming.md` already says so and tells a reader writing a theme to write the CSS
directly. The demo is now a worked example of its own guide.

## Consequences

**The package's appearance is DaisyUI's again, and so is its contrast.** `text-error` on the
prebuilt `light` theme is 2.87:1, which is the defect issue #136 recorded and ADR 0012 fixed by
replacing the default. A project that configures nothing gets that pairing back on a form
validation message. This is the cost of the decision rather than an oversight in it, and ADR 0012
had already accepted the same exposure for every project that chose any other prebuilt theme:
most of DaisyUI's put at least one brand colour below the text floor against their own page
background. The package does not undertake to deliver an accessible interface, because it cannot —
a theme is one input to a page, and the markup, the copy and the images around it are the
project's. What changes here is that the zero-configuration case is no longer the exception.
`docs/theming.md` says so where someone choosing a theme will read it, and writing a theme to a
contrast obligation costs one CSS file.

**A project's appearance changes on upgrade,** for the second time and in the opposite direction.
Anything rendering `mvp` renders `light`. A project that wants the previous appearance copies
`demo/static/css/themes.css` into its own static files and names the pair, which is the same two
steps as any custom theme.

**A returning visitor is not moved,** for the same reason as before: the applied theme is read from
`localStorage` before the configured default, so a stored `mvp` survives an upgrade that removes
the block defining it. The name is not validated (ADR 0011) and nothing raises — the page falls
through to the default theme and renders. Rewriting a stored preference on the visitor's behalf
stays rejected.

**No prebuilt theme is affected.** ADR 0010 stands: all thirty-five still ship and are reachable
by name. Removing ours curates none of DaisyUI's, and `tests/test_brand_assets.py` asserts that in
the same pass it asserts the branded pair is gone.

**The brand marks stay in the wheel.** `mvp/static/brand/*.svg` and the resolvers that name them
are untouched. A logo is what a project puts on a page before it has chosen one, and it is one
element rather than the whole surface — a placeholder that reads as a placeholder. A theme is not.

**The contrast gate survives the move.** It runs against the demo's CSS now
(`tests/test_demo/test_demo_themes.py`), computing ratios from the file rather than trusting a
design note. It is a floor on our own work and it always was, but it now sits where that is
unambiguous.

## Alternatives considered

- **Delete the two themes.** Rejected. The palette is drawn, audited and documented, and the demo
  is a site that needs one. Deleting it would discard the work and leave the demo rendering in a
  prebuilt theme, which is the "unchosen default" problem ADR 0012 identified — still true of the
  demo, just no longer true of the package.
- **Keep them in the wheel but stop applying them by default.** Rejected. It answers half the
  objection. The blocks would still be emitted into every consumer's build, and a theme named
  `mvp` sitting unused in a project's stylesheet is branding shipped without even the benefit of
  someone having chosen it.
- **Give the demo its own Tailwind build.** Rejected as machinery for nothing. It would add a
  second entry, a second npm script and a second artifact to produce output identical to the CSS
  file, and it would let the demo's build diverge from the packaged one — which
  `assets/tailwind.css` deliberately prevents, so that a utility missing from the shipped
  stylesheet breaks a demo page rather than being papered over (issue #238).
