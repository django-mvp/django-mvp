
## 2026-10-21T10:42:46Z · Forge · S3

Did: build started on the spec-approved branch, rebased onto origin/main 17788c4. research.md, plan.md, tasks.md written; ledger created and moved to PLAN; PR #570 relabelled building, milestone v1.0.0, Closes block confirmed (#569, #571-#575).
Verified: kit/forge verify on the rebased branch: lint, types, build, conformance, docs green; 1853 tests pass; four CDN-bound axe browser tests fail locally only (decisions D6).
Next: design review.
Watch: the list region swap must refresh the panel (D3).

## 2026-10-21T10:46:50Z · Forge · S3R

Did: tried to dispatch the design reviewer four times (default, opus, sonnet, claude-cli model ids); every spawn was refused with "the selected account or native runtime is unavailable".
Verified: plan, tasks, research and ledger committed.
Next: resume at S3R design review when sessions_spawn works again; the brief is the same.
Watch: nothing built yet; no code on the branch beyond specs/.

## 2026-10-21T11:09:40Z · Forge · S3R

Did: design review (one reviewer, three lenses) returned request_changes: 1 high, 1 medium, 4 low, all verified or likely; receipts green. Applied all six to plan.md and tasks.md: panel id on the component root with the aside as {id}-panel (high, verified against htmx 2.0.10 oobSwap), table heading row and empty state added to the panel refresh, breakpoint width from BREAKPOINT_WIDTHS, aside always a tab stop, appearance assertions dropped from T006/T010, T008 reduced to evidence. Notes swept in (root_attr stops at first tag, region prop on the filter panel, page_view.html section, translated strings, docstrings, CONTEXT.md lines). D4 updated, D7 added.
Verified: check-receipts on the findings green; each remedy checked against the finding's evidence; speckit check green.
Next: S4, dispatch A (US-4, US-1, US-5).
Watch: Alpine calling destroy() on an htmx-removed component is unverified; T010 and T016 test it.

## 2026-10-21T11:17:50Z · Implementer US4 · T001

Did: published the header height as --mvp-header-height (assets/js/header_height.js, 0px with no .mvp-header or a header that does not stick), added the 4rem fallback and html scroll-padding-top to base.css, rebuilt both artifacts, wrote the Header height docs section and a changelog entry.
Verified: uv run pytest tests/test_components/test_header_height_e2e.py -> 5 passed; red first (4 of 5 failed before the script); with scroll-padding-top set to 0 in the built CSS the anchor and the keyboard-focus tests fail, so both discriminate.
Next: US1 T002.
Watch: CONTEXT.md has no Header height entry; the brief names the term but T001 does not list CONTEXT.md.

## 2026-10-21T11:20:24Z · Implementer US1 · T002

Did: added the root_attr filter (first start tag only, HTMLParser stopped by an exception) and TestRootAttr.
Verified: uv run pytest tests/test_templatetags.py -> 52 passed; 14 TestRootAttr cases red before the filter existed; ruff and mypy clean.
Next: T003 page layout component.
Watch: no docs page yet names the filter; it is an internal helper of the layout.

## 2026-10-21T11:21:00Z · Implementer US1 · T003

Did: added <c-mvp.page.layout> (header wrapper only when a header is given, panel placed by root_attr of its own root) and its tests, which pass the panel as a bare element so they say nothing about the panel component.
Verified: uv run pytest tests/test_components/test_page_layout.py -> 13 passed; all 13 red before the component was rewritten.
Next: T004 page side component and stylesheet.
Watch: the stand-alone and with-panel cases here are also US5-1 and US5-2 evidence for T008.

## 2026-10-21T11:23:50Z · Implementer US1 · T004

