# ADR 0037 — Page title layouts are named Cotton components

**Status:** accepted

## Decision

Every page title is drawn by `<c-mvp.page.title>` from one set of arguments: eyebrow, title, lead, actions, info and info actions. The view sets each one with its own attribute and `get_page_*()` method, and `get_page_title_args()` gathers them into `page.title_args`. Every page template fills the component's slots from blocks whose defaults read that group, one block per argument (`page.eyebrow`, `page.heading`, `page.lead`, `page.info`, `page.actions`), inside `page.title`.

The arrangement is a title layout: a Cotton component chosen by name. `default`, `inline`, `centred` and `compact` ship under `cotton/mvp/page/title/`. Any other name is a Cotton component of the project's own and receives the same five slots. The name comes from the view's `page_title_layout` (or `get_page_title_layout()`), otherwise from `MVP_CONFIG["page_title"]["layout"]` for the view's `page_type`. `mvp.utils.title_layout_component()` turns a name into a component and raises `ImproperlyConfigured` for one it cannot find, at render time for a view and at startup (`mvp.E003`) for the setting.

## Why

One fixed title row did not suit every page, and the only way to change it was to override the whole block in every template. A named layout keeps the choice declarative and in the order Article XII sets (view, then setting, then default), and a project's layout works exactly like a shipped one, so the choice never dead-ends.

One attribute per argument, rather than one dictionary on the view, lets a subclass change one argument in one line, and matches every other page attribute. The gathering method gives back the single place to set the whole title.

Blocks per argument let a template replace one part without copying the rest. The cost is that a new argument adds one block to each page template, because Django blocks cannot be shared through an include.

The component gives every attribute an empty default, because Cotton reads an attribute that has no default from the caller's context when the call has no `only`. Without the default, a bare call could draw a `lead` or a `layout` that belongs to the page.

## Revisit if

Django gains a way to share a block structure between templates. A shared structure would let a new argument reach every page template from one place.
