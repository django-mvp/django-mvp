# Decisions: Page titles share one set of arguments and a choice of layouts

Questions the specification settled without asking, what was chosen, and why. Sam's own rulings
during intake are in `spec.md` under Clarifications and are not repeated here.

## Actions on list and table pages stay in the toolbar

**Ambiguous:** list and table pages draw their `page.actions` block in the toolbar, not the title
row; the list template says so in a comment. A view-set `page_actions` could go in either place.

**Chosen:** the toolbar, beside Add, whatever the title layout.

**Why:** the toolbar is where a reader of a list already looks for what they can do with it, and
moving Add into the title on some layouts and not others would make one page type behave two
ways. The title layout decides how the title is arranged; it does not move the page's controls.

## Actions set on a detail view are added to Edit and Delete

**Ambiguous:** `detail_view.html` fills `page.actions` with the Edit and Delete links the view has
resolved. Under "a filled block wins over the view", a detail view's own `page_actions` would
never be drawn.

**Chosen:** the package's built-in actions (Add on list and table pages, Edit and Delete on detail
pages) and the view's actions are drawn together. A project template that fills `page.actions`
replaces all of them.

**Why:** a developer who sets `page_actions` on a detail view means "and also these". Silently
dropping them because the package's own template happens to use the block is a failure nobody
would notice until a reader went looking for the button. The project template keeps the last
word.

## An unknown layout fails loudly

**Ambiguous:** a layout name that matches nothing could fall back to the default.

**Chosen:** an error naming the value, raised at startup for the settings and at render time for a
view.

**Why:** a fallback hides a typo until someone notices the page looks wrong. The settings already
fail at startup on values the package cannot use, and a view attribute is code the developer
wrote, so naming the view in the error points straight at it.

## A project's own layout is in scope

**Ambiguous:** a layout setting that accepts a template path was offered during intake as a
suggestion. Sam's reply was "looks good", which was read as taking it.

**Chosen:** a layout may be one of the shipped names or a template of the project's own (FR-011,
User Story 5, priority P3).

**Why:** G7 asks that customisation never dead-ends. Without it, a project that wants a layout the
package does not ship is back to overriding the whole `page.title` block on every template. It
costs little once the shipped layouts receive their arguments as one group, which FR-003 requires
anyway. It is the lowest-priority story, so it can be cut at the specification gate without
touching the others.

## Calling the component directly: `inline_actions` stays, `subtitle` is renamed

**Ambiguous:** intake confirmed both that projects calling `c-mvp.page.title` directly keep working,
`inline_actions` included, and that `page_subtitle` is renamed with no deprecation.

**Chosen:** `inline_actions` keeps working and draws the inline layout. The component's `subtitle`
attribute is renamed to `lead`, like the view's.

**Why:** the rename ruling was about the name, and one name in the view and another in the
component would leave two words for one thing. `inline_actions` names a layout rather than an
argument, so keeping it costs nothing and breaks nobody.

## An empty title draws no heading

**Ambiguous:** today a page with an empty `page_title` draws an empty `<h1>`.

**Chosen:** no heading element when the title is empty; the other arguments are still drawn.

**Why:** an empty heading is announced by screen readers as a heading with no name. FR-008 already
says no layout draws an empty element for an argument the page does not give, and the title is no
exception.

## Left out of this feature

Offered during intake as suggestions and not taken into this specification; each can be its own
request later:

- the model's verbose name as an automatic eyebrow on detail, edit and delete pages;
- a `media` argument (an avatar or logo beside the title) and a `footnote` argument (a line under
  the lead), and the banner-style layouts that would use them.
