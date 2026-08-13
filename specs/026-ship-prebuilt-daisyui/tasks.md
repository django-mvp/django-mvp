# Tasks: Themes that ship with the package

**Branch**: `026-ship-prebuilt-daisyui` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Test-first throughout (Article I): each task writes or changes its assertion before the code that
satisfies it. `[P]` marks tasks that touch disjoint files and may run in parallel within their phase.

## Phase 1 — Foundational

Blocks every story. Runs sequentially.

### T001 — Replace the named-theme exclusion guard

**Files**: `tests/test_smoke.py`

`test_smoke.py` currently asserts, over a parametrised list of named themes, that `[data-theme=<name>]`
is **absent** from the shipped stylesheet, with a comment citing #190. This feature reverses that
intent deliberately. Replace the guard with its inverse and add the two invariants that protect
FR-006:

1. Every theme the pinned daisyUI version publishes has a `[data-theme=<name>]` block in
   `mvp/static/css/django-mvp.css`. Read the list from `node_modules/daisyui/theme/*.css` rather than
   hardcoding 35 names, so a daisyUI upgrade cannot silently drop one.
2. The default theme is still bound through `:where(:root)` — the zero-specificity arm that makes an
   unmatched `data-theme` value fall through (FR-014, SC-008).
3. A `@media (prefers-color-scheme: dark)` block is still emitted, so the pre-existing dark-mode
   behaviour survives the build change.

Record in `decisions.md` that the guard was reversed on purpose, citing #190 as the original intent
and this spec as the superseding one. **Do not delete the original reasoning.**

**Fails until T002.** That is the point.

**Verifies**: FR-001, FR-006 · **Blocks**: T002

---

### T002 — Enable every prebuilt theme in the stylesheet build

**Files**: `assets/tailwind.css`, `mvp/static/css/django-mvp.css`, `mvp/static/css/django-mvp.css.br`

Change the bare `@plugin "daisyui";` to enable all themes:

```css
@plugin "daisyui" {
  themes: all;
}
```

`daisyui/functions/pluginOptionsHandler.js` shows the `all` branch applies `light` with `--default`
and `dark` under `@media (prefers-color-scheme: dark)` before emitting the rest, which is exactly the
bare default's behaviour plus the remaining themes. T001's invariants are what prove that here rather
than on trust.

Rebuild the committed artifacts with `invoke build-stylesheet` and commit both.

**Measurement discipline (Article XV)**: the build is not byte-reproducible, so do **not** diff a
fresh build against the committed artifact to judge staleness. Record the compressed size of the
pre-change committed `django-mvp.css.br` and of the new one, measured in the same session with the
same tool, and carry both numbers into the completion report for SC-003.

**Verifies**: FR-001, FR-002, FR-004, SC-003 · **Depends on**: T001

---

### T003 — Add the `theme` block to `MVP_CONFIG`

**Files**: `mvp/config.py`, `tests/test_config.py`

Test first: the merged config exposes `theme.default == "light"` and `theme.choices == []` with no
project override, and a project override of either key merges without disturbing the other or any
sibling block.

Then add the block as a top-level sibling of `brand` (not inside `layout` — a theme is appearance,
`layout` holds structural concerns), with the comments the plan specifies, including the note that a
name matching nothing falls through and is not validated.

**Verifies**: FR-003, FR-007 · **Blocks**: T004, T006, T007

---

## Phase 2 — US-1: Apply a prebuilt theme by configuration (P1)

Delivers issue #231. Independently shippable: at the end of this phase a project sets one value and
its application is themed.

### T004 — Pre-paint guard reads the configured theme

**Files**: `mvp/templates/mvp/base.html`, `tests/test_components/test_theme_controller.py`

Test first, against rendered markup (Article XIII):

- with nothing configured, the inline guard resolves to the same behaviour as v0.18.0 — stored value
  if present, otherwise `light` (SC-006);
- with `theme.default` set, an absent stored value yields that theme;
- the configured values reach the script as escaped JSON literals, not as raw interpolation into the
  script body (Article V) — assert that a value containing a quote or `</script>` cannot break out.

