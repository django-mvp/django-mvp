# Decisions — FS-026 Themes that ship with the package

Rationale too long to inline in `spec.md`, plus every ambiguity resolved without asking. Short
question-and-answer records live in `spec.md` under `## Clarifications`; this file carries the
evidence behind them.

## D1 — Themes are runtime CSS, so nothing here needs a build step

**Established by reading the pinned package, not the upstream documentation.** daisyUI 5.6.18 as
installed in this repo publishes each theme as a standalone plain CSS file under
`node_modules/daisyui/theme/<name>.css`. Each one is a single block of about thirty custom
properties:

```css
[data-theme="dracula"] { color-scheme: dark; --color-primary: oklch(75.461% 0.183 346.812); ... }
```

The packaged component classes already in `mvp/static/css/django-mvp.css` read those properties
through `var()`, so replacing the block replaces the look with no rebuild.

`daisyui/theme/index.js` shows the `@plugin "daisyui/theme" {}` syntax is a pass-through: it merges
the tokens given to it with a built-in theme of the same name if one exists and emits them through
`addBase`. It computes nothing. A hand-written theme file and a plugin-generated one therefore
produce the same CSS, except that the plugin's output lands in a cascade layer.

This is the fact the documentation has to carry (FR-016). Without it a reader reasonably assumes a
theme is a build artefact, which is why the current guidance sends them to a CDN or to a Tailwind
build.

## D2 — A project's theme wins on layers, not on load order

`mvp/static/css/django-mvp.css` places its light and dark blocks inside `@layer base`. daisyUI's
published theme files contain no `@layer` rule at all. Unlayered declarations beat layered ones in
the cascade whatever the source order, so a project's plain theme file overrides the packaged one
even when it loads first.

This is why FR-012 is stated as an ordering-independent guarantee rather than "load your theme
after ours", and why FR-017 requires the documentation to explain it. A reader who believes order
matters will write ordering assumptions into their base template, and those assumptions will hold
by accident until something reorders the page.

## D3 — Shipping every theme, rather than a curated subset

Measured against this repo's committed artefacts:

| Artefact | Raw | Compressed (brotli) |
|---|---|---|
| `mvp/static/css/django-mvp.css` | 414,884 B | 41,670 B |
| all 35 theme definitions (`daisyui/themes.css`) | 38,347 B | 5,011 B |

About 5 KB compressed for the complete set, because themes declare variables and add no component
or utility rules. `docs/styling.md` currently states that shipping them "would bloat the stylesheet
for every project", and `tests/test_smoke.py:157` asserts they are absent. Neither was measured.
Curating a subset would trade a decision the package has no basis to make for roughly 4 KB.

SC-003 bounds the growth at 8 KB compressed rather than at the measured 5 KB, so that a later change
which does add rules is caught rather than absorbed into the allowance.

## D4 — Nothing about the default theme changes

R18's roadmap entry names R11 as its predecessor, and R11 (issue #136, open) owns which theme the
package applies by default and whether it meets WCAG AA. This feature is deliberately built so the
two do not collide: with no configuration, the applied theme and the switcher's behaviour are
identical to the preceding release (FR-006, SC-006).

That also settles the upgrade question. A project that upgrades and changes nothing sees no visual
change, which is the only acceptable behaviour for a package at 0.x with real consumers.

## D5 — Theme names are not validated

*Settled at the Spec gate, 2026-08-13, on the maintainer's ruling. The specification originally
required a start-up error for a name that matched nothing.*

The check cannot be built honestly. A project's own theme is a block of custom properties in a CSS
file the project loads and the package never reads, so the package cannot know whether a name will
resolve. Validating against the shipped set alone would reject every custom theme, which is the case
the feature exists to support. The only way to keep a check would be a registration list, and that is
configuration a project has to keep in step with its own stylesheet, bought at the price of the
mechanism that made custom themes free.

Silent fall-through is benign rather than broken, which is what makes the ruling safe. In
`mvp/static/css/django-mvp.css` the default theme is bound to
`:where(:root),:root:has(input.theme-controller[value=light]:checked),[data-theme=light]`. The
`:where(:root)` arm carries zero specificity and matches the document root unconditionally, so an
unmatched `data-theme` value leaves the default theme in effect and the page renders normally. There
is no unstyled state to protect against.

What remains is a documentation obligation rather than a code one (FR-014, FR-020, SC-008): a
developer whose theme does not appear needs to be told that the name simply matched nothing, or they
will look for the fault in their CSS.

The wider principle, worth keeping: a validation rule the package cannot evaluate completely is worse
than none, because it converts an open extension point into a closed list.

## D6 — The switcher stays at light and dark until a project says otherwise

Presenting thirty-five themes to the visitors of every upgrading project would be a visible change
nobody requested. Which themes to offer is a product decision belonging to the project, so the
package ships the capability and no opinion (FR-007, FR-008), with the pre-existing pair as the
unconfigured behaviour (FR-006).

## D7 — Glossary gap found during grilling

`CONTEXT.md` defines component, attribute, override, mixin, integration and config, and says nothing
about themes, although the theme controller has been a configured navbar entry since before the
DaisyUI migration. FR-020 closes that. Recorded here because a missing glossary term is the kind of
thing a feature notices and nobody owns.

## Out of scope, recorded so it is a choice rather than an omission

- **Per-user theme storage.** The selection is per browser, as it already is. Binding a theme to a
  signed-in profile is its own feature with its own storage and migration questions.
- **Honouring the operating system's colour-scheme preference.** The package ignores it today.
  Starting to honour it would change appearance for every existing project and belongs with R11,
  which owns default appearance.
- **Curating which prebuilt themes exist.** The package ships what the pinned design system version
  publishes.
- **The remaining third-party asset fetch.** `mvp/templates/mvp/base.html:25` loads bootstrap-icons
  from a CDN, which G14 also forbids. It is unrelated to theming and belongs in its own change,
  where the icon set's weight and the packaging question get the attention they need.
