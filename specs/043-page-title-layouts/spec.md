# Feature Specification: Page titles share one set of arguments and a choice of layouts

**Feature Branch**: `043-page-title-layouts`

**Created**: 2026-10-23

**Status**: Draft

**Serves**: G7 (customization that never dead-ends, from view configuration through component
override to a project's own CSS), G1 (a complete, responsive application shell that a project
configures rather than builds)

**Roadmap**: none. No roadmap item covers the page title; this may be a gap in the roadmap.

**Issue**: #593

**Input**: Every page type lays its title out in one fixed way, and that layout does not suit every
page. The view can set only the title and the subtitle, and anything more means overriding the
whole title block in a template. Every page title should take the same few arguments, named as
daisy-cotton-ext's heroes name them: an eyebrow, the title, a lead and actions, plus the existing
info dialog. Each can be set on the view or replaced by itself through its own template block. The
package ships a few title layouts; a developer picks one for the whole site in settings and can
choose another for any single view.

## Clarifications

### Session 2026-10-23 (intake)

Sam's rulings during intake:

- **Q: What are the arguments called?**
  A: The names daisy-cotton-ext's heroes use: eyebrow, title, lead and actions, alongside the
  existing info text and info actions. The subtitle becomes the lead. Recorded as FR-001.

- **Q: Does `page_subtitle` keep working after the rename?**
  A: No. It is renamed to `page_lead` outright, with no deprecation period. Recorded as FR-004.

- **Q: Can a template replace one argument without replacing the whole title area?**
  A: Yes. Every argument has its own template block as well as its own view attribute, and a block
  a template fills wins over the view. Recorded as FR-005 and FR-006.

- **Q: Is the title declared as one dictionary on the view, or as one attribute per argument?**
  A: One attribute per argument, each with its own method, so a subclass changes one argument in
  one line. One further method gathers them, so a view can set the whole title at once by
  overriding it, and the page template receives them as one group. Recorded as FR-002 and FR-003.

- **Q: Where is the layout chosen?**
  A: For the whole site in settings, as a default for each page type, and for any single view on
  the view. Recorded as FR-009 and FR-010.

### Session 2026-10-23 (coverage scan)

The coverage scan found five further ambiguities, each answered from the intake discussion. Longer
rationale is in `decisions.md`.

- **Q: Where are actions set on the view drawn on a list or table page?**
  A: In the toolbar, beside Add, where those pages draw their actions today, whatever the title
  layout. Recorded as FR-015.

- **Q: Do actions set on a detail view replace its Edit and Delete buttons?**
  A: No. They are drawn with them. A template that fills the actions block replaces all of them.
  Recorded as FR-015.

- **Q: What happens when a layout is named that does not exist?**
  A: The page fails loudly, naming the value, rather than drawing a page with no title. Recorded as
  FR-012.

- **Q: Can a project add a layout of its own?**
  A: Yes. A layout can be named by a template of the project's, which receives the same arguments
  as a shipped one. Recorded as FR-011.

- **Q: Does a template that calls the page title component directly keep working?**
  A: Yes, including its `inline_actions` attribute. Its `subtitle` attribute is renamed to `lead`,
  as on the view. Recorded as FR-018.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer sets a page's eyebrow, lead and actions from its view (Priority: P1)

A developer building a project dashboard wants a short category line above the heading, a
sentence under it and two buttons beside it. They set `page_eyebrow`, `page_lead` and
`page_actions` on the view, next to the `page_title` it already has, and the page draws all four.
On the project's detail page the eyebrow depends on the object, so they override
`get_page_eyebrow()` instead. A subclass of the dashboard changes only the lead, in one line.

**Why this priority**: It is the feature's shared vocabulary. Every layout and every block in the
other stories draws these arguments.

**Independent Test**: Render a page view that sets each argument by attribute, one that sets one
by method, and a subclass that changes one argument. Confirm each argument is drawn, the method's
value wins, and the subclass keeps its parent's other arguments.

**Acceptance Scenarios**:

1. **Given** a view that sets an eyebrow, a title, a lead and actions, **When** its page renders,
   **Then** the title area draws all four.
2. **Given** a view that overrides the method for one argument, **When** its page renders, **Then**
   the method's value is drawn for that argument.
3. **Given** a subclass that sets one argument, **When** its page renders, **Then** that argument is
   the subclass's and every other argument is the parent's.
4. **Given** a view that overrides the one method that gathers every argument, **When** its page
   renders, **Then** the title area draws what that method returns.
5. **Given** actions set on the view, **When** its page renders, **Then** each action is a button
   accepting the same keys as the info dialog's actions.
6. **Given** a view that sets none of the new arguments, **When** its page renders, **Then** no
   eyebrow, lead or actions are drawn and nothing empty is left in their place.
7. **Given** a view that still sets `page_subtitle`, **When** its page renders, **Then** no lead is
   drawn.
8. **Given** a list or table view that sets actions, **When** its page renders, **Then** they are
   drawn in the toolbar beside Add, whatever the title layout.
