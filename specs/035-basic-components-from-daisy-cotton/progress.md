
## 2026-10-05T16:19:44Z · Forge · plan

Planning started. Brought the branch up to date with main (6b5f98f) and read the specification, the planning notes, both packages' templates for the sixteen components and every caller. Baseline verify green on the rebased branch (lint, typecheck, test, build, conformance, docs). With the sixteen templates set aside the suite fails 28 tests, all in the package's own tests; that list is the plan's. A browser probe showed the dock toggle takes focus but does not answer Enter or Space on main (D14). Wrote research.md, plan.md and tasks.md, and D14 to D18.

## 2026-10-05T16:27:48Z · Forge · design-review

Design review returned approve with no blocking finding; two medium and four low findings applied or carried (D19). The dock toggle's keyboard operation is carried as unmet by a ruling given during the build (D14, daisy-cotton#135). Plan comment posted on the pull request. Plan gate is open; build starts.

## 2026-10-05T16:43:59Z · Implementer US1-US2 · T001

Did: wrote tests/test_components/test_basic_components.py (sixteen tags resolve inside daisy-cotton and this package ships no file at the path; dashed button; `full` not translated; menu entry inside daisy-cotton's menu; avatar inside its group; a project badge in TEMPLATES DIRS wins) with tests/project_templates/cotton/badge.html, and cut PREFIX_EXCEPTIONS in test_component_prefix.py to the icon alone.
Verified: before the deletion, `uv run pytest tests/test_components/test_basic_components.py` gave 34 failed, 3 passed (the resolution and no-file tests failed because this package's own template answered; dash and `full` failed on the old button). test_component_prefix.py gave 2 failed, 4 passed (every_template_is_under_the_prefix, shared_paths_are_exactly_the_exceptions). The 3 that passed first time (menu entry, avatar in group, project badge precedence) hold today and are guards for after the deletion; they could not be seen failing.
Next: T002, the deletion.
Watch: the same two modules read 43 passed once the sixteen templates were gone.

## 2026-10-05T16:43:59Z · Implementer US1-US2 · T002

Did: `git rm` of the sixteen templates under mvp/templates/cotton/ (alert, badge, button, divider, link, avatar/group, breadcrumbs/index and item, dock/index and item, menu/index, mockup/browser, code/index, code/line, phone, window). The emptied directories went with them. cotton/icon.html and cotton/mvp/ are untouched.
Verified: `uv run pytest tests/test_components/test_basic_components.py tests/test_components/test_component_prefix.py` 43 passed. Full suite with only the deletion in place: 26 failed, 2640 passed, 1 skipped (`uv run pytest -q -n auto`). The plan says 28; this run counted 26, and every one of the 26 is an entry in the plan's table (the other two did not fail in this run).
Next: T003, rewrite what pinned the removed markup.
Watch: test_menu.py::TestMenuGrow still passes after the deletion only because `grow` now lands as an HTML attribute; the plan's table does not list it, so it is left alone and reported.

## 2026-10-05T16:43:59Z · Implementer US1-US2 · T003

Did: removed test_link.py, test_mockup_code.py, TestButtonCondition and TestTheItemTextSpan; rewrote the sidebar container and landmark tests (test_menu.py, test_app_sidebar.py, test_shell_renders_without_request.py), the dock class test (test_layout_config.py, now on nav.dock), the log-in button test (test_sidebar_footer.py), the dropdown trigger test (test_dropdown.py), and nav.dock in test_renderers.py. Removed five class-merge cases for the divider, menu and dock item from test_class_attribute_merge.py. Added: test_messages.py, test_share_dropdown.py, the dock markup class in test_renderers.py (landmark with a name, toggle name, aria-current), the dock default and theme chooser menu name tests, a daisy-cotton attribute test on the delete page's related-records alert, and the former-attribute scan for ten pages in test_templates.py. Nothing about the dock toggle's keyboard operation.
Verified: red before T004: the scan failed on shell, list, detail and delete (menu `grow` and `label` on ul.menu, `reverse` on buttons); the dock configured-class, theme chooser name and share menu name tests failed; the log-in button and sidebar landmark tests failed. The message, dock markup, related-records and breadcrumb tests passed first time because daisy-cotton already supplies that markup: they are guards, and they could not be seen failing after the deletion.
Next: T004.
Watch: the scan's list page is drawn with no products, because the demo's product card passes `reverse` and demo/ is US4's.

## 2026-10-05T16:43:59Z · Implementer US1-US2 · T004

Did: moved the callers: `ghost` in 500.html and mvp/error_base.html; the icon into the default slot after the text, `reverse` gone, in form_view.html, actions/login.html (also `:block="full"`), page/list/actions/create.html and filter.html; text-sm on the header trail; the dock takes :class from mvp_config; the sidebar menu is wrapped in a named nav with w-full grow; the theme chooser and share menus take aria-label and w-full; the user menu takes w-full. Docstrings corrected in mvp/views/base.py, mvp/views/edit.py and the comment in cotton/mvp/rule.html. No `only` added anywhere.
Verified: `uv run pytest tests/test_components tests/test_templates.py tests/test_menus.py tests/test_renderers.py tests/test_views tests/test_demo -n auto`: 1809 passed, 1 skipped, 1 failed (the e2e test noted under T005). A scan of every `<c-...>` call to the sixteen tags under mvp/templates for the former names finds none.
Next: T005.
Watch: an alert variant outside the four raises IconNotFoundError because daisy-cotton's alert asks this package's icon lookup for an icon of that name (`<c-alert variant="primary">` raised on this branch); an unregistered message level draws no variant and raises nothing.

## 2026-10-05T16:44:00Z · Implementer US1-US2 · T005

Did: the selector in mvp/tailwind/base.css is `.breadcrumbs li > :is(a, span)` with its comment rewritten; `btn-outline` added to the safelist; stylesheet rebuilt with `uv run invoke build-stylesheet` (css and .br).
Verified: test_daisy_cotton_coverage.py and test_smoke.py 110 passed. Rebuilding dropped seven classes nothing writes now: bg-neutral-900, flex-row-reverse, h-80, place-content-center, text-white, mvp-breadcrumb-text (six lines deleted from tests/fixtures/stylesheet_classes_0_26_0.txt) and btn-outline, which daisy-cotton's button still writes for `outline` and which is therefore kept by a safelist entry. In a browser, test_app_header_e2e.py: 16 passed, 1 failed. test_each_crumb_is_visibly_truncated selects `.mvp-breadcrumb-text`, a class the new markup does not have, so it finds no crumbs; test_every_crumb_stays_in_the_row passes because it loops over nothing. A scratch run selecting `nav.breadcrumbs li > :is(a, span)` found three crumbs, all truncated and none of zero width.
Next: Forge to decide whether the locator in test_app_header_e2e.py may change; T005 is reported blocked on that alone.
Watch: the plan's "no edit expected" for that file does not hold.
