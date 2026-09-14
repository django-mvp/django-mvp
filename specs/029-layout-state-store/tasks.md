# Tasks — 029 Layout state store and static responsive visibility

**Branch**: `029-layout-state-store` · **Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed.

*Revised after design review: the configuration payload moved into the foundational phase, the
stories were declared sequential, the characterisation tests changed form, and three under-scoped
task file lists were corrected. The reasoning is in `decisions.md` D7.*

## Order

**Phase 0 → US-1 → US-2 → US-3, one at a time.** The stories are not dispatched in parallel: they
share the committed bundle artifact, the store module, two test modules, the drawer template and
two documentation pages. The reasoning is in plan.md under *Story order*.

---

## Phase 0 — Foundational (sequential, before any story)

Shared ground every story reads.

### T001 — The resolver

**Files**: `mvp/layout.py` (new), `tests/test_layout.py` (new)

Build `LayoutConfig`: one class carrying the shell's resolved layout facts, constructed from the
breakpoint and collapse values a page has already resolved. Properties per plan.md's table, plus
`as_dict()` for the client payload.

Normalisation lives here and nowhere else: `never` or `none` in any case means the sidebar is never
persistent, an unrecognised breakpoint name falls back to `lg`, and a persistent breakpoint carries
its width in pixels.

Tests cover every supported value, both spellings of the disabled case in mixed case, the
unrecognised fallback, and the dictionary's exact keys. Include the disabled case's pixel width
explicitly — see T002.

### T002 — The surviving tags read the resolver

**Files**: `mvp/templatetags/mvp.py`, `tests/test_components/test_layout_config.py`

`sidebar_breakpoint_class`, `breakpoint_px` and `sidebar_has_breakpoint` become thin readers of
`LayoutConfig` instead of three separate implementations of the same normalisation. Add the tag
that resolves a `LayoutConfig` for a template to use.

Their existing tests are not modified — they are the proof the refactor changed no behaviour.

**One behaviour the existing tests do not pin**: `breakpoint_px` currently returns `1024` for
`never`, because the disabled value is not a key and takes the `lg` fallback. Nothing asserts it.
Keep that return value for the tag, and let `LayoutConfig` carry the honest nullable property for
the payload alongside it. Add a test for both, so the difference is deliberate and visible rather
than discovered later.

### T003 — The configuration payload

**Files**: `mvp/templates/cotton/layout/sidebar/index.html`,
`tests/test_components/test_layout_config.py`

Emit `LayoutConfig.as_dict()` through Django's `json_script` filter, from the drawer component —
not from `mvp/base.html`. A project overriding the base template writes its own and would lose a
payload that lived there, which is the same failure the attributes are placed to avoid.

Rendered-template tests assert the payload is present, carries every documented key, and reflects a
per-page override rather than the project default.

---

## US-1 (P1) — A project's markup reacts to the shell's layout state

Issue #347. Requirements FR-001 to FR-008, FR-021, FR-023.

### T004 — The store

**Files**: `assets/js/layout.js` (new), `assets/js/index.js`

Register one Alpine store named `layout`, **after `Alpine.plugin(persist)` and before
`Alpine.start()`**. The persist plugin is what defines `Alpine.$persist`, so a store registered
earlier cannot hold a persisted property; registering before `start()` alone is not enough.

At this task the store carries: the sidebar's open state, read from the drawer checkbox at `init()`;
the remembered desktop state as a persisted property; the collapse mode; whether the header is
stuck. It parses the T003 payload for what it needs, including the pixel width.

A page that renders no shell — the entrance page, the error pages — has no payload and no drawer.
The store must register, report package defaults and report the sidebar closed, without throwing.

Rebuild `mvp/static/js/django-mvp.js` and commit it.

### T005 — The drawer binds to the store, and the seed is defined once

**Files**: `mvp/templates/cotton/layout/sidebar/index.html`, `assets/js/layout.js`,
`tests/test_components/test_sidebar_persisted_state.py`

