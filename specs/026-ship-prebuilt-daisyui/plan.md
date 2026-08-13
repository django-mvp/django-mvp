# Implementation Plan: Themes that ship with the package

**Branch**: `026-ship-prebuilt-daisyui` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/026-ship-prebuilt-daisyui/spec.md`

## Summary

Enable every prebuilt daisyUI theme in the stylesheet build so all 35 ship inside the package, add a
`theme` block to `MVP_CONFIG` for the applied theme and the switcher's offered set, teach the
pre-paint guard and the theme controller to read that block, and write the theming documentation the
package has never had.

The whole feature is CSS custom properties and configuration. No models, no migrations, no new
dependency, no Python runtime logic beyond reading config into a template.

## Technical Context

**Language/Version**: Python 3.12+, Django 5.2 / 6.0

**Primary Dependencies**: Tailwind CSS 4.3.2, daisyUI 5.6.18, theme-change 2.0.2 — all already
pinned in `package.json`, all already vendored. Nothing is added.

**Storage**: N/A. The visitor's selection lives in browser `localStorage` under the existing `theme`
key.

**Testing**: pytest + pytest-django, rendered-markup assertions per Article XIII. No browser test is
warranted (Article XIV): every behaviour here is assertable against rendered HTML or the built
stylesheet.

**Target Platform**: Any browser the package already supports. `oklch()` and `:has()` are already
required by the shipped stylesheet, so themes introduce no new browser floor.

**Project Type**: Django package (single project, `mvp/`).

**Performance Goals**: No runtime cost. The only measurable change is stylesheet weight.

**Constraints**: Compressed stylesheet growth ≤ 8 KB (SC-003). Behaviour identical to v0.18.0 for a
project that configures nothing (FR-006, SC-006).

**Scale/Scope**: 35 prebuilt themes, one config block, two template changes, one new documentation
page, one inverted smoke-test guard.

## Phase 0 — Research

Complete. Findings and their evidence are in [decisions.md](decisions.md) (D1–D7); the load-bearing
mechanics were established by reading the pinned `node_modules/daisyui@5.6.18` rather than upstream
documentation. `research.md` is not created: there is no open technical question left to research,
and a file restating decisions.md would be a second place for the same facts to drift.

Three findings shape the plan:

1. **A theme is runtime CSS.** Each theme is a block of ~30 custom properties under
   `[data-theme="<name>"]`. `@plugin "daisyui/theme"` is a pass-through (`daisyui/theme/index.js`),
   not a generator. So nothing here needs a build step at consumer time.
2. **`themes: all` preserves today's behaviour exactly.** `daisyui/functions/pluginOptionsHandler.js`
   shows the bare `@plugin "daisyui"` default is `["light --default", "dark --prefersdark"]`, and the
   `themes: "all"` branch applies `light` with `--default` and `dark` under
   `@media (prefers-color-scheme: dark)` before emitting every remaining theme with no flags. Light
   stays bound to `:where(:root)` at zero specificity and dark keeps its media query. **This is why
   FR-006 needs no special-casing** — the one-line build change is behaviour-preserving by
   construction, and the plan verifies it rather than assuming it.
3. **Unlayered beats layered.** Packaged themes land in `@layer base` via `addBase`; a project's
   hand-written theme file has no layer, so it wins whatever the load order (FR-012).

## Constitution Check

*Gate: passed before Phase 1. Re-checked after the task breakdown.*

| Article | Bearing on this feature | Verdict |
|---|---|---|
| I — Test-First | Every task writes its assertion before its change. The stylesheet tasks assert against the built artifact, the config tasks against the merged dict, the template tasks against rendered markup. | Pass |
| II — Simplicity | The chosen approach is one build-config line plus one config block. The rejected alternative (per-theme static files with conditional loading) is recorded below. | Pass |
| III — Anti-Abstraction | No theme registry, no resolver, no indirection. Config values reach the template directly through the existing context processor. | Pass |
| IV — Integration-First | The config block is the integration surface and is designed before the templates that read it (T003 precedes T006/T008). | Pass |
| V — Security | No new input is trusted. The configured theme name and offered set are project-authored config, not user input, and reach the page as a JSON-escaped literal via `json_script`-style escaping rather than raw interpolation. The visitor's stored value is compared against the offered set before use, never injected into markup. | Pass |
| VI — Documentation | Six of the twenty-one requirements are documentation. README and CHANGELOG updated in this PR per the quality bar. | Pass |
| VII — Dependency discipline | Nothing added. daisyUI, Tailwind and theme-change are already pinned and vendored. | Pass |
| VIII — Internationalization | New user-facing strings in the theme switcher go through `gettext`. Theme names themselves are identifiers and are not translated. | Pass |
| IX — Data-model conventions | No models. | N/A |
| X — Test structure | New tests mirror the source tree: `tests/test_components/test_theme_controller.py`, `tests/test_config.py` additions, `tests/test_docs.py` for the documentation contract. | Pass |
| XI — Components are the public API | `c-actions.theme-controller` keeps its name and its role. It gains no new attribute: the offered set comes from `MVP_CONFIG`, which is the Article XII resolution order, not a widened attribute surface. | Pass |
| XII — Configuration-driven layout | The feature is configuration-driven by construction. | Pass |
| XIII — Rendered markup is a contract | The switcher's markup changes shape when a set is configured, so both shapes get rendered-markup assertions. | Pass |
| XIV — Browser tests are the exception | None added. Persistence across page loads (FR-009) is theme-change's documented behaviour against a `localStorage` key the guard already reads; the package's own contract is the emitted attributes, which is what gets asserted. | Pass |
| XV — Front-end assets are build artifacts | `mvp/static/css/django-mvp.css` and its brotli sibling are rebuilt and committed on this branch. The stylesheet build is non-deterministic, so size is measured once, in one session, with one tool — never by diffing a fresh build against the committed one. | Pass, with the measurement discipline recorded |
| XVI — Compatibility | Default behaviour is unchanged (FR-006). The config block is additive. CHANGELOG entry required. | Pass |
| XVII — Cohesion | The config block is one cohesive unit read by two templates. | Pass |

**Quality bar**: coverage floors 90% project / 85% patch; `ruff`, `mypy`, `deptry` green; README and
CHANGELOG updated. `djlint` is explicitly not a gate and is not cited as one.

### Complexity Tracking

No constitution violation to justify. One rejected alternative is recorded because it looks cheaper
than it is:

| Considered | Why rejected |
|---|---|
| Ship each theme as its own static file (`mvp/static/css/themes/<name>.css`) and link only the configured one | Saves about 4.8 KB compressed for a project on the default theme, and costs a second HTTP request, a config-dependent asset path, 35 new static files, and a failure mode where a mistyped name yields a 404 rather than a fall-through. Article II settles it: the saving does not pay for the moving parts. |
| Register themes in `MVP_CONFIG` so names can be validated | Rejected at the Spec gate. See decisions.md D5 — the package cannot evaluate the check, because a custom theme lives in a file the package never reads. |

## Project Structure

### Documentation (this feature)

```text
specs/026-ship-prebuilt-daisyui/
├── spec.md          # approved at the Spec gate
├── plan.md          # this file
├── decisions.md     # D1-D7, the evidence behind the spec's clarifications
├── progress.md      # stage and gate log
├── tasks.md         # Phase 2 output
└── feature-state.json
```

No `research.md`, `data-model.md`, `quickstart.md` or `contracts/`: there is no data model, no API
contract, and no open research question. The documentation this feature owes its readers is shipped
in `docs/`, not in the spec directory.

### Source code (repository root)

```text
assets/
├── tailwind.css                  # T001: themes: all
└── demo.css                      # T002: same, so the demo can show them