9. **Given** a detail view that sets actions, **When** its page renders, **Then** they are drawn
   with the Edit and Delete buttons.

---

### User Story 2 - A developer chooses the title layout for the whole site (Priority: P1)

A developer whose project is mostly overview pages finds the default title row too busy. They set
the centred layout in the package's settings, and every page in the project draws its title
centred. Later they want list pages to keep their usual layout, so they set the layout for list
pages alone. A project that sets nothing sees the same titles it saw before upgrading.

**Why this priority**: It is half of what was asked for, and the cheaper half for a developer: one
setting changes every page.

**Independent Test**: Render one page of each type with no layout setting, with one layout set for
all pages, and with a layout set for one page type. Confirm each page draws the layout the setting
gives it.

**Acceptance Scenarios**:

1. **Given** no layout setting, **When** any page renders, **Then** it draws the layout its page
   type has always drawn: the default layout on page, form, detail and delete pages, the inline
   layout on list pages and the compact layout on table pages.
2. **Given** one layout set for every page, **When** a page of any type renders, **Then** it draws
   that layout.
3. **Given** a layout set for one page type, **When** a page of that type renders, **Then** it
   draws that layout, and pages of other types draw theirs.
4. **Given** each shipped layout, **When** a page with every argument renders in it, **Then** every
   argument is drawn, the title is the page's one level-one heading, and the info trigger is
   outside it.
5. **Given** a table page set to any layout other than compact, **When** it renders, **Then** the
   title area is drawn above the toolbar and the toolbar keeps its controls and result summary.

---

### User Story 3 - A developer chooses a different title layout for one view (Priority: P1)

The same developer has one landing-style overview page that should be centred while the rest of
the site keeps the default. They set `page_title_layout` on that view. On a report view the layout
depends on whether the report has actions, so they override the method instead.

**Why this priority**: It is the other half of what was asked for. One site-wide choice rarely
suits every page.

**Independent Test**: With a site-wide layout set, render a view that names a different layout by
attribute and one that names it by method. Confirm each draws its own layout and other pages draw
the site-wide one.

**Acceptance Scenarios**:

1. **Given** a site-wide layout and a view that names another, **When** that view's page renders,
   **Then** it draws the view's layout.
2. **Given** a view that overrides the layout method, **When** its page renders, **Then** it draws
   the layout the method returns.
3. **Given** a view that names a layout that does not exist, **When** its page renders, **Then** an
   error names the value and the view, and no page is drawn.
4. **Given** a site-wide layout setting that names a layout that does not exist, **When** the
   project starts, **Then** an error names the value.

---

### User Story 4 - A developer replaces one part of a page's title in a template (Priority: P2)

A developer wants a detail page's lead to hold a link and a badge, which a view attribute cannot
express well. In the page's template they fill the lead block alone. The eyebrow, the title, the
actions and the info dialog still come from the view, drawn in the page's layout.

**Why this priority**: Templates are where a developer goes when the view's values are not enough,
and today the only way in is replacing the whole title area.

**Independent Test**: Render a template that fills each argument's block in turn on a view that
sets every argument. Confirm the filled block replaces only its own argument.

**Acceptance Scenarios**:

1. **Given** a template that fills one argument's block, **When** the page renders, **Then** that
   argument is drawn from the block and every other argument from the view.
2. **Given** a template that fills an argument's block with nothing, **When** the page renders,
   **Then** that argument is not drawn even though the view sets it.
3. **Given** a template that fills an argument's block, **When** the page renders in each shipped
   layout, **Then** the block's content is drawn where that layout draws the argument.
4. **Given** a template that overrides the whole title area block, **When** the page renders,
   **Then** its content replaces the title area, as it does today.
5. **Given** a template that extends none of the package's page templates and calls the page title
   component with arguments and a layout, **When** it renders, **Then** it draws the same title
   area a page view with those arguments and that layout draws.
6. **Given** a template that calls the page title component with `inline_actions`, **When** it
   renders, **Then** it draws the inline layout.
7. **Given** a template that fills the actions block on a list, table or detail page, **When** the
   page renders, **Then** only the block's content is drawn as the page's actions.

---

### User Story 5 - A developer adds a title layout of their own (Priority: P3)

A developer wants a title layout the package does not ship: the eyebrow and the actions on one
row, the heading and the lead below them. They write it as a template, name that template as the
layout in settings, and it receives the same arguments a shipped layout does, including what any
template block replaced.

**Why this priority**: It keeps the layout choice from becoming a dead end. It reuses everything the
first four stories build.

**Independent Test**: Name a project template as the layout, render a page that sets every argument
and fills one block, and confirm the template receives every argument with the block's content in
place of its view value.

**Acceptance Scenarios**:

1. **Given** a project template named as the layout, **When** a page renders, **Then** the
   template draws the title area with every argument the page sets.
2. **Given** that template and a page template that fills one argument's block, **When** the page
   renders, **Then** the project's template receives the block's content for that argument.
3. **Given** a project template named as the layout on one view, **When** that view's page renders,
   **Then** it draws the project's layout and other pages draw theirs.