The checkbox binds to the store's sidebar state instead of local component state.

The blocking pre-paint script becomes the **single definition** of the persisted default and the
storage key. It resolves the value before first paint exactly as it does now, and renders both the
key and the value it resolved into the drawer's markup. The store takes its persisted property's
key and initial value from that markup rather than restating either.

This is what FR-006 and SC-002 actually ask for. Moving the persisted expression onto the store
without this step carries the duplication along with it: the default `true` and the key would still
be written in two places.

Extend the existing #178 regression test rather than replacing it. It must still prove no width
animation on a restoring load, and must now also prove the store agrees with what is on screen.
Add an assertion that the default and the key appear exactly once in the rendered page.

### T006 — The header's stuck state moves to the store

**Files**: `mvp/templates/cotton/app/header/index.html`

The scroll handler writes to the store instead of local component state. The shadow behaviour is
unchanged: the header still gains its shadow on scroll and loses it at the top, and the store
reports the same thing.

### T007 — Correct state after a boosted navigation

**Files**: `assets/js/layout.js`, `assets/js/index.js`

In the existing `htmx:afterSettle` handler, when the swap target was the body, re-derive the
sidebar state: open only when the viewport is wide and the remembered desktop state says so. This
reproduces today's behaviour, where a mobile overlay closes on navigation and a desktop sidebar
does not.

Rebuild the bundle.

### T008 — The store's behaviour, in a browser

**Files**: `tests/test_components/test_layout_store.py` (new)

Browser tests only for what a rendered template cannot show:

- the store exists on a shell page and reports the sidebar state, collapse mode and stuck state;
- an element bound to the sidebar state follows every control the shell ships (navbar toggle,
  sidebar header toggle, drawer overlay);
- a boosted navigation leaves the store correct, asserted at a wide viewport **and** a narrow one;
- with JavaScript disabled the shell renders and the sidebar still opens and closes;
- a page that renders no shell still gets a store, reporting defaults and not throwing.

### T009 — The store as a documented extension point

**Files**: `docs/layout.md`, `CONTEXT.md`, `skills/django-mvp/references/layout.md`, `demo/`

Document the store as public surface, with a worked example of a project element reacting to the
shell. Add the store to the domain vocabulary. Add one demo page that uses it, so the example in
the documentation is a page that actually runs.

---

## US-2 (P2) — A project reads the shell's resolved configuration

Issue #348. Requirements FR-009, FR-010, FR-013, FR-014.