Did: added <c-mvp.page.side> (root div carries the id and data attributes, the aside is {id}-panel, always tabindex 0; drawer markup without x-data) and its stylesheet: widths, the column utility, the grid and its rows variable, the aside as scroller with a focus ring, and the filled-page rules. Rebuilt the stylesheet.
Verified: uv run pytest tests/test_components/test_page_side.py -> 28 passed (28 red before the template existed); lint clean; every breakpoint variant found in the built CSS.
Next: T005 the page.side block.
Watch: drawer-start is not a daisyUI class; the prototype wrote it and it is kept, harmless. The Alpine directives (x-ref, @click) are inert until T009 adds x-data.

## 2026-10-21T11:25:07Z · Implementer US1 · T005

Did: page_view.html draws <c-mvp.page.layout> around the title, content and the new page.side block; block names and nesting are otherwise unchanged. Added the page.side row to the Layer 2 block table (its Side panel anchor lands in T007).
Verified: uv run pytest tests/test_templates.py::TestPageViewSideBlock -> 5 passed (2 red before the template change; the 3 that characterise today's structure passed on the old template, as they should); tests/test_views and test_templates with -n auto: 834 passed, 4 failed (the CDN-bound axe tests, D6).
Next: T006 the column in a browser.
Watch: ruff format reformatted one pre-existing line in tests/test_templates.py; I restored it.

## 2026-10-21T11:27:54Z · Implementer US1 · T006

Did: wrote TestSideColumn against a test-only page served at /side-test/ (a function view in the test module, its URLconf set by an autouse fixture): sticky panel under the header, also after the header grows; non-sticky scrolls away; a tall panel scrolls on its own, takes Tab focus and scrolls by PageDown; on a filled page the panel is the layout height, not sticky, document does not scroll; rtl start panel on the right.
Verified: uv run pytest tests/test_components/test_page_side_e2e.py -> 7 passed. They passed on first run because T004 already carries the CSS, so I probed them by editing the built CSS: sticky->static fails 2, dropping the aside max-height/overflow fails 2, filled-page unstick reverted fails 1, dropping the fill layout flex/min-height fails 1 (after strengthening the filled-page test, which first passed under that mutation). Built CSS restored.
Next: T007 docs and demo page.
Watch: the rtl case flips dir after load; no markup carries dir.

## 2026-10-21T11:30:01Z · Implementer US1 · T007

Did: wrote the Side panel section of docs/layout.md (an On this page example in page.side with one attribute per option, and a stand-alone <c-mvp.page.layout> example), the components.md rows, CONTEXT.md entries (Side block, Side panel, Page layout, and Header height) with the line telling the page layout from the app shell Layout, a changelog entry, the skill routing line, and the demo Layout > Side Panel page (view, url, menu item, template) from the prototype.
Verified: uv run pytest tests/test_demo/test_pages.py::TestPageSideDemoPage -> 12 passed; red with the route removed (12 failed). The demo ships without the prototype's panel button and its Toggle option, since that component is US2; I added an off value for breakpoint so breakpoint=False is switchable.
Next: US5 T008.
Watch: the demo and docs say a drawer is not shown until the page can open it; US2 adds the button and its docs. The demo list page with side filters from the prototype is US3, not copied.

## 2026-10-21T11:32:10Z · Implementer US5 · T008

Did: confirmed the page layout stands alone and added nothing. US5-1 (layout with title, content and panel, as page_view.html draws it) is covered by test_page_layout.py TestPageLayoutWithAPanel (order, regions) and by test_templates.py TestPageViewSideBlock::test_a_page_filling_the_block_draws_the_layout_with_its_panel; US5-2 (no panel: title and content only) by TestPageLayoutWithoutAPanel::test_draws_the_title_and_content_with_no_wrapper. docs/layout.md carries the stand-alone example under "A side panel in a template of your own".
Verified: rendered the docs example once, outside the suite, through the Cotton compiler: it draws the layout with a start panel before the content. Full direct suite: 2503 passed, 1 skipped (axe tests deselected, D6).
Next: US2 T009.
Watch: none.

## 2026-10-21T11:42:26Z · Implementer US2 · T009

Did: wrote the markup tests first (TestDrawerConfiguration, TestSidePanelToggle; 16 red: no x-data, no toggle template), then the module assets/js/page_side.js (mvpPageSide, mvpPageSideToggle, registered from index.js), x-data on a drawer root carrying only the id and the breakpoint in rem, and <c-mvp.page.side.toggle>. The toggle's visibility rules were already in base.css from T004, so the stylesheet is unchanged after build-stylesheet.
Verified: uv run pytest tests/test_components/test_page_side.py -> 45 passed; uv run invoke build-js, build-stylesheet (stylesheet artifact unchanged).
Next: T010 the drawer in a browser; the behaviour is only proven there.
Watch: breakpoint_px is a simple tag, not a filter, so the template uses {% breakpoint_px breakpoint as ... %} then widthratio. The module listens on window for open and Escape, so the markup holds no handlers beyond the overlay and close button that already called close().

## 2026-10-21T11:57:53Z · Implementer US2 · T010

Did: wrote TestSideDrawer (15 cases, a test-only page at /side-drawer-test/ with the button, collapse, breakpoint and position read from the query string). Two failed on first run: Tab past the last link left the panel (a real gap in the module, so mvpPageSide now wraps Tab and Shift+Tab, D8), and a test page variable named breakpoint was shadowed by the shell's, so I renamed the page's keys.
Verified: uv run pytest tests/test_components/test_page_side_e2e.py tests/test_components/test_page_side.py -> 67 passed. Every test that passed first time was shown failing against a mutation of the code it guards, then restored: no inert (2 tests), no focus return (3), no focus into the panel (11), no Tab wrap, no media listener, destroy keeps inert, no Escape, no announce, overlay and close button not wired (one each), drawer always on one side (start and end), drawer starts open (hidden-panel and no-button tests), stacked drawn as a drawer, stacked toggle rule removed, breakpoint=False given xl, built CSS rule hiding the button at xl removed, and the overlay class removed.
Next: T011 documentation.
Watch: the CSS hides the button when no drawer panel exists on the page, not when none has that id; the button's id is not matched in CSS.

## 2026-10-21T11:59:03Z · Implementer US2 · T011

Did: docs/layout.md gains "On a narrow screen" (the drawer, the button and where to put it, what opening does, closing, widening past the breakpoint, stack, breakpoint=False, a swap with the drawer open); docs/components.md has the toggle's row; CONTEXT.md defines Panel button; the changelog has the entry. The demo's Side Panel page now carries the button in page.actions with a Toggle option, so "not shown" can be seen.
Verified: uv run pytest tests/test_demo/test_pages.py::TestPageSideDemoPage -> 12 passed; build-stylesheet left the stylesheet artifact unchanged.
Next: the full verify and the completion report.
Watch: the demo files are outside T011's Files line; the brief asked for the button on the demo page.

## 2026-10-21T12:07:28Z · Implementer US3 · T012

Did: renamed modal_fields / modal_applied_count / clear_modal_url to panel_fields / panel_applied_count / clear_panel_url in FilterContextMixin; each panel field's widget now carries form="filterForm"; MVPListViewMixin publishes filter_panel_attrs (default start / content) and filter_panel_id (default "filters"); reworded the "filter modal" docstrings. The two list templates read the renamed keys (a rename only) so the tree stays green until T013/T014 replace the modal.
Verified: uv run pytest tests/test_views/test_list.py (212 passed); new TestFilterPanelContext failed first with KeyError panel_fields.
Next: T013, the panel component.
Watch: the key rename in list_view.html and table_view.html is outside T012's Files line; it is mechanical and both files are rewritten in T014/T015.

## 2026-10-21T12:09:35Z · Implementer US3 · T013

Did: added <c-mvp.page.list.filters.panel> (fields, clear_url, id, region; everything else goes to <c-mvp.page.side label="Filters">) and its test module; reworded the actions component's description.
Verified: uv run pytest tests/test_components/test_list_filter_panel.py (18 passed; red first because the component did not exist). Probes: removing form="filterForm" from Apply, removing hx-select-oob from Clear, and dropping the empty-fields guard each failed a test; restored.
Next: T014 (list page), T015 (table page).
Watch: modal.html and test_list_filter_modal.py are still on disk because list_view.html and table_view.html draw the modal until T014/T015 switch them; both are deleted in T015, the last user. TestTheOverrideBeatsTheHeader goes with the modal's button: the panel's badge is a plain badge, not an indicator-item.

## 2026-10-21T12:14:45Z · Implementer US3 · T014

Did: list_view.html fills page.side with the filter panel and draws the panel button (count = panel_applied_count) where the Filter button was, only when panel_fields is not empty; the filter form, chips, pager and the empty state's Clear all carry hx-select-oob naming filter_panel_id; empty.html gains a panel prop beside region. Updated the pre-existing tests that asserted the modal (test_list.py, test_integrations.py, test_demo/test_list_filter_pages.py) to assert the panel.
Verified: failing first (16 failures with the templates reverted), then uv run pytest tests/test_views tests/test_integrations.py tests/test_demo tests/test_components/test_list_filter_panel.py tests/test_table_layout.py with TestErrorPagesAccessibilityE2E deselected: 830 passed.
Next: T015 (table page), which also deletes modal.html and its test module.
Watch: test_toolbar_stays_when_a_search_matches_nothing now passes toolbar_filters=["q"]: with no toolbar_filters the search is a panel field, and the old test only found it because the modal sat inside the toolbar. No dedicated test module exists for the empty state, so its out-of-band attribute is asserted from the list page.

## 2026-10-21T12:22:35Z · Implementer US3 · T015

Did: table_view.html now wraps the region in <c-mvp.page.layout> inside the filled page, with its own page.side block (block.super draws the same panel the list page does); the toggle replaces the Filter button; the filter form, chips and pager carry hx-select-oob; django_tables2/bootstrap5-mvp.html reads filter_panel_id from table.context for the heading row and the empty state. Deleted modal.html and test_list_filter_modal.py (nothing draws the modal any more). Rebuilt the stylesheet; one class was new.
Verified: red first (11 failures with the templates reverted), then tests/test_table_layout.py and tests/test_components (958 passed, 1 skipped); browser tests TestTheFilterPanelBesideTheTable (7 passed). Probes on mvp/tailwind/base.css, each rebuilt then restored: dropping the filled-page static rule failed the does-not-stick test; overflow-y visible failed the scroll test; align-self start with no height 100% failed the height test; flex none on the layout failed the fills-the-page tests. The gap test failed first, which found a 12px row gap from the layout's gap-3, fixed with gap-y-0!.
Next: T016 (browser tests in test_list_filters_e2e.py, list_view.js).
Watch: the pre-existing TestTheOverrideBeatsTheHeader test (indicator z-index) went with the modal's button; the base.css rule it read (.mvp-page-fill .indicator-item) is left in place because the Add button's badge elsewhere may use indicator, and base.css is outside this story's files.

## 2026-10-21T12:33:21Z · Implementer US3 · T016

Did: removed the modal's close handler and MODAL_ID from list_view.js; replaced TestFilterModalCloses and TestFilterModalApplies in test_list_filters_e2e.py with TestFilterPanel (11 browser tests: apply narrows and keeps search and sort and drops empty fields, apply from page two lands on page one, a toolbar change keeps the panel's values, the panel's Clear keeps toolbar and sort, the panel shows each response's state, breakpoint False puts the filters behind the button at 1440px, scrolling the panel keeps Apply and Clear in view, a developer's own widget and a Tom Select control are submitted, applying from an open drawer at 390px leaves it closed with nothing inert, and on a table page a sort chosen after applying survives Clear).
Verified: uv run pytest tests/test_list_filters_e2e.py (26 passed). Probes, each restored: the view no longer setting form="filterForm" on panel widgets failed 8 tests; Clear returning the bare path failed the Clear and table-sort tests; the filter form without hx-select-oob failed the state and open-drawer tests; the table heading row without hx-select-oob failed the table-sort test; the panel ignoring the view's attributes failed the breakpoint test; the foot without sticky failed the scrolling test.
Next: T017, documentation.
Watch: the scrolling test first failed because the sticky column only pins once the page has scrolled, so the test scrolls the window first. Tests that wait for an address that never arrives take 30s each when they fail.

## 2026-10-21T12:35:11Z · Implementer US3 · T017

Did: documented the filter panel. docs/views.md has a new "The filter panel" section (the form attribute, the out-of-band refresh, filter_panel_attrs, filter_panel_id) and every mention of the modal, the Filter button and the renamed context keys now reads as the panel; docs/integrations.md (table page blocks, including the new page.side row, and the renamed keys); docs/components.md (the panel component, the empty state's panel attribute, the hand-written list page example); CONTEXT.md (Filter panel replaces Filter modal, with a line telling it apart from the table page's page.panel block; Toolbar; the component tree); CHANGELOG.md (breaking entry). README.md does not name the modal.
Verified: grep for modal, filterModal, modal_fields, modal_applied_count, clear_modal_url and filters.modal across docs, README, CONTEXT, mvp and demo finds only the demo menu label "List, Filter Modal Only" (demo/menus.py, outside this story's files) and the changelog entry.
Next: full verify, then the report.
Watch: the demo still names its all-in-the-panel page product-list-modal-only (url name, menu label, class ProductModalOnlyListView); renaming touches demo files this story does not list.

## 2026-10-21T12:43:21Z · Forge · S5

Did: all five stories accepted. Converge: renamed the demo's every-filter page from modal to panel, dropped a removal-stays-removed assertion (T018). ADR verdicts on D1-D10; D3 graduated to ADR 0034 (out-of-band refresh beside the list region), D10 to ADR 0035 (behaviour lives in registered Alpine components). No migrations.
Verified: 2585 passed, 1 skipped (axe CDN class deselected, D6); stage-exit S5 green; tamper flags on the US3 diff are exactly the plan's retired/renamed tests plus one documented toolbar test.
Next: S6 review.
Watch: a toggle naming a missing panel id is shown (CSS cannot compare ids).

## 2026-10-21T12:53:00Z · Implementer FIX-1 · T019

Did: startHeaderHeight() keeps its ResizeObserver in module scope, disconnects it and observes the new header; index.js calls it from the body-target afterSettle branch. Added a boosted-navigation browser test.
Verified: test_header_height_e2e.py 6 passed; with the afterSettle call removed the new test fails (wait_for_function timeout), 5 passed 1 failed.
Next: T020.
Watch: header_height.js header comment is over three lines; T020 trims it.

## 2026-10-21T12:55:12Z · Implementer FIX-1 · T022

Did: wrapTab filters candidates to tabIndex >= 0, not type=hidden, checkVisibility(). Added a drawer page variant (?tail=1) ending in a hidden input and a closed details, and a Tab-wrap test.
Verified: test_page_side_e2e.py 23 passed; with the filter removed the new test fails (focus ends on no element), 1 failed.
Next: T021, T020.
Watch: the drawer test page template gained an opt-in tail block.

## 2026-10-21T12:55:35Z · Implementer FIX-1 · T021

Did: docs/layout.md (table, prose) and docs/components.md (table) write :breakpoint="False".
Verified: grep finds no bare breakpoint="False" under docs/.
Next: T020.
Watch: none.

## 2026-10-21T12:58:37Z · Implementer FIX-1 · T020

Did: trimmed every comment this branch added to at most three lines (header_height.js, page_side.js, base.css, the page layout, side panel, list/table/page views, table header, demo side page); long explanations point at docs/layout.md and docs/adr/0034 and 0035; FR-011 is now FS-042 FR-011.
Verified: a scan of the branch diff finds no added comment block over three lines and no bare FR/SC/US reference; build-stylesheet and build-js left the artifacts unchanged; components, templates, table layout, list view and demo tests 1455 passed, 1 skipped.
Next: full suite and verify.
Watch: a two-line comment in a template is written as two {# #} lines so the block stays within three lines.

## 2026-10-21T13:03:01Z · Forge · S6

Did: code review (phase 1) returned 2 high, 1 medium, 1 low; all accepted as T019-T022 and fixed by one dispatch. Review outcome recorded on the PR with zero open findings.
Verified: receipts green for reviewer and fixer; T019 and T022 mutations re-run independently (each 1 failed with the fix removed, restored); 2587 passed, 1 skipped (axe CDN class deselected); lint, typecheck, build, conformance, docs green; tamper-check clean against the pre-fix base.
Next: S7, walkthrough and ready for review.
Watch: no test pins a boosted page reached from a headerless page; the same call covers it.

## 2026-10-21T13:06:07Z · Forge · S7

Did: PR description rewritten with the Closes block; walkthrough checklist laid out on the PR; dev server on 8002 serving this worktree; ledger at PR_READY.
Verified: stage-exit S6 green; 2587 passed, 1 skipped (axe CDN class deselected).
Next: push as the bot, mark ready, CI green, stage-exit S7, merge gate.
Watch: nothing pushed after ready except a fix Sam asks for.

## 2026-10-21T15:20:28Z · Implementer FIX-2 · T023

Did: reproduced the end drawer jumping in (browser test, ltr fails, rtl passes). Cause: the end panel is translated past the right edge of an overflow box, and focusing its close button while it is still moving scrolls that box, so the panel jumps to its open position; the start side translates into unscrollable negative overflow. Fix: focus with preventScroll. Rebuilt the bundle.
Verified: uv run pytest tests/test_components/test_page_side_e2e.py: 25 passed; the new test fails with the preventScroll option removed.
Next: T024.
Watch: none.

## 2026-10-21T15:21:59Z · Implementer FIX-2 · T024

Did: the list view's filter_panel_attrs default is now {"position": "end"}; the filter panel template aligns content at the end and title at the start unless align is set. Updated the tests that pinned the start default, docs/views.md and the CHANGELOG; no demo page sets the default.
Verified: test_list_filter_panel, test_table_layout, test_views/test_list pass; two mutations fail (align default swapped; view default back to start).
Next: T025.
Watch: none.

## 2026-10-21T15:22:45Z · Implementer FIX-2 · T025

Did: the table page layout uses gap-0! in place of gap-y-0!, so no column gap sits between the filter panel and the table; the new browser test measures that the table area and the panel meet. Rebuilt the stylesheet.
Verified: test_table_layout_e2e and test_table_layout: 125 passed; the new test fails (1144 vs 1184) with gap-y-0! restored.
Next: full suite and verify.
Watch: none.

## 2026-10-21T15:27:15Z · Forge · S7

Did: Sam's merge-gate changes as T023-T025: end drawer slides in (focus with preventScroll), filter panel defaults to end with alignment following its side, table layout has no gap. Spec FR-014 and its clarification updated; D11. Long-contents demo option already off by default; kept.
Verified: receipts green; 2594 passed, 1 skipped (axe CDN class deselected); T023 mutation re-run 5 times: fails 4 of 5 (timing-sampled), fix green 3 of 3; tamper flags unchanged from the planned modal retirements.
Next: push, CI, walkthrough comment edited, merge gate.
Watch: T023's test samples mid-transition, so it can miss the regression on a slow run; it never fails a correct build.
