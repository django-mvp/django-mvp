
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
