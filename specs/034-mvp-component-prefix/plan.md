# Implementation Plan: Every component this package keeps moves under the mvp. prefix

**Branch**: `034-mvp-component-prefix` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Research**: [research.md](research.md) | **Tasks**: [tasks.md](tasks.md)

## Summary

Sixty-seven of the package's 84 component templates move from `mvp/templates/cotton/` to
`mvp/templates/cotton/mvp/`, which makes their tags `<c-mvp.…>`. Every place that names one of
them is updated in the same change: the package's own templates, the two settings defaults, one
template path in a template tag, the demo, the tests, the documentation, the glossary and the
assistant skill. Nothing inside a component changes. A test keeps future components under the
prefix, the changelog carries the upgrade table, and Article XI of the constitution states the
rule.

## Technical Context

**Language/Version**: Python 3.12+, Django 5.2 to 6.1

**Primary Dependencies**: django-cotton 2.6.1 (resolves a dotted component name to a template
path). No dependency is added, removed or re-pinned.

**Storage**: none. No model, no migration.

**Testing**: pytest with pytest-django; the package's own `cotton_render*` fixtures.

**Target Platform**: a Django package; templates only.

**Project Type**: single package (`mvp/`), a demo project (`demo/`), tests (`tests/`).

**Constraints**: no behaviour change (FR-002); no alias at an old name (FR-005); no release
(FR-017); nothing under `.github/` changes; the prebuilt stylesheet is not rebuilt (research R6).

**Scale/Scope**: 67 files moved, about 1,600 mentions of a component name rewritten across
roughly 300 files.

## Constitution Check

| Article | How the plan meets it |
|---|---|
| I Testing | Tests first for everything a test can decide: the prefix guard, old names failing, the settings scenarios, overrides following their component. Wording (changelog, documentation) gets no test, per the testing standard. |
| II Simplicity, III Anti-abstraction | No new module, no helper layer, no alias machinery, no startup check (D12). One new test module and one fixture template directory. |
| VI Documentation | Documentation, README, glossary and skill change in this pull request. |
| VII Dependencies | None added. |
| XI Components are the public API | Amended here at the maintainer's instruction (D6, D6a). |
| XIII Rendered markup is a contract | No markup changes. Existing markup tests pass with only the names they ask for changed. |
| XVI Compatibility | Breaking and recorded in the changelog, which the article allows before 1.0. |

No violation to justify.

## Design

### 1. The mapping

A component's new name is decided from its first dotted segment, with two split cases. This is
the whole rule, and the script, the guard test and the changelog table all follow from it.

