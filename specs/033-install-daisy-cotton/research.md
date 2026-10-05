# Research: Install daisy-cotton alongside the package, with no visible change

Investigated on 2026-10-05 against `main` at `bd63880` and daisy-cotton 0.1.2 as published on PyPI
and installed into this repository's environment. Every claim about daisy-cotton cites the
installed package, at `.venv/lib/python3.13/site-packages/daisy_cotton/`.

## Planning notes, answered

### "Scan `daisy_cotton/templates` for the plain Tailwind utilities its templates write literally"

**Adopted.** A build that scans `daisy_cotton/templates` picks up `end-2`, `top-2`
(`cotton/modal.html`), `focus-visible:outline-2`, `focus-visible:-outline-offset-2`
(`cotton/collapse.html`), `group/item`, `group-first/item:hidden`, `group-last/item:hidden`
(`cotton/timeline/item.html`) and `max-sm:megamenu-vertical` (`cotton/megamenu/index.html`). None
of them is in the stylesheet shipped with 0.26.0.

How the scan is reached differs between the two builds (R3, R4).

### "Safelist breakpoint-prefixed forms in `mvp/tailwind/base.css`"

**Adopted, and widened.** daisy-cotton builds a breakpoint-prefixed class through its `responsive`
tag in 19 places (`templatetags/daisy_cotton.py:14`, `BREAKPOINTS` at line 10), which gives 95
classes that no scan can see. They go in the preset.

The preset also has to carry the classes built by daisy-cotton's `variation` tag
(`templatetags/daisy_cotton.py:40`), 62 calls such as `btn-xs` and `tooltip-left`. The prebuilt
stylesheet has them already because it scans all of daisyUI. A project's own build does not scan
daisyUI, so without the preset those classes would be missing there (decision D10 in
`decisions.md`).

### "Resolve daisy-cotton's install path the way the entry file generator resolves the form pack's"

**Adopted.** `mvp/management/commands/mvp_tailwind.py:28` resolves `mvp_forms` from the imported
module's `__file__`. daisy-cotton is resolved the same way and its `templates` directory becomes a
fourth `@source` line and a fourth line of `--paths`.

### "Pass Cotton's `only` attribute on every call to a daisy-cotton component"

**Adopted as the rule; proved here.** No template calls a daisy-cotton component in this feature.
The behaviour was confirmed under the pinned Cotton (R6) and is pinned by tests, and the rule is
written into `CONTRIBUTING.md`.

### "Check that daisy-cotton's components render under `django-cotton==2.6.1`"

**Checked. They do, so the pin stays.** All 60 components that only daisy-cotton ships were
rendered under Cotton 2.6.1 with `daisy_cotton` below `mvp`, each as an isolated call with slot
content. None raised. This becomes a permanent test (R5).

### "Order: the project's apps, then `mvp`, then `daisy_cotton`, then `crispy_forms` and `mvp_forms`. A start-up check should warn when `mvp` is below `daisy_cotton`"

**Adopted.** The check compares the two positions in the app registry. The order of
`crispy_forms` and `mvp_forms` relative to `daisy_cotton` has no effect on template resolution,
because they share no template names, so the check is silent about it and the documentation simply
shows the recommended order.

### "The `Stylesheet` workflow installs no Python. Do not edit anything under `.github/`"

**Adopted. The workflow needs no change.** It runs `npm run build:css:prod` against
`assets/tailwind.css`, which is not changed to point into the Python environment (R3), so it keeps
compiling exactly as before. A `@source` whose directory does not exist was also tried and
compiles with exit status 0, so even a path into the environment would not have broken it.

## R1. The classes daisy-cotton can render, worked out from the installed package

daisy-cotton writes a class in one of four ways, and all four can be read from its templates
without rendering anything:

| How the class is written | Example | What it can produce |
|---|---|---|
| Literally, inside a `class` attribute or a `*_class` attribute | `class="dropdown … min-w-52"` | itself |
| `{% variation var "base" "a,b,c" %}` | `{% variation size "btn" "xs,sm,md,lg,xl" %}` | `base-a`, `base-b`, `base-c` |
| `{% responsive var "name" %}` | `{% responsive horizontal "menu-horizontal" %}` | `name`, and `bp:name` for each of `BREAKPOINTS` |
| A literal joined to a template variable | `mask-half-{{ item.half }}` (`cotton/form/rating.html`) | one class per value the variable can take |

A survey of every template tag used across the 82 templates found no other construction. The last
row occurs once, and its values (`1`, `2`) come from `rating_items` in
`templatetags/daisy_cotton.py`. A test cannot work those values out, so it holds them in a small
table keyed by the literal stem and fails, naming the stem, when it meets one it has no entry for.

For 0.1.2 this gives 649 classes. Caller-supplied classes (`{{ class }}`, `{{ content_class }}`)
are template variables and never appear. Icon classes do not appear either: daisy-cotton passes an
icon name to `<c-icon>` and writes no icon class itself.

**A class counts as styled** when the stylesheet has a selector for it: the class name, escaped
the way CSS escapes it, after a `.` and not followed by another name character. This is true of
marker classes such as `group/item` too, which appear in the selector of the variant that uses
them.

## R2. What the 0.26.0 stylesheet is missing

Comparing the 649 classes with the committed stylesheet:

