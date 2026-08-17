# Progress — 027 Full-screen tables and column styling helpers

## Spec gate — approved 2026-08-17

Approved by Sam, on condition that the specification folder be renamed: `027-full-screen-application`
did not describe the work. Renamed to `027-table-layout-and-column-styling`, and the feature branch
with it. The first draft pull request (#257) was opened from the old branch and could not follow the
rename, so it was closed and reopened as #258 from the renamed branch; the epic body and the gate
brief were re-pointed at the new paths.

Scope approved as specified: three stories, P1 layout, P2 column behaviour classes, P3 inferred
alignment. Four self-resolved ambiguities were carried in the brief and none was vetoed.

- Epic: #253
- Stories: #254 (P1), #255 (P2), #256 (P3)
- Pull request: #258 (draft)

## Layout story — complete 2026-08-17

Tasks T004–T014 landed. The scroll area, the rewritten page template, the refused ordering
declaration, the action set without sort, the pinned rows and the demo footer were all implemented
and committed by the implementer (`bfd1ed9`…`1348187`).

The browser evidence came back four assertions red, correctly. Two separate faults, both fixed
here rather than accepted:

1. **The shell had a height floor, not a ceiling.** `.drawer-content:has(.mvp-page-fill)` set
   `min-height: 100dvh`, so a page taller than the viewport pushed the whole shell taller instead
   of being bounded — and the window scrolled, which is the one behaviour this layout exists to
   prevent. The ceiling alone is inert, because a flex item's automatic minimum height stops
   `<main>` shrinking below its content, so both rungs above `<c-page.content>` release it.
   This is a defect in the filled-page mechanism shipped with #247, surfaced by its first
   consumer with content that overflows. Filled pages now clip and hand scrolling to their
   content, which is what `fill` always promised.
2. **The pinning tests were measuring the wrong element and had been passing vacuously.** DaisyUI
   pins `thead tr` and `tfoot tr`; the `<thead>` and `<tfoot>` boxes themselves stay with the
   table and travel off-screen with it. The tests measured the sections, and passed only because
   the table area never scrolled at all — `scrollTop = scrollHeight` was a no-op on an unscrollable
   container, so nothing was being asserted. They now measure the rows, and assert the scroll
   actually happened before asserting where the rows are.

Full suite 1219 passed, 1 skipped. Lint, format, type and dependency checks green. Both browser
suites green at 1440x900 and 390x844.

- Fix: `fa54fc6`
