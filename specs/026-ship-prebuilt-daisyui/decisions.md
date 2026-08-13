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

**ADR:** none — a mechanism, not a decision, and `docs/theming.md` is where a reader needs it.

## D2 — A project's theme wins on layers, not on load order

`mvp/static/css/django-mvp.css` places its light and dark blocks inside `@layer base`. daisyUI's
published theme files contain no `@layer` rule at all. Unlayered declarations beat layered ones in
the cascade whatever the source order, so a project's plain theme file overrides the packaged one
even when it loads first.

This is why FR-012 is stated as an ordering-independent guarantee rather than "load your theme
after ours", and why FR-017 requires the documentation to explain it. A reader who believes order
matters will write ordering assumptions into their base template, and those assumptions will hold
by accident until something reorders the page.

**ADR:** none — same as D1; the cascade-layer behaviour is explained in `docs/theming.md`.

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

**ADR:** docs/adr/0010-every-prebuilt-theme-ships-in-the-package.md

## D4 — Nothing about the default theme changes

R18's roadmap entry names R11 as its predecessor, and R11 (issue #136, open) owns which theme the
package applies by default and whether it meets WCAG AA. This feature is deliberately built so the
two do not collide: with no configuration, the applied theme and the switcher's behaviour are
identical to the preceding release (FR-006, SC-006).

That also settles the upgrade question. A project that upgrades and changes nothing sees no visual
change, which is the only acceptable behaviour for a package at 0.x with real consumers.

**ADR:** none — a sequencing choice between this feature and #136, spent once and not inherited.

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

**ADR:** docs/adr/0011-theme-names-are-not-validated.md

## D6 — The switcher stays at light and dark until a project says otherwise

Presenting thirty-five themes to the visitors of every upgrading project would be a visible change
nobody requested. Which themes to offer is a product decision belonging to the project, so the
package ships the capability and no opinion (FR-007, FR-008), with the pre-existing pair as the
unconfigured behaviour (FR-006).

**ADR:** none — a backwards-compatibility default, local to this feature.

## D7 — Glossary gap found during grilling

`CONTEXT.md` defines component, attribute, override, mixin, integration and config, and says nothing
about themes, although the theme controller has been a configured navbar entry since before the
DaisyUI migration. FR-020 closes that. Recorded here because a missing glossary term is the kind of
thing a feature notices and nobody owns.

**ADR:** none — a glossary gap, closed in `CONTEXT.md` where it belongs.

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

## D8 — Three remedies from the design-review gate (2026-08-13)

The S3R design review returned `request_changes` with three medium findings, all verified against
the repository before being accepted as work.

- **Two exact-string assertions were left orphaned.** `tests/test_smoke.py:74` and
  `tests/test_components/test_mvp_tailwind_command.py:25` both assert the literal `@plugin "daisyui";`,
  which T002 and T012 each invalidate, and neither task's file list owned the update. T002 now owns
  the smoke assertion and relaxes it to the plugin name without the trailing semicolon, which still
  guards the intent its failure message states. T012's file list pointed at
  `tests/test_management_commands.py`, which does not exist — creating it would have split one source
  module's tests across two modules, against Article X. Repointed to the module that already holds
  them.
- **The completeness guard would have passed vacuously in CI.** `node_modules/` is gitignored and the
  Python CI job never runs `npm ci`, so T001's theme-completeness case either errors at collection or,
  parametrised over an empty glob, reports green while asserting nothing. It now skips explicitly and
  asserts the discovered list is non-empty before parametrising. The two invariants that read only the
  committed stylesheet stay unconditional, because they are what prove FR-006 in CI.
- **SC-004 was demonstrated by no task.** The plan declined a browser test on the grounds that the
  package's contract is its emitted attributes. That reasoning does not reach `data-set-theme`, which
  is markup this package has never shipped: an attribute theme-change never binds passes every markup
  assertion and does nothing when clicked, which is the failure the repository's own e2e module
  documents for the deferred bundle. T016 adds one browser test. Article XIV's row in `plan.md` was
  corrected rather than argued around.

**ADR:** none — a record of review findings and their remedies, not a standing decision.

## D9 — T001 reverses the #190 named-theme exclusion guard on purpose

`tests/test_smoke.py`'s `TestShippedStylesheetShipsCompleteDaisyUI` carried
`test_named_themes_are_not_shipped`, asserting `[data-theme=<name>]` was *absent* for a handful of
named themes. That assertion was correct for #190: the ask there was complete daisyUI *component*
coverage regardless of what mvp's own templates reference, while deliberately keeping only the
default light/dark theme pair, so the stylesheet stayed small. Its docstring said so explicitly.

