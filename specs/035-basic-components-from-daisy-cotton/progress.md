
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

## 2026-10-05T16:50:41Z · Forge · T011

Accepted the first build pass after an independent verify (all steps green) and a read of every changed test (D23). Made three small fixes directly: the breadcrumb browser tests' locator, removal of tests left pinned to daisy-cotton's markup (D21), and the daisy-cotton floor raised to 0.1.3 by a ruling (D22). Carried as unmet: an alert variant with no icon raises (D20, daisy-cotton#136).

## 2026-10-05T16:57:11Z · Implementer US3 · T006

Did: Added tests/daisy_cotton_calls.py (class DaisyCottonCalls: compiles each template with
Cotton's compiler, tokenizes the compiled text with Django's lexer as patched by Cotton, reads
each `cotton` tag with parse_component_tag; `calls(dir)` yields path, name, attribute names,
only; `unisolated(dir)` yields the daisy-cotton calls without only). Added
tests/test_components/test_daisy_cotton_calls.py (the check, five self-tests on a tmp_path
directory including <c-hover-3d>). Extended tests/test_components/test_daisy_cotton_isolation.py
with three new classes: leak comparison over four pages, content inside an isolated alert,
dismissible alert under only. Existing tests in that module untouched.
Verified (before T007, uv run pytest on the two files): 3 failed, 18 passed.
The check names 47 calls: button 30, alert 7, menu 4, badge 1, breadcrumbs 1, divider 1,
dock 1, dock.item 1, link 1 (list kept at /tmp/fs035/scratch/offenders-before.txt).
Leak test fails on two elements: the list page's nav.breadcrumbs (aria-label becomes the page
variable's value) and the sign-out page's a.link (gains link-primary and link-hover from the
page's variant and hover).
Passed on first run: the shell page (the menu renderer draws the dock and sidebar menu with
its own context, so no page variable reaches them), the formset page's divider (the call
passes class itself and the divider declares nothing else without a default), the alert
slot-content tests and the dismissible-alert tests (Cotton and daisy-cotton already behave
that way).
Next: T007, add only to the 47 calls.
Watch: the blocking-records list on the delete page stands in for the related-records list, as
no demo page has a cascade delete to list.

## 2026-10-05T16:58:22Z · Implementer US3 · T007

Did: Added only to the 47 calls the check named, across 28 templates under mvp/templates/.
Nothing else about a call changed: the diff of mvp/ is 47 lines changed, each adding the
word only before the tag's closing. No call needed an attribute passed explicitly. No c-mvp.*
call and no <c-icon> was touched.
Verified: uv run pytest on test_daisy_cotton_calls.py and test_daisy_cotton_isolation.py:
21 passed. The check now names 0 calls. Both leak failures (list page's nav.breadcrumbs,
sign-out page's a.link) are gone. uv run pytest -q -n auto over the whole tree:
2687 passed, 1 skipped.
Next: the story's full verify, then the ledger rows and the report.
Watch: the leak comparison does not look inside kept c-mvp.* components (issue 485).

## 2026-10-05T17:06:41Z · Implementer US4 · T008

Did: wrote tests/test_demo/test_basic_component_attributes.py (scan of demo/**/templates for former attribute names on button, avatar.group, divider, menu; table holds only names daisy-cotton does not declare). Added calls_with_examples and read to tests/daisy_cotton_calls.py; the scan strips cotton:verbatim markers before compiling so the shown examples are read. calls() now delegates to read() and returns the same tuples.
Red first: the scan failed on the demo as it stood with 10 offenders (button reverse x3 in the product card, the account overview and the button page; button full x2 in the button and dropdown pages; divider label x5 in the divider page). Moved every demo template: full to block, reverse to the icon in the slot, variant ghost/link to ghost/link, divider label to text and vertical to horizontal (by hand), avatar group class -space-x-6, code lines prefix="$", size lists xs to xl, descriptions in component_docs.py say which components come from daisy-cotton. Added a label placement section to the divider page.
Verified: uv run pytest tests/test_demo -n auto: 91 passed. Scan seen failing then passing. All 16 component pages answered 200 (scratch run, not committed). ruff check and format clean on touched files.
Next: T009 documentation.
Watch: the divider's vertical/horizontal swap and the alert variants were moved by reading each use; no test covers them.

## 2026-10-05T17:11:11Z · Implementer US4 · T009

Did: docs/components.md has a new section naming the sixteen tags as daisy-cotton's with a link for each, one explanation of `only` and when a project needs it (replacing the earlier paragraph, so it is explained once), and what a project override of one of the tags now also answers (the dismiss button in an alert, the close button in daisy-cotton's modal, the dropdown and floating action button triggers, the breadcrumb steps). Removed the attribute rows and examples for the sixteen from the Data display, Layout and Navigation tables and moved their notes; fixed the shared vocabulary table (button sizes, alert variants, breakpoints). getting-started.md and README.md no longer say both packages ship button and menu: only `icon` is shared. layout.md says the dock class is passed by the shell's template. navigation.md says the menu sits in a nav. views.md names the alert's four variants. CONTEXT.md and skills/django-mvp/SKILL.md list the sixteen as daisy-cotton's and drop the "bare until #435" wording.
Verified: forge verify --steps docs,lint passed; rendered the new examples (button with only, modal with only, alert, dropdown, breadcrumbs, avatar group) through the cotton fixture in a scratch test; pytest tests/test_checks.py tests/test_smoke.py tests/test_utils.py tests/test_components/test_declared_attributes.py tests/test_views/test_inline.py tests/test_components/test_daisy_cotton_install.py: 735 passed.
Next: T010 changelog.
Watch: the daisy-cotton documentation link is the repository, since no per-component pages could be confirmed; the README and component gallery are named in the text.

## 2026-10-05T17:12:40Z · Implementer US4 · T010

Did: one breaking entry under Unreleased / Changed naming all sixteen tags, with a table of every row of FR-006 and what to write now, the divider swap on its own paragraph, no aliases, the override note, the other differences (badge span, dock nav, menu no longer w-full or role=navigation, breadcrumb crumb text span, mockup window and phone, button and badge sizes xs to xl), the 0.1.3 floor, the six classes gone from the stylesheet and a Known gaps note with two items linking daisy-cotton#135 and #136. A Fixed line covers a MESSAGE_TAGS level tag no longer raising. Two sentences in the existing daisy-cotton dependency entry and the prefix entry said both packages ship components under the same names and that the basic components wait for #435; both were no longer true and are corrected in place.
Verified: forge verify --steps docs,lint passed. Rendered a menu with horizontal="lg", dividers with horizontal and vertical, and a link without href to confirm what the table says. No version number, date or release.
Next: full verify, ledger rows, report.
Watch: the old avatar group overlap mapping (xs to xxl to -space-x-2 to -space-x-12) was read from the deleted template in git history.

## 2026-10-05T17:20:21Z · Forge · converge

Converged. Rebased on main (d4cb801). The only rule graduated to ADR 0032 (D24); ADR 0030's sentence about the bare names was brought up to date. Verify green on the whole feature diff; the fourteen changed test files map to D23; story comments on all four issues.
