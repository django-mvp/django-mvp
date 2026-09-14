# Tasks — 029 Layout state store and static responsive visibility

**Branch**: `029-layout-state-store` · **Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed.

## Phase 0 — Foundational (sequential, before any story)

Both tasks are shared ground that all three stories read. Nothing else starts until they are done.

### T001 — The resolver

**Files**: `mvp/layout.py` (new), `tests/test_layout.py` (new)

Build `LayoutConfig`: one class carrying the shell's resolved layout facts, constructed from the
breakpoint and collapse values a page has already resolved. Properties per the plan's table, plus
`as_dict()` for the client payload.

Normalisation lives here and nowhere else: `never` or `none` in any case means the sidebar is
never persistent, an unrecognised breakpoint name falls back to `lg`, and a persistent breakpoint
carries its width in pixels.

Tests cover every supported value, both spellings of the disabled case in mixed case, the
unrecognised fallback, and the dictionary's exact keys.

### T002 — The surviving tags read the resolver

**Files**: `mvp/templatetags/mvp.py`, `tests/test_components/test_layout_config.py`

`sidebar_breakpoint_class`, `breakpoint_px` and `sidebar_has_breakpoint` become thin readers of
`LayoutConfig` instead of three separate implementations of the same normalisation. Add the tag
that resolves a `LayoutConfig` for a template to use.

Their existing tests are not modified — they are the proof the refactor changed no behaviour.

---

## US-1 (P1) — A project's markup reacts to the shell's layout state

Issue #347. Requirements FR-001 to FR-008, FR-021, FR-023.

### T003 — The store

**Files**: `assets/js/layout.js` (new), `assets/js/index.js`

Register one Alpine store named `layout`, before the existing `Alpine.start()` call so its `init()`
runs ahead of the DOM walk (research R1). At this task it carries the live state only: whether the
sidebar is open, read from the drawer checkbox at init; the collapse mode; whether the header is
stuck. The remembered desktop state moves here as a persisted property under the storage key the
sidebar already uses, so an upgrading project keeps what its users had.

Rebuild `mvp/static/js/django-mvp.js` and commit it.

### T004 — The drawer binds to the store

**Files**: `mvp/templates/cotton/layout/sidebar/index.html`,
`tests/test_components/test_sidebar_persisted_state.py`

The checkbox binds to the store's sidebar state instead of local component state. The blocking
pre-paint script stays exactly as it is — it is what makes the ordering work.

Extend the existing #178 regression test rather than replacing it: it must still prove no width
animation on a restoring load, and must now also prove the store agrees with what is on screen.

### T005 — The header's stuck state moves to the store

**Files**: `mvp/templates/cotton/app/header/index.html`

The scroll handler writes to the store instead of local component state. The shadow behaviour is
unchanged, so the assertion is that the header still gains its shadow on scroll and loses it at the
top, and that the store reports the same thing.

### T006 — Correct state after a boosted navigation

**Files**: `assets/js/layout.js`, `assets/js/index.js`

In the existing `htmx:afterSettle` handler, when the swap target was the body, re-derive the
sidebar state: open only when the viewport is wide and the remembered desktop state says so. This
reproduces today's behaviour, where a mobile overlay closes on navigation and a desktop sidebar
does not.

Rebuild the bundle.

### T007 — The store's behaviour, in a browser

**Files**: `tests/test_components/test_layout_store.py` (new)

Browser tests only for what a rendered template cannot show:

- the store exists on a shell page and reports the sidebar state, collapse mode and stuck state;
- an element bound to the sidebar state follows every control the shell ships (navbar toggle,
  sidebar header toggle, drawer overlay);
- a boosted navigation leaves the store correct, asserted at a wide viewport **and** a narrow one;
- with JavaScript disabled the shell renders and the sidebar still opens and closes.

### T008 — The store as a documented extension point

**Files**: `docs/layout.md`, `CONTEXT.md`, `skills/django-mvp/references/layout.md`, `demo/`