FS-026 changes what "correct" means for the same code path: the feature's entire point is that a
project selects any prebuilt theme by setting one config value, which requires every theme's block to
ship. The old assertion and the new requirement are direct opposites over the same evidence (the
built stylesheet), so the guard could not be kept alongside the new one — it was replaced with its
inverse rather than left to rot as a second, contradictory source of truth.

The original reasoning is not deleted: `TestShippedStylesheetShipsCompleteDaisyUI` and its docstring,
which explain #190's component-coverage ask, are untouched above the new class. Only the
themes-are-excluded assertion — the one part of #190 this spec deliberately supersedes — is replaced,
by `TestShippedStylesheetShipsEveryPrebuiltTheme`, which also adds the two invariants (default theme
still bound through `:where(:root)`, `prefers-color-scheme: dark` still emitted) that prove FR-006
holds through the reversal rather than assuming it.

**ADR:** none — the reasoning lives in the test that replaced the guard, which is where the next reader meets it.

## D10 — US1 was built by a delegated worker, through a fallback route (2026-08-13)

The usual mechanism for handing a story to a separate worker was unavailable, returning a
connection error on three consecutive attempts while the service behind it reported healthy. The
story was handed over by a second, equivalent route instead.

What the usual mechanism protects was kept: the story was built by a worker separate from the one
that reviews and merges it, on the smaller model tier rather than the one used for planning, and
its report was re-verified independently before the ledger advanced. What was lost is live
visibility of the worker while it ran, which costs observability rather than correctness.

**Revisit if**: the usual route returns. This is a fallback, not a new preference.

**ADR:** none — how the work was delegated, with no bearing on the package.

## D11 — FR-001 needed a check that survives CI (2026-08-13)

Found in the orchestrator's independent verification of US1, not by the implementer or by any gate.

T001's completeness case discovers theme names from `node_modules/daisyui/theme/*.css`. The design
review had already caught that this would report green on an empty glob, and the remedy was to skip
explicitly and assert a non-empty list first. That remedy is correct and it was implemented
correctly. It does not, however, address what remains once the skip fires.

`node_modules` is gitignored and the Python CI job never runs `npm ci`, so in CI the completeness
case is skipped. Running the class with `node_modules` moved aside gives two passed, two skipped —
and both survivors, the `:where(:root)` binding and the `prefers-color-scheme` block, were already
true before this feature. They are regression guards for FR-006, which is what they were designed
to be. Nothing was left asserting FR-001, the requirement this feature exists to satisfy. Reverting
`themes: all` would have been a silently green change.

The fix is the five theme names #190's original guard listed, asserted unconditionally against the
committed stylesheet. No new dependency on the front-end toolchain, and the completeness case stays
as the stronger local check.

Proven against the defect before being accepted as a gate: with `themes: all` reverted and
`node_modules` absent, five cases fail where the suite was previously green. Restored, the class is
green again.

The general shape, which is not about themes: **a skip changes which assertions remain, and the
remainder has to be checked on its own terms.** Reviewing the skip's correctness is not the same as
reviewing what is left running, and here the two answers differed.

**ADR:** none — a testing lesson, carried in the comment above the check it produced.

## D12 — T007's offered set stays an inline escaped array; its tests stay source-level (2026-08-13)

**The offered set reaches the guard as an inline JS array of individually escaped literals, not
`json_script`.** `mvp/base.html`'s guard already emits `theme.default` as `"{{ ... |escapejs }}"`,
a double-quoted JS string literal built the same way. `theme.choices` is a list, so the same
technique applied per element — `[{% for choice in ... %}"{{ choice|escapejs }}"...{% endfor %}]`
— keeps both values escaped by the identical mechanism, in the same script block, with no second
element or `id` added to the page. `json_script` was the alternative: safer for arbitrary nested
data, but it buys nothing here (every element is a short plain string, already safe under
`escapejs`) at the cost of a second DOM node purely for guard bookkeeping, plus a JS parse step to
read it back. Not used.

**T007's new tests assert against the guard's emitted script source, exercising neither a real
browser nor a JS runtime.** This is not a new choice for this file — `TestPrePaintThemeGuardPosition`,
`TestPrePaintThemeGuardDefault` and `TestPrePaintThemeGuardEscaping` (T004) already established this
seam, and the module docstring names why: the Django test client has no real `localStorage`, so the
guard's actual contract, as tested here, is its source. T007 continues that pattern rather than
introducing a second one (e.g. shelling out to the `node` binary already present for the frontend
build, which is available but would exercise this one file differently from every other guard test
in the same suite for no proportionate gain). The membership tests therefore check that the offered
set reaches the script, and that a real membership expression (`indexOf`/`includes` against the
stored value) is present, rather than exercising `localStorage` end to end — that end-to-end case
is what T016 exists for, out of this dispatch's scope, using the browser harness that already has a
documented failure mode for scripts bound on `DOMContentLoaded`.

