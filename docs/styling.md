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
django-mvp's own templates happen to use — plus the package's own `mvp` and
`mvp-dark` themes, every daisyUI theme, and the sidebar breakpoint/rail
classes. It is loaded automatically by `mvp/base.html`.

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

## Column behaviour classes

A django-tables2 column says how it competes for width and treats its text
the same way it says anything else about itself: by naming one or more of
these classes in its `attrs`, not by writing raw CSS.

```python
import django_tables2 as tables


class ProductTable(tables.Table):
    name = tables.Column(attrs={"td": {"class": "mvp-col-grow"}})
    sku = tables.Column(attrs={"td": {"class": "mvp-col-shrink"}})
    description = tables.Column(
        attrs={"td": {"class": "mvp-col-wrap mvp-col-max-md"}}
    )
```

| Class | Effect |
| --- | --- |
| `mvp-col-grow` | Claims whatever width is left over once every other column has taken the width it needs. |
| `mvp-col-shrink` | Takes no more width than the column's own content needs, so a short code or date column never stretches to match a longer neighbour. |
| `mvp-col-wrap` | Lets a cell's text wrap onto more than one line instead of stretching the column to fit it on one. |
| `mvp-col-nowrap` | Keeps a cell's text on a single line rather than wrapping the row taller. |
| `mvp-col-max-xs` | Stops a column at a `8rem` maximum width once its text is allowed to wrap. |
| `mvp-col-max-sm` | Stops a column at a `12rem` maximum width once its text is allowed to wrap. |
| `mvp-col-max-md` | Stops a column at a `16rem` maximum width once its text is allowed to wrap. |
| `mvp-col-max-lg` | Stops a column at a `24rem` maximum width once its text is allowed to wrap. |
| `mvp-col-max-xl` | Stops a column at a `32rem` maximum width once its text is allowed to wrap. |

Maximum width comes from this fixed set of named classes rather than a
number the table author supplies — nothing here is generated at runtime, so
every class a table can use already exists in the built stylesheet.

Grow and shrink are opposites, and naming both on the same column is a
contradiction the stylesheet does not resolve for you: the later declaration
in the merged class list wins, which is an accident of ordering rather than
a decision either name is allowed to rely on. Choose one.

### Put the width classes on the heading too

A table lays out with `table-layout: auto`, which negotiates each column's
width across every cell in it — heading included. A heading longer than
anything in the body will therefore win the argument, and `mvp-col-shrink`
or `mvp-col-max-md` on the `td` alone comes out looking like it did nothing.
Where a column's heading is the long part, name the class on both:

```python
sku = tables.Column(
    attrs={"td": {"class": "mvp-col-shrink"}, "th": {"class": "mvp-col-shrink"}}
)
```

The wrap classes are the exception, and deliberately: headings wrap whatever
the project-wide default says, so that a column is never widened by its own
title. Only cell text is held to one line, because cell text is
arbitrary-length and keeping one row per record is what makes a long table
scannable. Name `mvp-col-nowrap` on the `th` yourself if a particular
heading must stay on one line.

### The project-wide wrap default

Whether a column wraps at all when it names neither `mvp-col-wrap` nor
`mvp-col-nowrap` itself is a project setting, not a per-column guess:

```python
MVP_CONFIG = {
    "table": {
        "wrap": True,  # every column wraps unless it says mvp-col-nowrap
    },
}
```

The shipped default is `False` — a column stays on one line unless it or the
project says otherwise. Resolution order is the column's own class first,
then this setting, then the package default.

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

Themes are pure CSS custom properties, so they apply with no build step in either
tier. With nothing configured, pages render in `mvp`, the package's own theme, and
the packaged toggle switches to `mvp-dark`. Set the applied theme, its dark
partner and the switcher's offered set through `MVP_CONFIG["theme"]`, and use
`<c-actions.theme-controller />` (included in the default navbar config) to let
visitors switch between them.

See [Theming](theming.md) for the packaged pair and how to replace it, the full
variable reference, why the theme plugin computes nothing, why a project's own
theme overrides a packaged one regardless of load order, and a worked example of
writing one from scratch.

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
  fails if it no longer compiles. It cannot check the committed
  `django-mvp.css` against that rebuild, because the Tailwind and daisyUI
  build is not byte-reproducible — an identical toolchain gives different
  bytes on consecutive runs. Keeping the committed artifact current is
  therefore the author's job, not the pipeline's. Never hand-edit the built
  files: rebuild them.
- The rail-mode CSS in the preset is intentionally **unlayered** so it beats
  DaisyUI's `@layer` rules; don't move it into `@layer components`.