| First segment | Result |
|---|---|
| `icon`, `alert`, `badge`, `breadcrumbs`, `button`, `divider`, `dock`, `link`, `mockup` | unchanged |
| `avatar` | `mvp.avatar`, except `avatar.group`, which is unchanged |
| `menu` | unchanged, except `menu.item`, `menu.group`, `menu.collapse`, `menu.divider`, which gain the prefix |
| `actions`, `addons`, `app`, `backdrop`, `brand`, `card`, `container`, `data-field`, `documentation`, `dropdown`, `entrance`, `form`, `grid`, `group`, `layout`, `messages`, `modal`, `page`, `pagination`, `placeholder`, `rule`, `section`, `text`, `toolbar`, `user` | gains the prefix |
| anything else | unchanged (Cotton's own `vars`, `slot`, `component`; the demo's `components.*`, `demo.*`, `navbar.*`; example names for a project's own components) |

On disk: `mvp/templates/cotton/<path>` becomes `mvp/templates/cotton/mvp/<path>` for the 67
templates, moved with `git mv`. The 17 that stay are `icon.html`, `alert.html`, `badge.html`,
`button.html`, `divider.html`, `link.html`, `avatar/group.html`, `breadcrumbs/{index,item}.html`,
`dock/{index,item}.html`, `menu/index.html` and the five under `mockup/`.

### 2. The move is one commit

Moving the templates without updating their callers leaves every page broken, and the demo's
pages are exercised by the test suite. So the templates, every caller in `mvp/`, `demo/` and
`tests/`, the two settings defaults and the path in the `documentation` template tag change in
one commit that leaves the suite green. The settings default is therefore changed in the first
story although its tests and documentation belong to the second.

The rewrite is scripted (research R1). The script is written for this change, kept outside the
repository and not committed. What it cannot be trusted with is edited by hand from a search:

- component names in Python strings: `mvp/config.py`, `tests/settings.py`, and the tests' calls
  to `cotton_render`, `cotton_render_soup` and `render_component`
- template paths in strings: `mvp/templatetags/mvp.py`, `mvp/config.py`, and
  `render_to_string` / `get_template` / `template_name` in the tests
- the literal in `page/list/actions/index.html`: `is="page.list.actions.…"` becomes
  `is="mvp.page.list.actions.…"`
- comments that name a template path, in `mvp/tailwind/base.css`, `assets/js/layout.js`, the
  templates and the tests

After the script runs, a search for each old name must come back empty in the areas it covered.

### 3. Proving nothing changed

Research R2. Before the move, capture the rendered output of every component template (as
`test_render_all.py` renders them) and of every demo URL the suite's smoke tests request, into a
scratch directory outside the repository. After the move, capture again and compare. Component
output must be identical. Page output must be identical except for component tags printed as
text on gallery pages. The existing tests are the lasting proof and are edited only where they
name a component or a template path: no assertion is changed, removed or weakened.

### 4. New tests

One new module, `tests/test_components/test_component_prefix.py`:

- `TestComponentPrefix`
  - every template under `mvp/templates/cotton/` is either under `mvp/` or on the exception list
    (FR-005, FR-016, SC-001, SC-007); the failure message names each offending template
  - every entry on the exception list exists, so the list cannot outlive what it excuses
  - a moved component's old bare name does not resolve: `<c-page>`, `<c-toolbar>` and
    `<c-data-field>` raise `TemplateDoesNotExist` (US1 scenario 3; research R3 for the choice)
- `TestNamesSharedWithDaisyCotton` (skipped at class level when `daisy_cotton` is not installed)
  - the template paths the two packages have in common are exactly the exception list (FR-007,
    SC-002)

The exception list is one module-level constant, a frozenset of the 17 template paths.

Settings (US2), in `tests/test_components/test_layout_config.py` beside the existing navbar
widget tests: the default configuration renders the theme controller and login widgets; a
configuration naming a packaged widget by its prefixed name renders it; a configuration naming
the demo's own `navbar.test-widget` renders it with no prefix added.

Overrides (US3), in `tests/test_templates.py`: with a fixture template directory placed first
in the template search path (research R5), a template at `cotton/mvp/app/sidebar/footer.html`
replaces the packaged sidebar footer, and one at `cotton/app/sidebar/footer.html` does not.
The fixture templates carry a `data-` marker to assert on, not wording.

Fixtures (US3): `tests/test_fixtures.py` already renders components through the shipped
fixtures; its calls take the prefixed names, which is FR-011.

### 5. The record

- **Changelog** (FR-012): under `## [Unreleased]`, a `### Changed` entry marked breaking: the
  rule; the names that did not move and why; the five to check first when daisy-cotton is
  installed (card, modal, avatar, dropdown, menu entry); a note that template overrides and
  component names in settings move too; and the old-to-new table, one row per moved component,
  generated from the moved files so it cannot miss one. No version heading, no version bump.
- **Documentation** (FR-013): every page under `docs/` except the records (research R7, D16),
  `README.md`, `CONTRIBUTING.md` and `skills/django-mvp/SKILL.md`. `docs/components.md` and
  `docs/configuration.md` also explain the rule itself: the prefix, the icon, how a name in a
  setting is written, and where an override goes.
- **Glossary** (FR-014): `CONTEXT.md`'s component library lists every component under its
  current name, and its naming rules state the prefix, the icon exception and the components
  waiting on #435.
- **Constitution** (FR-015): Article XI states that the package's own components live under
  `mvp/templates/cotton/mvp/` and are reached as `<c-mvp.…>`; that the icon is the one permanent
  exception, because it replaces daisy-cotton's icon by sitting at the same name; that basic
  daisyUI components come from daisy-cotton and are not written again here; and that the rule
  against raw utility classes in templates that demonstrate a component covers this package's
  own components. Version 5.0.0 becomes 5.1.0 (a rule added and one scoped, none removed), with
  the amendment date.
- **Decision record**: one ADR, numbered at the merge gate from what is free on `main`: the
  package's components carry a prefix, and the icon does not.

## Story order

**US1 → US2 → US3 → US4, one at a time, in the feature's worktree.** They touch the same
templates, `mvp/config.py` and the same tests, so they do not run in parallel.

| Story | Delivers | Owns |
|---|---|---|
| US1 | FR-001 to FR-007, the default half of FR-008 | `mvp/`, `demo/`, `tests/`, `assets/js` comments; the new guard module |
| US2 | FR-008, FR-009 | settings tests; `docs/configuration.md` and `docs/layout.md` on widget names |
| US3 | FR-010, FR-011, FR-012, FR-017 | override tests and fixture templates; `mvp/fixtures.py` docstrings; `CHANGELOG.md` |
| US4 | FR-013 to FR-016 (the guard itself lands in US1) | `docs/`, `README.md`, `CONTRIBUTING.md`, `skills/`, `CONTEXT.md`, `CONSTITUTION.md` |

## Risks

- **A mention the script misses.** Mitigated by the closing search in each area and, for tags in
  templates, by the suite: an old tag in a packaged or demo template fails to render.
- **Main moves underneath.** Seven sibling features touch the same templates. A template or a
  caller added on `main` after the move is caught by the guard test and by rendering, and the
  script's rule applies to it unchanged. The branch is brought up to date and re-verified
  before it is offered for review.
- **A project left on an old name with daisy-cotton installed** gets daisy-cotton's component
  silently for five names. Accepted in the specification (D12); the changelog names the five.

## Project Structure

```text
mvp/templates/cotton/
├── icon.html, alert.html, badge.html, button.html, divider.html, link.html
├── avatar/group.html
├── breadcrumbs/, dock/, mockup/
├── menu/index.html
└── mvp/                      # everything the package keeps
    ├── actions/ addons/ app/ brand/ card/ dropdown/ entrance/ form/ layout/
    ├── page/ pagination/ placeholder/ section/ user/
    ├── avatar/index.html
    ├── menu/{item,group,collapse,divider}.html
    └── backdrop.html container.html data_field.html documentation.html grid.html
        group.html messages.html modal.html rule.html text.html toolbar.html

tests/test_components/test_component_prefix.py     # new
tests/fixtures/override_templates/cotton/…         # new, two templates
```