**Revisit if**: a future story needs to assert genuine runtime behaviour of `mvp/base.html`'s guard
beyond what T016's `@requires_browser` test already covers — at that point the source-level tests in
this file stop being sufficient evidence and the file's own established convention should be
revisited, not worked around task by task.

**ADR:** none — a local implementation choice within an established seam, and reversible in one edit.

## D13 — T010's test moved from a standalone tests/test_docs.py into tests/test_smoke.py (2026-08-13)

`plan.md`'s Structure Decision and `tasks.md`'s T010 file list both name `tests/test_docs.py` as
the home for the variable-coverage contract. Written there first, it failed `forge verify`'s
conformance check on the story's mandatory final run: "mirrors no source module (expected
mvp/docs.py or mvp/docs/__init__.py); a cross-cutting test belongs in the module of its subject as
another Test\* class." `docs/theming.md` is markdown, not a Python module, so Article X's
mirror-source-tree rule has nothing for a `test_docs.py` to mirror.

`tests/test_smoke.py` already carries `TestStylingDocs`, a near-identical check against
`docs/styling.md`, established as this repo's home for exactly this shape of cross-cutting
documentation check. `TestThemingDocVariableCoverage` moved there instead, reusing the
`_DAISYUI_THEME_DIR` module-level constant T001/T005's class already defines rather than
duplicating it. The test's content and behaviour (RED/GREEN proof, the skip convention) are
unchanged from the version described in progress.md's first T010 entry; only its file location and
import surface (`re`, `Path`, `pytest`, `BASE_DIR` — all already imported in `tests/test_smoke.py`)
changed.

**Revisit if**: a `mvp/docs.py`-shaped module is ever introduced (unlikely — documentation content
checks in this repo have never mirrored a source module), at which point this class could move
again to mirror it properly.

**ADR:** none — a file moved to satisfy a structure rule the project already states.

## D14 — T016 implemented directly rather than dispatched (2026-08-13)

One test, no design content, and it depends on T013, which belongs to a different story than the
one T016 was filed under. Standing up a fourth worktree and provisioning two toolchains to add a
single browser test costs more than it returns.

Recorded because skipping dispatch is the exception, not the norm, and the exception is supposed to
be visible.

The test was proven against the failure it exists to catch, rather than accepted because it passed:
with the JavaScript bundle blocked at the network layer — the state where `data-set-theme` is
rendered correctly and nothing ever binds it — the test fails. Restored, it passes. That is the
same failure the toggle test beside it already documents, and the reason a rendered-markup assertion
could not have covered SC-004.

**ADR:** none — how one task was executed, with no bearing on the package.

## D15 — Four review findings, and one defect in my own remedy (2026-08-13)

The code review returned `request_changes` with two high and two lower findings. Both highs were
verified against the code before being accepted as work rather than taken on the reviewer's word.

**A stale theme came back after first paint (high).** The pre-paint guard rejected a stored theme
the project no longer offers, but never rewrote the stored value. The bundled theme-change library
re-applies `localStorage.theme` on `DOMContentLoaded` with no membership check of its own —
confirmed by reading the shipped bundle, which calls `setAttribute` guarded only by the key being
truthy. So the requirement held for one frame and was reverted on every load, permanently. The
tests missed it because they asserted on the guard's emitted source, where the logic is correct,
and the browser test only ever selected a theme that was in the offered set. The fix writes the
resolved theme back, deliberately only when a stored value was rejected: writing unconditionally
would populate the key on a first visit to a project that configures nothing, which flips the
toggle's active state and is a visible change for an upgrading project.

**Switcher entries were not keyboard reachable (high).** They rendered as `<a>` with no `href`,
which is not in the tab order, and theme-change binds only `click`. The switcher could be opened
with a keyboard and not used. Fixed by rendering through the packaged `c-menu.item`, which already
emits a `<button>` when given no href, so the entries became focusable and Article XI's reuse rule
is satisfied as a side effect rather than by a second hand-rolled list.

**The documentation check was skipped in the environment that needed it (medium)** and **the size
budget had no test at all (low).** Both now read committed files, so both run in CI.

**And a defect in my own remedy, found by testing it against the bug it was for.** Pointing the
documentation check at the committed stylesheet was correct, but the assertion looked for each
variable *anywhere in the page*, and the worked example sets all twenty-eight. The variable table
could have been deleted outright with the check still green. It now reads the table's rows, and a
second case asserts each row actually says what its variable controls, since a row with an empty
description satisfies coverage while telling a reader nothing.

Every remedy was proven against its defect before being accepted: reverting each fix in turn makes
the corresponding test fail, and restoring it makes the test pass.

**ADR:** none — remedies to findings against this feature's own code, each already carried by the
test that guards it.
