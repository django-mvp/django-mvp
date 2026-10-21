
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
