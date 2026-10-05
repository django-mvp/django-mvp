
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
