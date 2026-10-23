# Decisions: Page titles share one set of arguments and a choice of layouts

Questions the specification settled without asking, what was chosen, and why. Sam's own rulings
during intake are in `spec.md` under Clarifications and are not repeated here.

## D1 — Actions on list and table pages stay in the toolbar

**Ambiguous:** list and table pages draw their `page.actions` block in the toolbar, not the title
row; the list template says so in a comment. A view-set `page_actions` could go in either place.

**Chosen:** the toolbar, beside Add, whatever the title layout.

**Why:** the toolbar is where a reader of a list already looks for what they can do with it, and
moving Add into the title on some layouts and not others would make one page type behave two
ways. The title layout decides how the title is arranged; it does not move the page's controls.

## D2 — Actions set on a detail view are added to Edit and Delete

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

## D3 — An unknown layout fails loudly

**Ambiguous:** a layout name that matches nothing could fall back to the default.

**Chosen:** an error naming the value, raised at startup for the settings and at render time for a
view.

**Why:** a fallback hides a typo until someone notices the page looks wrong. The settings already
fail at startup on values the package cannot use, and a view attribute is code the developer
wrote, so naming the view in the error points straight at it.

## D4 — A project's own layout is in scope

**Ambiguous:** a layout setting that accepts a template path was offered during intake as a
suggestion. Sam's reply was "looks good", which was read as taking it.

**Chosen:** a layout may be one of the shipped names or a template of the project's own (FR-011,
User Story 5, priority P3).

**Why:** G7 asks that customisation never dead-ends. Without it, a project that wants a layout the
package does not ship is back to overriding the whole `page.title` block on every template. It
costs little once the shipped layouts receive their arguments as one group, which FR-003 requires
anyway. It is the lowest-priority story, so it can be cut at the specification gate without
touching the others.

## D5 — Calling the component directly: `inline_actions` stays, `subtitle` is renamed

**Ambiguous:** intake confirmed both that projects calling `c-mvp.page.title` directly keep working,
`inline_actions` included, and that `page_subtitle` is renamed with no deprecation.

**Chosen:** `inline_actions` keeps working and draws the inline layout. The component's `subtitle`
attribute is renamed to `lead`, like the view's.

**Why:** the rename ruling was about the name, and one name in the view and another in the
component would leave two words for one thing. `inline_actions` names a layout rather than an
argument, so keeping it costs nothing and breaks nobody.

## D6 — An empty title draws no heading

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

## D7 — A new argument still adds a block to each page template

**Ambiguous:** FR-003 and SC-005 say an argument added later changes no page template. FR-005 gives
every argument a block of its own, and a block has to be declared in each page template, because
Django blocks cannot be shared through an include.

**Chosen:** the view gathers the arguments in one method, `get_page_title_args()`, and the page
templates read every block's default from that one group, `page.title_args`. A later argument
changes the view method, the layouts and one block per page template.

**Why:** the two requirements cannot both hold in full. FR-005 is the one a developer uses every
day, and the cost FR-003 meant to remove, four templates each naming every value the view
produces, is gone: overriding the one method changes what every page draws. Raised by the design
review and recorded here so it is visible at the merge gate.

## D8 — The design review's findings, and what was done

One reviewer, three lenses, one round (request changes: 2 high, 3 medium, 6 low, all verified or
likely; no finding against the spec except the edge case in D9). Each was applied to `plan.md`,
`research.md` or `tasks.md` and checked against its evidence:

- List and table pages would have drawn the view's actions in the title as well as the toolbar:
  they now give the title an empty actions slot.
- Overriding `get_page_title_args()` would not have changed the rendered title: every block's
  default now reads `page.title_args`, and T003 renders it.
- The Account Center overview took neither the group nor the layout: it now does, and T003 tests
  it.
- Passing the group to the layouts would have written it onto their root element as an attribute:
  the component no longer takes it, and forwards a caller's other attributes instead.
- A bare call to the component could read `layout` from the page: every name it declares now has
  an empty default.
- The resolver probes the four paths Cotton itself tries.
- The CHANGELOG records two further breaking changes; `page_type` and the toolbar's new slot are
  documented; the SC-003 test asserts structure, not classes; the demo's switch tests are dropped.

## D9 — The info trigger without a heading

**Ambiguous:** the spec's edge case says an empty title draws no heading and the other arguments
are still drawn; FR-013 says the info trigger sits beside the heading. The sketch dropped the
trigger with the heading.

**Chosen:** the trigger is drawn whenever there is info text, beside the heading when there is
one. Emptying `page.heading` therefore removes the heading alone, as FR-005 requires.

**Why:** it satisfies the edge case, FR-005 and FR-008 at once, and FR-013 still holds wherever
there is a heading to sit beside.

## D10 — The shipped-name resolver is written in T002, the probe and the error in T006

**Decision:** `title_layout_component()` in `mvp/utils.py`, and the filter of the same name, come
back in T002 as the shipped-name mapping alone. T006 adds the probe for a project's own
component and the error, test-first.

**Why:** restoring the sketch's Python removed the filter the component's dispatcher calls, and
no component test can render a layout without it. The mapping is the smallest thing the
dispatcher needs; the behaviour T006 specifies (the probe, the error) has no code until T006's
tests are red.

**Revisit if:** T006's mapping test passes on its first run for this reason and the reviewer
wants it shown able to fail; the mutation is recorded in T006's evidence.

## D11 — `title_layout` joins the page context in T004

**Decision:** T001's page context carries `title_args` and not `title_layout`. T004 adds
`page_type`, the setting, `get_page_title_layout()` and the context key together. Until then the
page templates pass an empty layout and every page draws `default`.

**Why:** the layout's value is the setting resolved for the view's page type, which is T004's
behaviour. A key written earlier would have carried a stub value with no test that could fail.

**Revisit if:** a story that ships before T004 needs a table page's title in its toolbar.