- 84 breakpoint-prefixed forms of the 19 `responsive` classes. (Eleven are already present from
  the package's own safelist.)
- The eight literal utilities listed under the first planning note.
- `menu-paged`. **daisyUI 5.6.18, the version this package builds with, has no such class.** It
  was added in daisyUI 5.7.0 (`components/menu.css` in the published packages: absent from 5.6.22,
  present from 5.7.0).

Building with daisyUI 5.7.0 in place of 5.6.18, with everything else the same, adds exactly one
class selector to the stylesheet (`menu-paged`) and removes none. The build tool is therefore
moved to `daisyui@5.7.0`, the smallest version that has every class daisy-cotton 0.1.2 writes.

daisy-cotton's README says it needs "daisyUI 5" and does not say 5.7. That is reported upstream as
a documentation issue. It is not worked around here: this package builds with a daisyUI that has
the class, which is what daisy-cotton expects of any project.

## R3. Reaching daisy-cotton's templates from the prebuilt build

`assets/tailwind.css` is a static file, and daisy-cotton lives in the Python environment at a path
that contains the Python version. Tried with `@tailwindcss/cli` 4.3.2:

| `@source` form | Result |
|---|---|
| exact relative path into `.venv` | scanned |
| absolute path | scanned |
| any glob into `.venv` (`python*`, `*`, `**`) | compiles, scans nothing (`.venv` is git-ignored) |
| a symlink to the package | compiles, scans nothing |
| a path that does not exist | compiles, scans nothing |

So a static line cannot find the package without naming a Python version. Instead, `invoke
build-stylesheet` composes the entry it hands to Tailwind: it imports `assets/tailwind.css` and
adds one `@source` line with daisy-cotton's templates directory, resolved from the imported
module. The CLI reads that entry from standard input (`-i -`), with relative paths resolved from
the repository root. No temporary file is written and `assets/tailwind.css` keeps its meaning.

`npm run build:css:prod`, which the `Stylesheet` workflow runs, still builds from
`assets/tailwind.css` alone. That build compiles but lacks the eight literal utilities, and the
coverage test fails against it by name. This is the behaviour the specification asks for when the
stylesheet is built where daisy-cotton is not installed.

## R4. The generated entry file

`mvp_tailwind` gains a fourth resolved path, daisy-cotton's `templates` directory, written as an
`@source` line after the form pack's and printed last by `--paths`. The scan covers the literal
classes. The preset, which the entry already imports, covers the rest (R1's second, third and
fourth rows).

A real Tailwind build cannot run inside the Python test suite, which has no Node. Coverage of the
generated entry is therefore proved from what Tailwind is given: a class is covered when it is
written literally in a file under the fourth path, or is declared by an `@source inline()` entry
in the preset at the first path. `tests/test_components/test_responsive_safelist.py` already
proves the package's own render-time classes this way.

## R5. Which components the two packages share

Walking both `templates/cotton` trees, 22 component paths exist in both: `alert`, `avatar`,
`avatar.group`, `badge`, `breadcrumbs`, `breadcrumbs.item`, `button`, `card`, `divider`, `dock`,
`dock.item`, `dropdown`, `icon`, `link`, `menu`, `menu.item`, `mockup.browser`, `mockup.code`,
`mockup.code.line`, `mockup.phone`, `mockup.window`, `modal`. With `daisy_cotton` below `mvp`,
`get_template("cotton/<path>")` returns this package's file for each of them. The other 60 exist
only in daisy-cotton and resolve there.

Tests work both lists out from the two installed trees. No list is copied into the repository.

## R6. Isolation under the pinned Cotton

Rendered under Cotton 2.6.1:

| Call | Page context | Output |
|---|---|---|
| `<c-menu.title />` | `text="LEAK"` | `<li class="menu-title ">LEAK</li>` |
| `<c-menu.title only />` | `text="LEAK"` | `<li class="menu-title "></li>` |
| `<c-menu.title only>{{ page }}</c-menu.title>` | `text="LEAK"`, `page="PAGEVAL"` | `<li class="menu-title ">PAGEVAL</li>` |
| `<c-menu.title text="Given" only />` | `text="LEAK"` | `<li class="menu-title ">Given</li>` |
| `<c-stat only><c-slot name="title">{{ page }}</c-slot></c-stat>` | `page="PAGEVAL"`, `title="LEAK"` | the title slot shows `PAGEVAL` |

The leak happens only for an attribute a component declares with no default
(`<c-vars text class />` in `cotton/menu/title.html`). An attribute declared with a default
(`size=""` in `cotton/kbd.html`) does not read the page. daisy-cotton has both kinds, which is why
the rule is to isolate every call and not to work out which ones need it.

## R7. The start-up check

`mvp/apps.py` already registers one check from `MvpConfig.ready()`, and `mvp.E001` is the only
identifier in use. The new check lives in a new module, `mvp/checks.py`, and reads the app
registry:

- `daisy_cotton` not installed: `mvp.E002`, an error.
- `daisy_cotton` installed above `mvp`: `mvp.W001`, a warning.
- otherwise nothing.

The ordering rule is a plain function over a list of app names, so the same function can be run
against the list of apps the getting-started guide shows.

## R8. Dependency tooling

`uv add "daisy-cotton>=0.1.2,<0.2"` writes `pyproject.toml` and `uv.lock`. `deptry` reports a
declared dependency that no module imports, and `mvp_tailwind` does not import `daisy_cotton`
until the third story, so the package is listed with the others reached through `INSTALLED_APPS`.
`django-mvp-forms` is in the same position today: listed there and imported by the command.