mvp/
├── config.py                     # T003: the theme config block
├── management/commands/
│   └── mvp_tailwind.py           # T004: parity for Tier 2 entry files
├── static/css/
│   ├── django-mvp.css            # rebuilt artifact
│   └── django-mvp.css.br         # rebuilt artifact
└── templates/
    ├── mvp/base.html             # T006: pre-paint guard reads config
    └── cotton/actions/
        └── theme_controller.html # T008: offered set, two shapes

docs/
├── index.md                      # T012: link the new page
├── styling.md                    # T011: drop the CDN route, point at theming
└── theming.md                    # T010: the page the package has never had

tests/
├── test_smoke.py                 # T005: invert the named-theme guard
├── test_config.py                # T003
├── test_docs.py                  # T013: the variable-coverage contract
└── test_components/
    └── test_theme_controller.py  # T007, T009
```

**Structure Decision**: The existing package layout is unchanged. Every path above already exists
except `docs/theming.md`, `tests/test_docs.py` and `tests/test_components/test_theme_controller.py`.

## Design

### The configuration block

```python
"theme": {
    # Applied when the visitor has expressed no preference. Any name a theme
    # block exists for: one shipped with the package, or one the project loads
    # from its own stylesheet. A name that matches nothing falls through to the
    # default theme, and is not validated - see decisions.md D5.
    "default": "light",
    # Themes the packaged switcher offers, in order. Empty keeps the existing
    # light/dark toggle, so an upgrading project sees no change.
    "choices": [],
},
```

Top-level, a sibling of `brand` rather than a member of `layout`: a theme is appearance, and
`layout` holds structural concerns (sidebar, navbar). `mergedeep` handles the override with no new
code.

### The pre-paint guard

`mvp/base.html` currently hardcodes both the storage key and the fallback:

```js
var theme = localStorage.getItem('theme') || 'light';
```

It becomes a comparison against the configured values, with the offered set and default emitted as
escaped JSON literals rather than interpolated into the script body:

- stored value present **and** (no offered set **or** stored value is in the offered set) → use it;
- otherwise → the configured default.

With nothing configured this evaluates to today's expression exactly, which is what SC-006 asserts.
FR-010 is the membership arm. It is not the validation D5 rejected: the offered set is a list the
project declared, so the package genuinely knows it.

### The switcher, in two shapes

`c-actions.theme-controller` keeps its name, its role and its attribute surface (Article XI):

- **No `choices` configured** — renders exactly today's markup, the `data-toggle-theme="dark,light"`
  checkbox. Byte-for-byte unchanged, asserted by test.
- **`choices` configured** — renders a dropdown of those themes, each entry carrying
  `data-set-theme="<name>"`, which is theme-change's documented API and is present in the shipped
  bundle (verified: `data-set-theme` appears in `mvp/static/js/django-mvp.js`). It writes the same
  `localStorage.theme` key the guard reads, so persistence (FR-009) needs no new code.

The two shapes are a backwards-compatibility requirement, not a variation for its own sake.

### Documentation

`docs/theming.md` is the new page and carries FR-015 through FR-018 and FR-020: what a theme is,
the full variable table, the plugin-is-a-pass-through explanation, the layer/order explanation, a
worked custom-theme example from empty file to rendered page, and the fall-through behaviour.
`docs/styling.md` loses the CDN instructions (FR-019) and links onward.

SC-007 is made mechanical by `tests/test_docs.py`: extract the custom-property names from a shipped
theme definition and assert each appears in `docs/theming.md`. That way a daisyUI upgrade adding a
theme variable fails a test instead of silently ageing the documentation.

## Risks

| Risk | Handling |
|---|---|
| The stylesheet build is not byte-reproducible (Article XV), so SC-003 cannot be measured by diffing a fresh build against the committed artifact | Measure the compressed size of the committed v0.18.0 artifact and of the new one in a single session with one tool, and record both numbers in the PR |
| `tests/test_smoke.py:157` deliberately asserts no named theme ships, written when #190 asked for complete components while excluding themes | Inverted deliberately in T005 with the reason recorded in decisions.md, not edited away as an inconvenience |
| Enabling all themes could change which theme applies by default | Research finding 2 says it does not, and T005 asserts the `:where(:root)` default and the `prefers-color-scheme` block both survive the rebuild |
| A project overriding `base.html` today to set `data-theme` by hand keeps working | It does: the guard is inside the block such a project replaces. Covered as a spec edge case and left alone |