Then change the guard. Keep it inline and pre-paint (FR-005): it must stay the first thing in
`<head>`, before any stylesheet link.

**Verifies**: FR-003, FR-005, FR-006 · **Depends on**: T003

---

### T005 — A name that matches nothing falls through

**Files**: `tests/test_components/test_theme_controller.py`

No production code. Assert the behaviour D5 settled: a configured theme name with no matching block
leaves the document rendering under the `:where(:root)` default, and nothing raises. This is a
regression guard on a deliberate non-feature — without it, a later contributor reads the absence of
validation as an oversight and adds it back.

**Verifies**: FR-014, SC-008 · **Depends on**: T002, T004

---

## Phase 3 — US-2: Let visitors choose from the themes a project offers (P2)

Delivers issue #232.

### T006 — Pin the unconfigured switcher shape, then add the offered-set shape

**Files**: `mvp/templates/cotton/actions/theme_controller.html`,
`tests/test_components/test_theme_controller.py`

Test first, in two halves:

1. **Unchanged shape.** With `theme.choices` empty, the component renders today's markup: the
   `data-toggle-theme="dark,light"` checkbox, its `data-act-class`, both icons and the translated
   label. Write this assertion against the *current* template and confirm it passes **before**
   touching the template, so it is a genuine regression guard rather than a description of whatever
   the change produced.
2. **Offered-set shape.** With `theme.choices` populated, the component renders one entry per
   configured theme, in the configured order, each carrying `data-set-theme="<name>"` — theme-change's
   documented API, present in the shipped bundle. Entries carry accessible names (Article XIII) and
   the control's label goes through `gettext` (Article VIII).

The component gains no new attribute (Article XI): the set comes from `MVP_CONFIG`, per Article XII's
resolution order.

**Verifies**: FR-007, FR-008, FR-009, FR-006 · **Depends on**: T003

---

### T007 — Fall back when a stored selection is no longer offered

**Files**: `mvp/templates/mvp/base.html`, `tests/test_components/test_theme_controller.py`

Test first: with `theme.choices` populated, a stored value outside that set resolves to
`theme.default`; a stored value inside it is honoured. With `theme.choices` empty, any stored value is
honoured, which is the v0.18.0 behaviour.

This membership check is **not** the validation rejected in D5. The offered set is a list the project
declared, so the package genuinely knows it. A theme name it was never given remains unvalidated.

**Verifies**: FR-010 · **Depends on**: T004, T006

---

## Phase 4 — US-3: Write and apply a theme of your own (P3)

Delivers issue #233. Mostly documentation, with the two contracts that keep it honest.

### T008 — Write `docs/theming.md`

**Files**: `docs/theming.md`

The page the package has never had. It must carry, in this order:

1. **What a theme is** — a block of CSS custom properties under `[data-theme="<name>"]`, read at
   runtime, requiring no build step (FR-016).
2. **The full variable table** — every variable a theme may define, with what each controls. Derive
   the list from a shipped theme definition rather than from memory; the colour variables, their
   `-content` pairs, `--radius-*`, `--size-*`, `--border`, `--depth`, `--noise` and `color-scheme`
   (FR-015).
3. **The plugin is a pass-through** — `@plugin "daisyui/theme"` emits exactly the properties it is
   given and computes none of them, so a hand-written file and a generated one are equivalent
   (FR-016). This is the point readers most often get wrong, and it is why no build step is needed.
4. **Why your theme wins** — packaged themes sit in a cascade layer, a plain theme file does not, and
   unlayered rules beat layered ones whatever the load order. So a project must **not** write ordering
   assumptions into its base template (FR-017).
5. **A worked example** — from an empty file to a rendered page: write the block, load the stylesheet,
   name the theme in `MVP_CONFIG`, see it applied. No step omitted (FR-018).
6. **When your theme does not appear** — a name matching nothing falls through to the default without
   an error, so check the name and that the stylesheet is loading before suspecting the CSS (FR-020).