*(FR-011 and FR-012 are delivered by T003 in the foundational phase: the payload has to exist before
the store can parse it, and both the store and the stylesheet attributes read the same resolver.
The spec's coverage table was corrected to match — no requirement was dropped or added.)*

### T010 — The configuration the store reports

**Files**: `assets/js/layout.js`

The store reports the full resolved configuration as a named surface: breakpoint, pixel width,
collapse mode, sticky, boost. Build the viewport flag from the pixel width with a `matchMedia`
listener, so it stays current as the window is resized. Where the sidebar is never persistent the
store says so and the flag stays false, rather than reporting a width that means nothing.

Rebuild the bundle.

### T011 — The configuration's behaviour, in a browser

**Files**: `tests/test_components/test_layout_store.py`

The store reports a per-page override rather than the project default; the viewport flag flips in
both directions across the configured breakpoint without a reload; the never-persistent case
reports correctly.

### T012 — Document the configuration half

**Files**: `docs/layout.md`, `skills/django-mvp/references/layout.md`

The keys the store carries and what each one means.

---

## US-3 (P3) — Responsive visibility from the stylesheet

Issue #349. Requirements FR-015 to FR-020, FR-022.

### T013 — Characterise the current behaviour first

**Files**: `tests/test_components/test_responsive_visibility.py` (new)

Write these tests against the package **as it is today**, and get them green before touching
anything.

**Assert computed visibility in a real browser** — the resolved `display` of each region at a width
below and a width at or above each setting. **No assertion may name a class string.** The class
strings are the mechanism under substitution, so an assertion on them either pins the old mechanism
and has to be rewritten, or pins the new one and never said anything about the old. Computed
visibility is indifferent to how visibility is achieved, which is the whole point. Record the
Article XIV justification in the module docstring: this equivalence is not expressible from
rendered HTML once the mechanism moves into the stylesheet.

The matrix: four governed regions, six breakpoint settings **including `never`**, an unrecognised
setting, both collapse modes, two viewport widths.

This ordering is the task's point. A test written after the tags are gone proves only that the new
code does what the new code does.

### T014 — The shell renders the attributes

**Files**: `mvp/templates/mvp/base.html`, `mvp/templates/cotton/app/index.html`,
`mvp/templates/cotton/layout/sidebar/index.html`, `tests/test_components/test_layout_config.py`

The drawer element gains the resolved breakpoint and collapse mode as attributes.

**The collapse mode does not reach the drawer today** and has to be threaded there: `base.html`
resolves it and passes it to the sidebar and the header only, and `cotton/app/index.html` declares
no such variable, so it cannot forward what it never received. Declare it on both components'
variable blocks, defaulting to the configured value, and pass it down from `base.html`.

Rendered-template tests assert both attributes, that an unrecognised breakpoint is rendered already
normalised, and that a per-page override is what appears.

### T015 — The rules move into the stylesheet and the tags go

**Files**: `mvp/tailwind/base.css`, `mvp/templates/cotton/app/header/navbar.html`,
`mvp/templates/mvp/account/base.html`, `mvp/templatetags/mvp.py`,
`tests/test_components/test_responsive_safelist.py`, `tests/test_components/test_layout_config.py`,
`tests/test_views/test_account.py`

Add one media block per supported breakpoint to the preset, selecting on the attributes from T014,
and give the four regions their semantic classes.

**One extra rule, easily missed.** Under `never`, two of the three classes want their unconditional
state and get it by no media block matching. The third does not: `navbar_narrow_only_class` returns
`hidden` under `never`, so that a project reads one set of header actions rather than two stacked
copies. Write that one explicitly — hide the narrow-only region under that attribute value — or the
mobile copy appears at every width in that setting.

Delete `navbar_wide_only_class`, `navbar_narrow_only_class` and `sidebar_navbar_toggle_class`, the
three safelist entries that existed for them, the safelist test's case for them, and the tag-level
tests in `test_layout_config.py`.

`tests/test_views/test_account.py` asserts the two removed tags' literal output at lines 177 and
181, and names one of them in a docstring. Restate both against the semantic classes and update the
docstring.

**Two rules about changing tests, and they are not the same rule.** T013's characterisation tests
must pass unmodified — if one needs changing to go green, the substitution changed behaviour and
the change is wrong, not the test. Tests that assert the removed mechanism *by name* are expected
to change, because their subject is being deleted.

### T016 — Prove it without JavaScript, and rebuild

**Files**: `tests/test_components/test_responsive_visibility.py`

One browser test at a representative setting with JavaScript disabled, proving visibility is
identical. Rebuild `mvp/static/css/django-mvp.css` and its compressed sibling, and commit them.

### T017 — Record the removal

**Files**: `CHANGELOG.md`, `docs/layout.md`, `skills/django-mvp/references/layout.md`

A breaking-change entry naming the three tags and stating what replaced them.

---

## Dependencies

- T001 → T002 → T003 → everything.
- US-1: T004 → T005, T006, T007 → T008 → T009.
- US-2: T010 → T011 → T012.
- US-3: T013 → T014 → T015 → T016 → T017.
- Between stories: sequential, in the order above.

## Out of scope for every task

No change to what the shell renders or how it looks. No new configuration key. No new dependency.
No change to the drawer-open class or the drawer-state variants.
