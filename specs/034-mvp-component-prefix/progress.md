
## 2026-10-05T14:40:19Z · Forge · plan

Planning started. Read the specification, the planning notes and the component directory on main (bd63880): 84 templates, 67 move, 17 stay. Baseline verify green on bdd7fc9 (lint, typecheck, test, build, conformance, docs). Wrote research.md, plan.md and tasks.md.

## 2026-10-05T14:49:18Z · Forge · design-review

Design review returned changes requested: one high finding (the htmx form mixin's default component), re-planned as D21; seven others carried or recorded (D22, D23). Plan comment posted on the pull request. Plan gate is open; build starts.

## 2026-10-05T15:04:41Z · Implementer US1 · T001

Did: wrote the guard before any move. `tests/test_components/test_component_prefix.py` holds `PREFIX_EXCEPTIONS` (17 paths), `TestComponentPrefix` (every template under cotton/mvp/ or excepted; every exception exists; `<c-page>`, `<c-toolbar>`, `<c-data-field>` raise `TemplateDoesNotExist`) and `TestNamesSharedWithDaisyCotton` (class-level skip when `daisy_cotton` cannot be imported). `tests/test_views/test_htmx.py` gained `TestHtmxFormDefaultComponent`: an invalid htmx POST to a stub view with no `htmx_form_component` of its own, no patch of `render_component`, answers 200 with a `<form>` element.

Verified (all before the move, from the base commit): the htmx test passed (1 passed). The prefix class failed for the right reason: 4 failed, 1 passed, 1 skipped; the offender list named exactly 67 templates and the three old names did not raise. With `PYTHONPATH=/tmp/dc012/t` (daisy_cotton 0.1.2, 82 templates): the shared test failed, 22 template paths shared (the 17 plus avatar/index, modal, menu/item, card/index, dropdown/index). After the move (see T002): prefix module 6 passed; with daisy_cotton on the path 6 passed and 17 shared. Probe: with the mixin default put back to "form" after the move, the htmx test fails with `TemplateDoesNotExist: cotton/form/index.html`; with "mvp.form" it passes.

Next: T002 lands in the same commit, so no commit leaves the suite red.

Watch: the commit is shared with T002 (`T001 T002: …`).

## 2026-10-05T15:04:41Z · Implementer US1 · T002

Did: captured before the move (scratch outside the repo): all 84 component templates rendered as test_render_all does, and every demo URL (52 under tests.settings, 54 under demo.settings; anonymous and superuser; every gallery slug; one invalid htmx POST), with the clock-free output checked deterministic by capturing twice. Then `git mv` of the 67 templates under mvp/templates/cotton/mvp/ and one scripted pass over mvp/, demo/, tests/ and assets/ (not committed): 852 tag rewrites and 34 template-path rewrites over 139 files; a second pass changed nothing. By hand: the default navbar widgets in mvp/config.py (and the comment above them), `htmx_form_component` default and its two docstring mentions in mvp/views/htmx.py, the widget lists in demo/settings.py and tests/settings.py, the monkeypatched widget lists in test_layout_config.py, test_app_header.py and test_config.py, the `render` names in test_list_create_action.py, test_list_sort_action.py and test_fixtures.py, the `is="…"` literal in page/list/actions/index.html, the pathlib segments in test_list_filter_action.py, test_form_formset.py (two places) and test_library.py, the `SKIP` key in test_render_all.py, and two prose path comments. Long test strings the longer tags pushed past 88 columns were wrapped into adjacent literals, and ruff format was run over the touched files.

Verified: after capture compared with before. Components: 84 of 84 byte-identical, under both settings. Pages: tests.settings 105 files, 81 byte-identical, 22 differ only where a gallery page prints a tag as text (the same rule applied to the before text gives the after text), 2 (django-tables2, anonymous and admin) differ only by the clock time of rows created minutes apart; demo.settings 109 files, 85 identical, 22 printed-tag, the same 2 clock-only. Collection: test_render_all 84 (was 84), test_declared_attributes 68 declaring components (68 templates with `<c-vars` before and after). Search for every old name in mvp/, demo/, tests/, assets/: none left. `uv run pytest -q -n auto`: 2452 passed, 2 skipped (base: 2446 passed, 1 skipped; the difference is the 6 new passing tests and the daisy-cotton class skipping).

Next: full verify, then flip T001 and T002 in feature-state.json and write the report.

Watch: mvp/static/js/formset.js line 2 (a comment naming the two formset tags) is outside the file list in tasks.md; edited because the acceptance search covers mvp/. mvp/fixtures.py docstring tags were rewritten by the script (card, card.title, card.body, grid); its bare-name examples ("card", "app.sidebar") are left for T006, which owns that file.

## 2026-10-05T15:10:39Z · Implementer US2 · T003

Did: added TestNavbarWidgetNames to tests/test_components/test_layout_config.py: the default lists (fresh runpy of mvp/config.py under settings.MVP_CONFIG = {}) render the theme controller then the login widget; navbar.test-widget listed by its own name renders. Prefixed packaged widget scenario already proved by TestShellRendersConfig::test_navbar_widgets_render_from_config (named in the class docstring).
Verified: uv run pytest tests/test_components/test_layout_config.py -q -> 60 passed. Probes: old name in mvp/config.py default fails the default test (TemplateDoesNotExist cotton/actions/theme_controller); old name in tests/settings.py fails the existing test; listing mvp.navbar.test-widget fails the own-name test. ruff check and format clean.
Next: T004 docs.
Watch: the demo widget carries no id or data- hook, so the test selects li.nav-item inside the desktop wrapper.

## 2026-10-05T15:11:15Z · Implementer US2 · T004

Did: applied the plan's mapping to docs/configuration.md and docs/layout.md (tags, template paths, bare widget names in MVP_CONFIG examples and the bundled-widgets table). Added to the widget-lists sections: a name is written in full as it would follow c- in a tag, nothing is added for the project, a packaged widget carries mvp., a project's own component is listed by its own name, an unprefixed old name raises TemplateDoesNotExist.
Verified: scripted check that every c-mvp.* tag, quoted mvp.* widget name and templates/cotton/mvp/... path on the two pages resolves to a file under mvp/templates/cotton/ (all true). Block names such as app.header.widgets and the page.* blocks are template blocks, not components, and are unchanged.
Next: T005 override test.
Watch: none.

## 2026-10-05T15:11:58Z · Implementer US2 · T005

Did: added TestComponentOverridePath to tests/test_templates.py (fixture dir first in TEMPLATES DIRS via the settings fixture, as the head-template test does) and two fixture templates under tests/fixtures/override_templates/cotton/{mvp/,}app/sidebar/footer.html, each with its own data-footer-override marker.
Verified: written test-first; before the fixtures existed the prefixed-marker test failed (marker absent, packaged footer rendered), the other passed vacuously. With the fixtures: uv run pytest tests/test_templates.py -q -> 201 passed. Probes: removing the prefixed fixture fails the first test; swapping the two markers fails both. ruff check/format clean.
Next: T006 fixtures docstrings.
Watch: the old-path test only has teeth once the fixture exists, so it is always run with the fixture dir in place.

## 2026-10-05T15:12:22Z · Implementer US2 · T006

Did: mvp/fixtures.py docstrings only: cotton_render("card") and cotton_render_soup("card") examples now use "mvp.card"; the "such as card or app.sidebar" sentences name mvp.card and mvp.app.sidebar; the nested-card example no longer uses c-mvp.card.title and c-mvp.card.body (neither template exists, the card takes a title attribute), so it is now <c-mvp.card :title="title">. Left c-ul/c-li in the nested-list example (names the package never shipped, not moved).
Verified: AST of mvp/fixtures.py with docstrings blanked is identical to HEAD's. uv run pytest tests/test_fixtures.py -q passes (all four fixtures already render a moved component by its prefixed name: mvp.card, mvp.card/mvp.grid, c-mvp.card, c-mvp.grid, plus c-mvp.pagination.link); no test case needed adding. ruff clean.
Next: T007 changelog.
Watch: none.

## 2026-10-05T15:12:59Z · Implementer US2 · T007

Did: CHANGELOG.md, under ## [Unreleased], a ### Changed entry marked breaking: the rule, the two groups that did not move and why, the five tags to check first with daisy-cotton and the old-path override effect, the three names outside a tag (overrides, MVP_CONFIG names, htmx_form_component), and the old-to-new table. The table was generated from mvp/templates/cotton/mvp/ by /tmp/fs034/scratch/changelog_table.py (not committed).
Verified: a second check parsed the committed table: 67 rows, 67 distinct old names, each row old == new minus the prefix, and the set equals the set derived from the directory. git diff of CHANGELOG.md is 109 insertions, 0 deletions, all above ## [v0.26.0]. No em dash in the entry.
Next: full verify, ledger, report.
Watch: none.

## 2026-10-05T15:19:39Z · Implementer US4 · T008

Did: ran the US1 rename script over docs/*.md (not docs/adr/, not docs/ROADMAP.md), docs/contributing/, README.md, CONTRIBUTING.md and skills/django-mvp/SKILL.md (180 tags, 6 paths), then read every changed page. By hand: htmx_form_component default in docs/integrations.md is now "mvp.form"; docs/components.md gains "Names and the mvp. prefix" (rule, icon exception, the basic components waiting on #435, override at the prefixed path) and its directory = namespace examples, override example and navbar widget-name example are true; docs/navigation.md renderer sentence; CONTRIBUTING.md test example rewritten (it imported cotton_render from django_cotton, which does not export it, and used slash paths); SKILL.md gains a component-names row and the override path. Prose reflowed to the file's existing wrap width.
Verified: closing search (rename.py --dry over the same files) prints "files changed: 0 | tag rewrites: 0 | path rewrites: 0". A script resolving every c-tag in these files to a template under mvp/templates/cotton/ reports only the intended non-matches (Cotton's own tags, project-example names, globs). The CONTRIBUTING example ran as a test in scratch and passed. ruff check clean.
Next: T009 (CONTEXT.md), T010 (CONSTITUTION.md).
Watch: no test was written for any of this text.

## 2026-10-05T15:19:46Z · Implementer US4 · T008

Did: correction to the T008 entry above. "ruff check clean" was wrong. `uv run ruff check .` reports 15 errors, all in tests/ (test_declared_attributes, test_field_errors_aria_describedby, test_responsive_safelist, test_mounted, test_table_layout, test_views/*). The T008 commit changes no .py file, so none come from it; whether they predate this branch is not something I checked. The lint step of `forge verify` is the authority and runs before I report.
Verified: nothing new. The 15 errors are as reported by `uv run ruff check .` at this commit.
Next: T009.
Watch: do not read the T008 entry's lint claim as a pass.

## 2026-10-05T15:20:47Z · Implementer US4 · T009

Did: ran the rename script over CONTEXT.md, then rewrote the Component Library by hand: all 84 shipped components are listed, 67 with the mvp. prefix and 17 bare. Added the five that were missing (c-mvp.actions.language-switcher-modal, c-mvp.app.sidebar.back, c-mvp.page.info, c-mvp.rule, c-mvp.documentation, plus c-mvp.card.wrapper) and removed c-page.list.footer, which has no template. Naming rules 1 to 3 now use true examples (mvp/templates/cotton/mvp/card/index.html -> c-mvp.card); new rules 5 and 6 state the prefix, the icon exception and the basic components that stay bare until #435. Component Attribute scopes the utility-class rule to this package's components; Override gives the prefixed path; the Cotton Component vs. DaisyUI Component entry now says the basic daisyUI components come from daisy-cotton; the navbar widget names in the Config example carry the prefix.
Verified: a script compared the names in the library blocks with the template files on disk: none missing, none extra. Rename script dry run over CONTEXT.md: 0 files changed. No test written for this text.
Next: T010 (CONSTITUTION.md).
Watch: the Config example in CONTEXT.md still shows the flat `end` key, which docs/layout.md calls a legacy shape; only the names were changed.

## 2026-10-05T15:20:58Z · Implementer US4 · T010

Did: amended Article XI of CONSTITUTION.md. The package's own components live under mvp/templates/cotton/mvp/ and are reached as <c-mvp.…>, in lowercase-kebab form; the icon is the one exception, kept at cotton/icon.html because it replaces daisy-cotton's plain icon by sitting at the same name; basic daisyUI components come from daisy-cotton and are not written again here; the utility-class rule is scoped to this package's own components, with the daisy-cotton clause. The sentences on attributes being the only supported customisation, template overrides and the {% include %} ban are kept. Footer is Version 5.1.0, Last Amended 2026-10-05. Nothing else changed.
Verified: git diff CONSTITUTION.md shows only Article XI and the footer.
Next: forge verify, feature-state, completion report.
Watch: none.

## 2026-10-05T15:24:03Z · Forge · converge

Convergence: every FR traced to a task and a commit, no gap, no new task. No migration. Cleanup pass over the new tests found nothing to simplify. ADR 0030 written (D1, D2, D11); every decision carries its verdict. Tamper check clean for US2 to US4; US1's flags triaged as name-only (D24).
