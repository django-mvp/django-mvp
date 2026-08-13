# Styling, Tailwind & Extending the CSS

django-mvp is styled with **Tailwind CSS v4** and **DaisyUI 5**. The package
ships a prebuilt stylesheet, so most projects need **no build tooling at all**.
Projects that write their own Tailwind classes rebuild the CSS themselves with
one generated file.

## Which tier am I?

| You... | Tier |
| --- | --- |
| Use the packaged components and configure them via attributes and `MVP_CONFIG` | **Tier 1 — no build** |
| Write your own templates with your own Tailwind utility classes | **Tier 2 — own build** |

## Tier 1: no build step

The packaged stylesheet (`mvp/static/css/django-mvp.css`) contains the
**complete daisyUI 5 component set** — every component, not just the ones
django-mvp's own templates happen to use — plus every daisyUI theme and the
sidebar breakpoint/rail classes. It is loaded automatically by `mvp/base.html`.

The contract that makes this work: **customize through component attributes and
template overrides that reuse packaged components — not raw utility classes**.
A template override that only composes existing components (`<c-card>`,
`<c-button variant="primary">`, a raw `<div class="chat chat-start">`, ...)
needs no CSS rebuild. The stylesheet also carries a curated set of common
Tailwind utility classes — layout, spacing, sizing, typography, colour and
state — so `class="grid grid-cols-3"` works in Tier 1 too. See [Utility
Classes](utility-classes.md) for the full list. The moment you reach for a
utility class outside that list, or an arbitrary value like `w-[37px]`, you're
in Tier 2: those were never scanned from django-mvp's own templates and don't
exist in the prebuilt stylesheet.

Theme changes (colors, radius, borders) do **not** require Tier 2. See
[Theming](#theming) below.

## Tier 2: build your own stylesheet

Your build must scan **both** your templates **and** django-mvp's packaged
templates. django-mvp generates the Tailwind entry file for you:

```bash
# 1. Install build tooling (once)
npm install -D tailwindcss @tailwindcss/cli daisyui

# 2. Generate the entry file (re-run after upgrading django-mvp)
python manage.py mvp_tailwind > assets/tailwind.css

# 3. Build
npx @tailwindcss/cli -i assets/tailwind.css -o static/css/app.css --minify
```

Then load your stylesheet instead of the packaged one by overriding the
`head` block (or just the stylesheet links) of `mvp/base.html`.

The generated entry file:

- imports Tailwind with `source(none)` and lists sources explicitly, so builds
  are deterministic;
- imports the **django-mvp preset** (`mvp/tailwind/base.css` inside the
  installed package) — the drawer-state variants (`is-drawer-open:`,
  `is-drawer-close:`), the safelisted `{sm..2xl}:drawer-open` breakpoint
  classes, and the icon-rail CSS;
- adds a `@source` for django-mvp's packaged templates (absolute path resolved
  from your environment);
- adds `@source "./templates"` as a starting point for your own code — add one
  line per directory that contains Tailwind classes.

Prefer wiring it yourself? `python manage.py mvp_tailwind --paths` prints the
two package paths (preset CSS, templates directory) and nothing else.

### Why this is necessary

Tailwind generates only the classes it finds in scanned source files. The
prebuilt stylesheet was scanned against django-mvp's templates — your
templates weren't there. Rebuilding with both `@source` lines closes the gap.

## Theming

DaisyUI themes are pure CSS custom properties, so they apply with no build step in
either tier. Set the applied theme and the switcher's offered set through
`MVP_CONFIG["theme"]`, and use `<c-actions.theme-controller />` (included in the
default navbar config) to let visitors switch between them.

See [Theming](theming.md) for the full variable reference, why the theme plugin
computes nothing, why a project's own theme overrides a packaged one regardless of
load order, and a worked example of writing one from scratch.

## For django-mvp developers

- Source of truth: `assets/tailwind.css` (entry) + `mvp/tailwind/base.css`
  (shared preset, shipped in the wheel).
- `assets/tailwind.css` scans `node_modules/daisyui/{components,utilities}`
  (installed via `npm ci`) as content, not just `../mvp`, so that every
  daisyUI class is forced into the build regardless of what mvp's own
  templates use. Removing those two `@source` lines silently shrinks Tier 1
  back down to the components mvp itself renders.
- Build: `invoke build-stylesheet` (runs `npm run build:css:prod` and
  brotli-compresses the output). Both artifacts are committed.
- CI: `.github/workflows/stylesheet.yml` rebuilds the CSS on every PR and
  fails if the committed `django-mvp.css` is stale — never hand-edit the
  built files.
- The rail-mode CSS in the preset is intentionally **unlayered** so it beats
  DaisyUI's `@layer` rules; don't move it into `@layer components`.