7. **Where theming stops** — the boundary between what a theme can change and where a component
   override takes over, which is R18's third deliverable.

Public markdown: humanized before commit, no internal handles.

**Verifies**: FR-015, FR-016, FR-017, FR-018, FR-020, SC-005

---

### T009 — Rewrite the theming parts of `docs/styling.md` and link the new page

**Files**: `docs/styling.md`, `docs/index.md`

- Delete the "Want a named theme that isn't light or dark?" section, whose entire content is a
  jsDelivr `<link>` (FR-019).
- Correct the Tier 1 paragraph that says only the default light and dark themes ship and that shipping
  the rest "would bloat the stylesheet for every project". Both statements become false with T002, and
  the second was never measured — about 5 KB compressed for all 35.
- Point the theming section at `docs/theming.md` rather than restating it. One page owns theming.
- Add a `docs/index.md` row for the new page, matching the existing table's style.

**Verifies**: FR-019 · **Depends on**: T008

---

### T010 — Make the variable coverage mechanical

**Files**: `tests/test_docs.py`

Extract the custom-property names from a shipped theme definition under `node_modules/daisyui/theme/`
and assert every one appears in `docs/theming.md`. A daisyUI upgrade that adds a theme variable then
fails a test instead of silently ageing the documentation.

Skip cleanly when `node_modules` is absent, so the suite still runs for a contributor who has not
installed the front-end toolchain — the same convention the repo already uses for build-artifact
tests.

**Verifies**: SC-007 · **Depends on**: T008

---

### T011 — Define *theme* in the glossary

**Files**: `CONTEXT.md`

Add a `### Theme` entry under Core Concepts, in the register of its neighbours: what a theme is, that
it carries no structure or layout, and that this is why changing one never requires a template change.
Reference the two sources — shipped and project-written.

**Verifies**: FR-021

---

### T012 — Tier 2 parity in the generated entry file

**Files**: `mvp/management/commands/mvp_tailwind.py`, `tests/test_management_commands.py`

`ENTRY_TEMPLATE` emits a bare `@plugin "daisyui";`, so a project that builds its own stylesheet gets
only light and dark while a no-build project gets all 35. That inverts the tiering: the project doing
more work would get less. Emit the same `themes: all` block, and assert it.

**Verifies**: FR-004, FR-011, FR-013 · **Depends on**: T002

---

### T013 — Show it in the demo

**Files**: `assets/demo.css`, `demo/` theme page, `mvp/static/css/` demo artifact if built separately

Enable all themes in the demo's own stylesheet entry and extend the existing theme page so the
switcher is exercised with a configured `choices` set and a project-written custom theme. This is the
evidence for SC-002 and the reference a reader checks against `docs/theming.md`.

**Verifies**: SC-002, SC-005 · **Depends on**: T002, T006, T008

---

## Phase 5 — Polish

### T014 — README and CHANGELOG

**Files**: `README.md`, `CHANGELOG.md`

Required by the quality bar for any public API change. The `theme` config block is public API. State
the added capability and that default behaviour is unchanged.

**Depends on**: everything above

---

### T015 — Full verification

Run `forge verify` (lint, format, typecheck, dependency check, full suite), confirm coverage floors
hold (project ≥ 90%, patch ≥ 85%), and record the measured compressed stylesheet sizes from T002
against SC-003's 8 KB bound.

**Depends on**: T014

---

## Dependency summary

```text
T001 → T002 ─┬→ T005
             ├→ T012
             └→ T013
T003 ─┬→ T004 ─┬→ T005
      │        └→ T007
      └→ T006 ─┬→ T007
               └→ T013
T008 ─┬→ T009
      ├→ T010
      └→ T013
T011 [P]
everything → T014 → T015
```

## Parallel opportunities

`T008` and `T011` are documentation-only and share no file with the Phase 1–3 code tasks, so the US-3
documentation can be written while US-1 and US-2 are implemented. Phase 1 remains strictly
sequential: T001 must fail before T002 makes it pass.
