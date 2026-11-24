"""Write static/daisy_cotton_layout/layout.css.

Run with ``python -m daisy_cotton_layout.build_css``. A container query cannot
take its width from a custom property, so the drawer rules are written out once
for each breakpoint here rather than by hand.
"""

from pathlib import Path

BREAKPOINTS = {"sm": "40rem", "md": "48rem", "lg": "64rem", "xl": "80rem", "2xl": "96rem"}

BASE = """\
/* Layouts arranged by a layout code, such as lHh LpR lff.
   Written by daisy_cotton_layout/build_css.py: edit that file, not this one.

   The colours are daisyUI's theme variables, so the layout follows the
   host's theme. Every rule reaches its areas through child combinators, so a
   layout nested inside another is styled by its own code and nothing else. */

.dcl {
  --dcl-header-h: 0px;
  --dcl-footer-h: 0px;
  --dcl-dir: 1;
  --dcl-vh: 100dvh;
  container: dcl / inline-size;
  min-width: 0;
}
[dir="rtl"] .dcl,
.dcl[dir="rtl"] {
  --dcl-dir: -1;
}

/* A contained layout fills the box it is given and scrolls inside it. Its
   root holds still, so a drawer drawn against it stays in view while the
   grid inside it scrolls. */
.dcl[data-dcl-container] {
  --dcl-vh: 100cqh;
  container: dcl / size;
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.dcl-grid {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  grid-template-rows: auto 1fr auto;
  grid-template-areas: var(--dcl-areas);
  min-height: 100dvh;
}
.dcl[data-dcl-container] > .dcl-grid {
  height: 100%;
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
}

.dcl-grid > .dcl-header { grid-area: header; min-width: 0; }
.dcl-grid > .dcl-page { grid-area: page; min-width: 0; }
.dcl-grid > .dcl-footer { grid-area: footer; min-width: 0; }
.dcl-grid > .dcl-sidebar[data-side="left"] { grid-area: left; }
.dcl-grid > .dcl-sidebar[data-side="right"] { grid-area: right; }

/* Upper case in the code: the area stays in place while the layout scrolls. */
.dcl[data-dcl-header-fixed] > .dcl-grid > .dcl-header {
  position: sticky;
  top: 0;
  z-index: 30;
}
.dcl[data-dcl-footer-fixed] > .dcl-grid > .dcl-footer {
  position: sticky;
  bottom: 0;
  z-index: 30;
}

/* A header that stays gets a line under it once the layout has scrolled. */
.dcl[data-dcl-header-fixed] > .dcl-grid > .dcl-header {
  transition: box-shadow 0.15s ease;
}
.dcl[data-dcl-header-fixed][data-dcl-scrolled] > .dcl-grid > .dcl-header {
  box-shadow: 0 1px 0 var(--dcl-line, var(--color-base-300)), 0 1px 3px rgb(0 0 0 / 0.06);
}
.dcl[data-dcl-footer-fixed] > .dcl-grid > .dcl-footer {
  box-shadow: 0 -1px 0 var(--dcl-line, var(--color-base-300));
}

/* A sidebar beside the page. Its column is as wide as it is, so a closed
   sidebar, or one the page left empty, takes no space. */
.dcl-grid > .dcl-sidebar {
  --dcl-w: 16rem;
  --dcl-rail-w: 4rem;
  --dcl-mode: docked;
  width: var(--dcl-w);
  min-width: 0;
  background: var(--dcl-sidebar-bg, var(--color-base-100));
  transition: width 0.2s ease;
}
.dcl-grid > .dcl-sidebar[data-side="right"] { --dcl-w: 18rem; }
.dcl-grid > .dcl-sidebar[data-side="left"] > .dcl-panel {
  border-inline-end: 1px solid var(--dcl-line, var(--color-base-300));
}
.dcl-grid > .dcl-sidebar[data-side="right"] > .dcl-panel {
  border-inline-start: 1px solid var(--dcl-line, var(--color-base-300));
}
.dcl-grid > .dcl-sidebar > .dcl-panel {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  width: var(--dcl-w);
  min-height: 100%;
}
.dcl-grid > .dcl-sidebar > .dcl-backdrop { display: none; }

.dcl[data-dcl-left-fixed] > .dcl-grid > .dcl-sidebar[data-side="left"] > .dcl-panel,
.dcl[data-dcl-right-fixed] > .dcl-grid > .dcl-sidebar[data-side="right"] > .dcl-panel {
  position: sticky;
  z-index: 20;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
}
.dcl[data-dcl-left-fixed] > .dcl-grid > .dcl-sidebar[data-side="left"] > .dcl-panel {
  top: var(--dcl-left-top);
  height: calc(var(--dcl-vh) - var(--dcl-left-top) - var(--dcl-left-bottom));
}
.dcl[data-dcl-right-fixed] > .dcl-grid > .dcl-sidebar[data-side="right"] > .dcl-panel {
  top: var(--dcl-right-top);
  height: calc(var(--dcl-vh) - var(--dcl-right-top) - var(--dcl-right-bottom));
}

/* Closed beside the page: slid away, or an icon rail. */
.dcl-grid > .dcl-sidebar[data-state="closed"][data-collapse="offcanvas"] {
  width: 0;
  overflow: clip;
}
.dcl-grid > .dcl-sidebar[data-state="closed"][data-collapse="offcanvas"] > .dcl-panel {
  visibility: hidden;
  transition: visibility 0s linear 0.2s;
}
.dcl-grid > .dcl-sidebar[data-state="closed"][data-collapse="icons"] { width: var(--dcl-rail-w); }
.dcl-grid > .dcl-sidebar[data-state="closed"][data-collapse="icons"] > .dcl-panel {
  width: var(--dcl-rail-w);
  overflow-x: hidden;
}

/* Content that is only for the open sidebar, or only for the rail. */
.dcl-rail-only { display: none; }
.dcl-sidebar[data-dcl-rail] .dcl-rail-hide { display: none !important; }
.dcl-sidebar[data-dcl-rail] .dcl-rail-only { display: revert; }

/* The script hides a toggle with nothing to toggle. daisyUI's buttons set
   their own display, which would otherwise beat the hidden attribute. */
.dcl-toggle[hidden],
[data-dcl-when][hidden] { display: none !important; }

@media (prefers-reduced-motion: reduce) {
  .dcl-grid > .dcl-sidebar,
  .dcl-grid > .dcl-sidebar > .dcl-panel,
  .dcl-grid > .dcl-sidebar > .dcl-backdrop { transition: none !important; }
}

@media print {
  .dcl-grid > .dcl-sidebar { display: none; }
  .dcl[data-dcl-header-fixed] > .dcl-grid > .dcl-header,
  .dcl[data-dcl-footer-fixed] > .dcl-grid > .dcl-footer { position: static; }
}
"""

