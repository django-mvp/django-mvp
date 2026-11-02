# ADR 0039 — Each base colour has one meaning

**Status:** accepted

## Decision

`base-100` is raised: cards, inputs, modals, dropdowns and tables. `base-200` is the page: the page background, the header and the dock. `base-300` is sunk: the sidebar, wells, stripes and placeholders. Every template in the package follows these meanings, so a theme sets colours and nothing else.

The page default moves from daisyUI's `base-100` to `base-200` by setting `--root-bg`. A theme can still set `--root-bg` to put the page elsewhere.

One optional property, `--color-line`, gives the default button, borders and rules a colour that shows on all three surfaces. When a theme leaves it unset it is worked out from `base-300` and `base-content` where it is read, not at the root, so a region with its own surfaces gets a line that belongs to them.

## Why

daisyUI, the templates and themes each assumed something different about which colour was the page, and every theme that moved the page found the difference: default buttons the colour of the page, a filter panel foot on the wrong surface, a placeholder card with no shape, and a sidebar override and a button rule needed for raised cards.

The mapping follows what daisyUI already paints. Inputs, selects, textareas, modals, tables, tabs and toggles read `base-100`, so raised surfaces need no overrides. Making `base-100` the page would mean overriding those components, and raised cards on `base-200` would match the default button.

Each colour vanishes on its own surface, so a default button filled from `base-200` needs moving. daisyUI's coloured buttons set `--btn-color` and never read the fallback, so re-pointing `--color-base-200` on `.btn` moves only the default button and its hover. A value set at the root would resolve there, so a dark sidebar on a light page would draw the page's pale button with its own light text.

Package templates use `border-line` and `bg-line` instead of a stylesheet rule that repoints `.border-base-300`. A class named after a colour keeps meaning that colour.

## Revisit if

daisyUI gains a colour of its own for the default fill of a button, or themes turn out to need a line colour per surface.
