# Implementation Plan: Install daisy-cotton alongside the package, with no visible change

**Branch**: `033-install-daisy-cotton` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/033-install-daisy-cotton/spec.md`, with
[research.md](research.md) and [decisions.md](decisions.md).

## Summary

django-mvp takes daisy-cotton `>=0.1.2,<0.2` as a runtime dependency and lists `daisy_cotton`
below `mvp` in its demo and test project. No template under `mvp/templates/` changes. Four things
are added around that:

1. Tests that work out, from the two installed packages, which components both ship and which only
   daisy-cotton ships, and prove the first resolve to this package and the second are found and
   render under the pinned Cotton.
2. Stylesheet coverage. The preset gains the classes daisy-cotton builds at render time. The
   prebuilt build lists the eight plain utilities daisy-cotton's templates write and moves to
   daisyUI 5.7.0, the first version with `menu-paged`. The generated entry file scans daisy-cotton's templates. One test module
   works out every class daisy-cotton can render and fails by name when the prebuilt stylesheet,
   or what the generated entry covers, lacks one.
3. A start-up check: `mvp.E002` when `daisy_cotton` is missing, `mvp.W001` when it is above `mvp`.
4. Tests that pin Cotton's `only` behaviour against a daisy-cotton component, and the rule in
   `CONTRIBUTING.md`.

## Technical Context

**Language/Version**: Python 3.12+ and Django 5.2+ (the supported matrix is unchanged)

**Primary Dependencies**: django-cotton 2.6.1 (pin unchanged), **daisy-cotton >=0.1.2,<0.2 (new)**;
build tooling Tailwind CSS 4.3.2 and **daisyUI 5.7.0 (was 5.6.18)**

**Storage**: N/A. No model, no migration.

**Testing**: pytest with pytest-django, through `uv run pytest`

**Target Platform**: a Django project; the stylesheet is a committed build artifact

**Project Type**: library (a reusable Django app)

**Performance Goals**: N/A. The start-up check reads the app registry once.

**Constraints**: no template under `mvp/templates/` changes; nothing under `.github/` changes; no
release and no version bump; every existing test that asserts on rendered output passes unchanged

**Scale/Scope**: daisy-cotton 0.1.2 has 82 component templates and can render 649 classes

## Constitution Check

| Article | How the plan meets it |
|---|---|
| I — Testing | Every story is written test-first. Each acceptance scenario has a test named in `tasks.md`. |
| II — Simplicity | One new module (`mvp/checks.py`), one new test helper module. No new setting, no new abstraction. |
| III — Anti-Abstraction | The class derivation is three functions in one test helper, used by one test module. Nothing in `mvp/` parses daisy-cotton's templates. |
| V — Security | No new input surface. The check reads settings the project wrote. |
| VI, XVII — Documentation | Each story updates the pages it changes the truth of: getting started, README, the shipped skill, styling, troubleshooting, the contributor guide, the changelog. |
| VII — Dependency discipline | One new runtime dependency, justified in ADR 0030. `deptry` passes. |
| VIII — Internationalization | Check messages are for the developer at the terminal and follow `mvp.E001`, which is not translated. |
| XI — Components are the public API | No component is added, removed or changed. |
| XIII — Rendered markup is a contract | No markup changes. The existing component tests are the proof and are not edited. |
| XIV — Browser tests are the exception | No browser test is added. |
| XV — Shipped assets are build artifacts | The stylesheet's inputs change, so it is rebuilt and committed on this branch. |
| XVI — Compatibility | The new `INSTALLED_APPS` line is a breaking upgrade step, recorded in the changelog. |

No violation needs justifying.

## Design

### Dependency and app order (foundation)

- `pyproject.toml`: `"daisy-cotton (>=0.1.2,<0.2)"` in `dependencies`, added with `uv add` so
  `uv.lock` follows. `daisy-cotton` joins the `DEP002` list of packages reached through
  `INSTALLED_APPS`, as `django-mvp-forms` is.
- `demo/settings.py`: `"daisy_cotton"` directly below `"mvp"`. `tests/settings.py` inherits it.

### Which package a component comes from (US-1)

`tests/test_components/test_daisy_cotton_install.py`. Component paths are worked out by walking
`mvp/templates/cotton` and `daisy_cotton/templates/cotton`:

- declared dependency: `importlib.metadata.requires("django-mvp")` carries a `daisy-cotton`
  requirement whose specifier is `>=0.1.2,<0.2`, and the installed version satisfies it;
- every path in both trees: `get_template("cotton/<path>").origin.name` is under this package;
- every path only in daisy-cotton's tree: the origin is under daisy-cotton, and the component
  renders as an isolated call under the pinned Cotton (FR-005, FR-011);
- the guide's app list: the `INSTALLED_APPS` block in `docs/getting-started.md` is read and passed
  to the ordering rule from US-4, which returns nothing for it. This test is added in US-4, where
  the rule exists.

### Stylesheet coverage (US-2 and US-3)

**The preset, `mvp/tailwind/base.css`.** A new block, headed as daisy-cotton's, with `@source
inline()` entries for:

- every `responsive` class at every breakpoint:
  `{sm,md,lg,xl,2xl}:{alert-horizontal,alert-vertical,card-side,…}`;
- every `variation` class, grouped by option list:
  `{btn,badge,card,…}-{xs,sm,md,lg,xl}`, and so on.

Existing entries are left as they are, even where the new block repeats a class.

**The derivation, `tests/daisy_cotton_classes.py`.** A helper module the two coverage test classes
share:

- `component_classes(templates_dir)` returns the set of classes the templates under a directory
  can render, by the four rules in research R1. It raises, naming the stem and the file, when a
  class is built from a template variable it has no values for.
- `unstyled_classes(classes, stylesheet)` returns the classes with no selector in a stylesheet.
- `safelisted_classes(preset)` returns every class the preset's `@source inline()` entries
  declare, with brace groups expanded. `test_responsive_safelist.py` has private helpers that do
  the same; they are left alone, because this feature edits no existing test and adds no
  underscore-prefixed name.

**The prebuilt build.** `assets/tailwind.css` gains `@source inline()` entries for the eight plain
utilities daisy-cotton's templates write, under a comment naming daisy-cotton (research R3).
`tasks.py` and the `npm` scripts do not change. `package.json` and `package-lock.json` move
`daisyui` to 5.7.0.
`mvp/static/css/django-mvp.css` and its `.br` sibling are rebuilt and committed.

**The generated entry.** `mvp_tailwind` resolves `Path(daisy_cotton.__file__).resolve().parent /
"templates"`, writes it as an `@source` line after the form pack's, and prints it as the fourth
line of `--paths`.

**The tests, `tests/test_components/test_daisy_cotton_coverage.py`:**

- `TestClassDerivation`: against a small made-up template directory under `tmp_path`, the
  derivation returns the literal, `variation` and `responsive` classes, leaves out a
  caller-supplied `{{ class }}`, and raises by name on an unknown interpolated stem. A made-up
  class that no stylesheet has is reported by `unstyled_classes` by name (US-2 scenario 4).
- `TestPrebuiltStylesheet`: no class of the installed daisy-cotton is unstyled in the committed
  stylesheet (FR-006, SC-003; the breakpoint forms are in the set, so US-2 scenario 2 too). Every
  class the 0.26.0 stylesheet styled is still styled (FR-007, SC-005), read from
  `tests/fixtures/stylesheet_classes_0_26_0.txt`.
- `TestGeneratedEntry`: every class of the installed daisy-cotton is written literally under the
  fourth path or declared by the preset at the first path (FR-009, SC-004). Every class the 0.26.0
  preset declared is still declared (US-3 scenario 4), read from
  `tests/fixtures/preset_safelist_0_26_0.txt`.

`tests/test_components/test_mvp_tailwind_command.py` gains tests for the fourth path and the new
`@source` line. Its one test that unpacks exactly three lines from `--paths` is changed to read
the first three, because FR-016 adds a fourth. That is the only existing test this feature edits.

The two fixtures are written once from the 0.26.0 files as they stand on `main`. A later feature
that removes a class on purpose deletes its line.

### The start-up check (US-4)

`mvp/checks.py`:

- `daisy_cotton_app_messages(app_names)` takes app names in order and returns the list of check
  messages: `Error` `mvp.E002` when `daisy_cotton` is not among them, `Warning` `mvp.W001` when it
  comes before `mvp`, otherwise empty. Each has a `hint` saying where the line belongs.
- `check_daisy_cotton_app(app_configs, **kwargs)` calls it with
  `[config.name for config in apps.get_app_configs()]`.

`MvpConfig.ready()` registers it beside the existing check. Tests in `tests/test_checks.py` cover
the three orders, both identifiers, silencing through `SILENCED_SYSTEM_CHECKS` with
`call_command("check")`, and the repository's own settings reporting nothing.

### Isolation (US-5)

`tests/test_components/test_daisy_cotton_isolation.py`, against `menu.title` (declares `text` with
no default) and `stat` (named slots), the cases in research R6: the page's `text` does not reach
an isolated call; default-slot content and named-slot content render the page's values; a passed
attribute is used. `CONTRIBUTING.md` gains the rule and its reason under *Component Development*.

### Documentation

| Page | Change | Story |
|---|---|---|
| `docs/getting-started.md`, `README.md`, `skills/django-mvp/SKILL.md` | `daisy_cotton` in the app list below `mvp`, and why | US-1 |
| `docs/adr/0030-daisy-cotton-is-a-runtime-dependency.md` | the dependency's justification | US-1 |
| `CHANGELOG.md`, under *Unreleased* | the dependency and the upgrade line (US-1); stylesheet coverage and daisyUI 5.7.0 (US-2); the generator's fourth path (US-3); the check (US-4) | each |
| `docs/styling.md` | what the prebuilt stylesheet covers; the generated entry and `--paths`; daisyUI 5.7 or later for a project's own build | US-2, US-3 |
| `docs/troubleshooting.md` | the two check identifiers | US-4 |
| `CONTRIBUTING.md` | isolate every call to a daisy-cotton component | US-5 |

The documentation says daisy-cotton is installed, found and styled. It does not present its
components as replacing this package's.

## Story order

**Foundation → US-1 → US-2 → US-3 → US-4 → US-5, one at a time, in one worktree.** US-2 and US-3
share the preset, the helper module and `docs/styling.md`. Every story touches `CHANGELOG.md`.

## Project Structure

```text
mvp/
├── apps.py                              # registers the new check
├── checks.py                            # new
├── management/commands/mvp_tailwind.py  # fourth path
├── static/css/django-mvp.css(.br)       # rebuilt
└── tailwind/base.css                    # daisy-cotton safelist block
demo/settings.py                         # daisy_cotton below mvp
assets/tailwind.css                      # daisy-cotton's eight plain utilities
package.json, package-lock.json          # daisyui 5.7.0
pyproject.toml, uv.lock                  # the dependency
tests/
├── daisy_cotton_classes.py              # new helper
├── fixtures/stylesheet_classes_0_26_0.txt, preset_safelist_0_26_0.txt   # new
├── test_checks.py                       # new
└── test_components/
    ├── test_daisy_cotton_install.py     # new
    ├── test_daisy_cotton_coverage.py    # new
    ├── test_daisy_cotton_isolation.py   # new
    └── test_mvp_tailwind_command.py     # extended
docs/, README.md, CONTRIBUTING.md, CHANGELOG.md, skills/django-mvp/SKILL.md
```

## Risks

- **daisyUI 5.7.0 changes an existing rule.** Measured: the set of class selectors gains
  `menu-paged` and loses nothing. Rule bodies were not compared one by one, and no test in the
  suite judges appearance. The control is a look at the shell's pages on the rebuilt stylesheet,
  named in T006 and repeated before the pull request is marked ready.
- **The fixtures make later removals noisy.** A feature that deletes a component deletes lines
  from a fixture. That is the intended cost of SC-005: a class cannot leave the stylesheet without
  someone saying so.
- **The eight utilities are a hand-kept list.** A daisy-cotton upgrade that writes a new one fails
  the coverage test by name, and the fix is one more entry.