# One sidebar as a drawer over the page. {s} is the selector of the sidebar.
DRAWER = """\
{s} {{
  --dcl-mode: overlay;
  width: 0;
  overflow: visible;
}}
{s} > .dcl-panel {{
  position: fixed;
  top: 0;
  bottom: 0;
  z-index: 40;
  width: min(var(--dcl-w), 100% - 3.5rem);
  height: auto;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  visibility: hidden;
  border-inline-width: 0;
  background: var(--dcl-sidebar-bg, var(--color-base-100));
  box-shadow: 0 0 2rem rgb(0 0 0 / 0.25);
  transition: translate 0.25s ease, visibility 0s linear 0.25s;
}}
{s}[data-side="left"] > .dcl-panel {{
  inset-inline-start: 0;
  translate: calc(-100% * var(--dcl-dir)) 0;
}}
{s}[data-side="right"] > .dcl-panel {{
  inset-inline-end: 0;
  translate: calc(100% * var(--dcl-dir)) 0;
}}
{s}[data-overlay="open"] > .dcl-panel {{
  translate: 0 0;
  visibility: visible;
  transition: translate 0.25s ease, visibility 0s;
}}
{s} > .dcl-backdrop {{
  display: block;
  position: fixed;
  inset: 0;
  z-index: 39;
  background: rgb(0 0 0 / 0.4);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}}
{s}[data-overlay="open"] > .dcl-backdrop {{
  opacity: 1;
  pointer-events: auto;
}}
{c} > .dcl-panel,
{c} > .dcl-backdrop {{
  position: absolute;
}}
"""


def drawer(sidebar: str) -> str:
    """The drawer rules for one sidebar selector, such as ``.dcl-sidebar[...]``."""
    return DRAWER.format(
        s=f".dcl > .dcl-grid > {sidebar}",
        c=f".dcl[data-dcl-container] > .dcl-grid > {sidebar}",
    )


def build() -> str:
    parts = [BASE, "\n/* A sidebar whose behaviour is overlay is a drawer at every width. */\n"]
    parts.append(drawer('.dcl-sidebar[data-side][data-behavior="overlay"]'))
    for name, width in BREAKPOINTS.items():
        block = drawer(f'.dcl-sidebar[data-side][data-behavior="auto"][data-breakpoint="{name}"]')
        indented = "".join(f"  {line}" if line.strip() else line for line in block.splitlines(True))
        parts.append(
            f"\n/* Below {width} of layout width, a sidebar with breakpoint {name} is a drawer. */\n"
            f"@container dcl (width < {width}) {{\n{indented}}}\n"
        )
    return "".join(parts)


def main() -> None:
    target = Path(__file__).parent / "static" / "daisy_cotton_layout" / "layout.css"
    target.write_text(build())
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
