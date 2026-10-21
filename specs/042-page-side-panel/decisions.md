# Decisions: FS-042

## Self-resolved ambiguities (coverage scan, 2026-10-21)

**Drawer open when the window widens past the breakpoint.** Chosen: it closes. Leaving it open
would leave the page dimmed and unreachable behind a panel that is now also a column. Defensible
because nothing the reader chose is lost: the panel's content is the same in both forms.

**Two panels on one page.** Chosen: one. Two columns beside one content area leave too little room
for the content at any common screen width with the app sidebar open, and no request asked for it.
A project needing two writes its own layout with the page layout component's pieces.

**List page with every filter in the toolbar.** Chosen: no panel and no button, matching today's
rule that such a page has no Filter button and no modal (FS-041).

**Panel taller than the screen.** Chosen: it scrolls inside its own column. The alternative,
dropping the stickiness, would make a long filter panel's apply button unreachable without scrolling
the whole page to the bottom. The scrolling region is focusable and named, per ADR 0013.

**Pages that fill the screen's height.** Chosen: a full-height column with no sticking. On such a
page the window does not scroll, so sticking has nothing to do, and the content region already
scrolls inside itself.

## Why the default breakpoint is extra large

At the large width with the app sidebar open, about 760px remains for the page. A 16rem column and
its gap leave about 460px for the content, below a readable line length for body text and too
narrow for a three-column card grid. At extra large about 1020px remains.