### Edge Cases

- A page with an empty title draws no heading element; its other arguments are still drawn.
- A page whose info text is empty draws no info trigger in any layout, as today.
- A list or table page draws its actions in the toolbar whatever layout its title uses.
- A table page in any layout other than compact draws its title above the toolbar; the toolbar
  keeps its controls and its result summary.
- A template that calls the page title component directly, without a layout, draws the default
  layout, or the inline layout when it passes `inline_actions`.
- Right-to-left documents: every layout follows the document's direction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every page the package's templates draw, the page, form, detail, delete, list and
  table pages and the account overview, MUST draw its title area from one set of arguments: an
  eyebrow, a title, a lead, actions, info text and info actions.
- **FR-002**: Each argument MUST be settable on the view as a class attribute, `page_eyebrow`,
  `page_title`, `page_lead`, `page_actions`, `page_info` and `page_info_actions`, and through a
  method of its own that returns that attribute unless overridden.
- **FR-003**: The view MUST offer one method that gathers every argument, which a view MAY override
  to set the whole title area at once. The page templates MUST receive the arguments as one group,
  so an argument added later needs no change to any page template.
- **FR-004**: `page_subtitle` and its method MUST be renamed to `page_lead` and its method, with no
  deprecation period, in the view, the template context and the documentation.
- **FR-005**: Each argument MUST have its own template block, nested inside the block for the whole
  title area: `page.eyebrow`, `page.heading` for the title text, `page.lead`, `page.actions` and
  `page.info`. A block a template fills MUST replace the view's value for that argument alone,
  including when it is filled with nothing.
- **FR-006**: The `page.title` block MUST remain the block for the whole title area, so a template
  that overrides it today keeps working.
- **FR-007**: The package MUST ship at least four title layouts:
  - **default**: the title and lead in one column, with the actions beside them on a wide screen
    and below them on a narrow one;
  - **inline**: the actions on the heading's own row at every width, the lead across the full
    width below;
  - **centred**: every argument centred in one column, the actions under the lead;
  - **compact**: one row holding the title and the info trigger, with the lead shown only where
    there is room, as a table page draws it today.
- **FR-008**: Every layout MUST draw every argument the page gives it, and MUST NOT draw an empty
  element for an argument the page does not give.
- **FR-009**: The package's settings MUST accept a title layout for every page, or one for each page
  type. A page type with no setting MUST draw the layout it draws today: default on page, form,
  detail and delete pages, inline on list pages, compact on table pages.
- **FR-010**: A view MUST be able to name its own title layout as a class attribute,
  `page_title_layout`, and through a method that returns it unless overridden. A view's layout MUST
  win over the settings.
- **FR-011**: A layout MUST be nameable either as one of the shipped layouts or as a template of the
  project's own, which MUST receive the same arguments, with any block's content in place of its
  view value.
- **FR-012**: A layout name that is neither a shipped layout nor a template that can be found MUST
  raise an error naming the value: at startup when it comes from the settings, at render time,
  naming the view, when it comes from a view.
- **FR-013**: In every layout the title MUST be the page's one level-one heading, and the info
  trigger MUST sit beside the heading, never inside it.
- **FR-014**: Each action MUST be a button that accepts the same keys as the info dialog's actions.
- **FR-015**: On list and table pages the actions MUST be drawn in the toolbar beside Add, whatever
  the layout. On detail pages the view's actions MUST be drawn with the Edit and Delete buttons. A
  template that fills the `page.actions` block MUST replace all of them.
- **FR-016**: A table page MUST draw its title inside its toolbar in the compact layout, and above
  the toolbar in any other layout. The toolbar MUST keep its controls and its result summary in
  both cases.
- **FR-017**: A project that sets no new argument and no layout MUST see the same title area on
  every page as before this feature, apart from the rename in FR-004.
- **FR-018**: The page title component MUST accept the same arguments and a layout, so a template
  that does not extend the package's page templates can use it. Its `inline_actions` attribute MUST
  keep working, and its `subtitle` attribute MUST be renamed to `lead`.

### Key Entities

- **Page title**: The whole title area at the top of a page, drawn from its arguments in its
  layout.
- **Title**: The page title's heading text.
- **Eyebrow**: A short line above the title, such as a category or the kind of record.
- **Lead**: A sentence or two under the title saying what the page is for. Formerly the subtitle.
- **Page actions**: The buttons that belong to the page as a whole.
- **Title layout**: One arrangement of the page title's arguments, shipped by the package or written
  by the project, chosen in the settings or on the view.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer changes the title layout of every page in a project by editing one
  setting, and of one page by setting one view attribute, and writes no template to do either.
- **SC-002**: A developer replaces any one argument of a page title from a template without copying
  any of the others.
- **SC-003**: A project that sets nothing new renders the same title area on every page type as
  before the feature, apart from the rename.
- **SC-004**: Every page has exactly one level-one heading in every shipped layout.
- **SC-005**: Adding an argument to the page title later changes no page template.