Document the store as public surface, with a worked example of a project element reacting to the
shell. Add the store to the domain vocabulary. Add one demo page that uses it, so the example in
the documentation is a page that actually runs.

---

## US-2 (P2) — A project reads the shell's resolved configuration

Issue #348. Requirements FR-009 to FR-014.

### T009 — The configuration payload

**Files**: `mvp/templates/mvp/base.html`, `tests/test_components/test_layout_config.py`

Emit `LayoutConfig.as_dict()` through Django's `json_script` filter. Rendered-template tests assert
the payload is present, carries every documented key, and reflects a per-page override rather than
the project default.

### T010 — The store hydrates from the payload

**Files**: `assets/js/layout.js`

Parse the payload in `init()`. Build the viewport flag from the pixel width with a `matchMedia`
listener, so it stays current as the window is resized. Where the sidebar is never persistent the
store says so and the flag stays false rather than reporting a meaningless width.

Rebuild the bundle.

### T011 — The configuration's behaviour, in a browser

**Files**: `tests/test_components/test_layout_store.py`

The store reports a per-page override; the viewport flag flips in both directions across the
configured breakpoint without a reload; the never-persistent case reports correctly.

### T012 — Document the configuration half

**Files**: `docs/layout.md`, `skills/django-mvp/references/layout.md`

The keys the store carries and what each one means.

---

## US-3 (P3) — Responsive visibility from the stylesheet

Issue #349. Requirements FR-015 to FR-020, FR-022.

### T013 — Characterise the current behaviour first

**Files**: `tests/test_components/test_responsive_visibility.py` (new)

Write the tests against the package **as it is today**, and get them green before touching
anything. They assert, for each of the four governed regions, at all six breakpoint settings, at an
unrecognised setting, and in both collapse modes, which regions are hidden and which are shown.

This ordering is the task's point. A test written after the tags are gone proves only that the new
code does what the new code does.

### T014 — The shell renders the attributes

**Files**: `mvp/templates/cotton/layout/sidebar/index.html`,
`tests/test_components/test_layout_config.py`

The drawer element gains the resolved breakpoint and collapse mode as attributes. Rendered-template
tests assert both, including that an unrecognised breakpoint is rendered already normalised, and
that a per-page override is what appears.

### T015 — The rules move into the stylesheet and the tags go

**Files**: `mvp/tailwind/base.css`, `mvp/templates/cotton/app/header/navbar.html`,
`mvp/templates/mvp/account/base.html`, `mvp/templatetags/mvp.py`,
`tests/test_components/test_responsive_safelist.py`, `tests/test_components/test_layout_config.py`

Add one media block per supported breakpoint to the preset, selecting on the attributes from T014.
Give the four regions their semantic classes. Delete `navbar_wide_only_class`,
`navbar_narrow_only_class` and `sidebar_navbar_toggle_class`, the safelist entries that existed for
them, the safelist test's case for them, and the tag-level tests in `test_layout_config.py`.

T013's tests must still pass, unmodified. If one needs changing to go green, the substitution
changed behaviour and the change is wrong, not the test.

### T016 — Prove it without JavaScript, and rebuild

**Files**: `tests/test_components/test_responsive_visibility.py`

One browser test at a representative setting with JavaScript disabled, proving visibility is
identical. Rebuild `mvp/static/css/django-mvp.css` and its compressed sibling, and commit them.

### T017 — Record the removal

**Files**: `CHANGELOG.md`, `docs/layout.md`, `skills/django-mvp/references/layout.md`

A breaking-change entry naming the three tags and stating what replaced them.

---

## Dependencies

- T001 → T002 → everything.
- Within US-1: T003 → T004, T005, T006 → T007 → T008.
- Within US-2: T009 → T010 → T011 → T012. US-2 needs T003 (the store exists).
- Within US-3: T013 → T014 → T015 → T016 → T017. Independent of US-1 and US-2 beyond Phase 0.

## Out of scope for every task

No change to what the shell renders or how it looks. No new configuration key. No new dependency.
No change to the drawer-open class or the drawer-state variants.
