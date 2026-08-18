# Decisions — 027 Full-screen tables and column styling helpers

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without asking the
maintainer. Each entry states what was unclear, what was chosen, and why the choice is defensible.

## D1 — The scrolling table area is a labelled, keyboard-focusable region

**Unclear**: `spec.md` asked for a scroll container and said nothing about reaching it without a
mouse or announcing it to assistive technology.

**Chosen**: the table area is a tab stop with an accessible name and a region role. Recorded as
FR-025.

**Why**: a `div` with `overflow: auto` scrolls with the mouse wheel in every browser, but only
Chromium makes it keyboard-scrollable without an explicit tab stop. In Firefox and Safari a
keyboard-only reader can reach the rows only by tabbing to a focusable element inside them, which
a read-only table does not have. Article XIII requires components to be keyboard-navigable and to
carry ARIA attributes where markup alone does not convey the role, and a scrollable region is
exactly that case. The alternative — leaving it as an unfocusable div — makes the whole feature
unusable without a pointing device on two of three engines, which is not a defensible default for
a package whose tables are the main surface of an application.

**ADR:** docs/adr/0013-a-scrollable-region-is-focusable-and-named.md — graduated. The rule is about scrollable regions, not tables, and binds every one the package ships from here on.


## D2 — Maximum column width comes from named classes, never an author-supplied value

**Unclear**: FR-012 asked for a way to cap a column's width without saying whether the author
states the number.

**Chosen**: a fixed set of named width classes. No runtime value reaches the markup.

**Why**: three independent reasons point the same way.

- Article V forbids hand-built string interpolation of author or model data into rendered output.
  A width value placed in a `style` attribute is exactly that, and the value's origin (a table
  class the project controls) does not change the shape of the mechanism.
- Article XI makes component attributes the supported surface and forbids raw utility classes in
  templates that demonstrate a component. An arbitrary width is a raw utility by another name.
- The stylesheet is built by scanning templates for class names, so a class assembled from a value
  known only at runtime is never emitted unless it is separately safelisted. A named set is the
  only version of this that survives the build.

The existing component's `min_height` attribute is the same pattern, interpolated into an inline
`style`. It is removed rather than reproduced.

**ADR:** docs/adr/0014-sizing-comes-from-named-classes-not-runtime-values.md — graduated. It constrains how any component accepts a dimension, and the build-scan reason is not something a reader would reconstruct.


## D3 — The component becomes the table area; the page template owns the bars

**Unclear**: whether the layout belongs entirely to `table_view.html`, or whether the reusable
component changes too.

**Chosen**: both, split by what each is for. The component is the scroll container with its fixed
heading and footer rows. The page template is the action bar, the component, and the pagination
bar, inside a filled page. Recorded as FR-026.

**Why**: a project embedding the component directly in a page of its own wants the scrolling and
the fixed heading — that behaviour is intrinsic to displaying a table and should not be something
you get only by using the packaged view. The bars are not: they carry a page title, a view's
actions and a view's pagination, none of which the component has any access to. Putting the bars
in the component would mean passing all three in as attributes, which is the wider attribute
surface Article XI tells us to refuse in favour of a template.

The consequence for `min_height` follows from the split rather than being a separate decision. A
container that derives its height from its parent cannot also hold a fixed viewport-relative
floor; the two sizing rules contradict each other, and the floor is the one that existed only to
work around the absence of the parent height.

**ADR:** none — local to this feature. Where the seam between one component and one page template falls binds nothing downstream, and the template comment carries the reasoning for whoever edits it next.


## D4 — A wide table on a small screen scrolls sideways

**Unclear**: FR-011 required the layout to hold at phone widths without saying what a table too
wide for a phone does.

**Chosen**: horizontal scrolling within the table area, at every width. No card fallback, no
column hiding, no responsive transform.

**Why**: Article II asks for the simplest design that satisfies the spec, and the spec asks for a
table that fills the shell and owns its scrolling — which it does at 390px exactly as it does at
1440px. A responsive card transform is a different feature with its own questions (which columns
survive, what the card looks like, how sorting works when there are no headings), and the package
already answers "show this data as cards on a phone" with the list view. Shipping a half-considered
transform inside this feature would be the wrong abstraction Article III warns about.

**ADR:** none — a scope boundary, not an architectural decision. It records what this feature declined to build; a future responsive-table feature answers the question on its own terms rather than inheriting this.


## D5 — Declaring an ordering on a table view is an error, not a no-op

**Unclear**: the intake said the view class should not allow ordering to be declared. Silently
dropping the declaration and failing loudly are both ways to "not allow" it.

**Chosen**: fail, with a message naming the table as where ordering belongs. Recorded as FR-009
and SC-004.

**Why**: the failure mode of silently ignoring it is a developer who declares an ordering, sees
rows in a different order, and has no way to discover why — the declaration sits in their view
class looking correct. That is the same shape as a setting that is read, stored and never
consulted, which is a recurring source of lost time in Django projects. An error at the point of
declaration costs one clear message and cannot be misread.

**ADR:** none — one class's behaviour, not yet a package stance. The general form (a mixin refuses configuration it cannot honour rather than ignoring it) would be worth an ADR, but one instance does not establish it. Graduate when a second mixin needs the same rule.


## D6 — Alignment inference reads the model field, not the column class

**Unclear**: whether a column's kind can be determined at all, which the intake explicitly flagged
as uncertain.

**Chosen**: it can, from the model field behind the column. Where there is no model field, no
alignment is imposed.

**Why**: django-tables2 3.0.0 registers thirteen column classes and picks one per model field
through `column_for_field`, but none of them is numeric — `IntegerField`, `DecimalField` and
`FloatField` all fall through to the base `Column`. So the column class alone cannot tell a number
from a string, which is the single distinction the feature most needs. The model field can, and it
is reachable at render time. Falling back to no alignment where no model field exists keeps
FR-021's promise that a table the template cannot read renders exactly as it does today.

Registering the package's own column classes so they win the dispatch was considered and rejected
at intake: it would make correct alignment depend on the author importing something, which is the
opposite of the requirement.

**ADR:** none — an implementation route forced by the library, not a choice this package gets to make. The rejected alternative is recorded above and the tag's docstring carries the reason.

## D7 — A filled page is bounded, not merely at least as tall as the viewport

**Unclear**: nothing was unclear at planning time. This decision was forced during implementation,
when the browser evidence for US-1 came back red.

**Chosen**: the filled-page rule shipped with #247 states a `height` ceiling as well as its
`min-height` floor, and the two rungs between the shell and the page content release their
automatic minimum height so the bound propagates. Filled pages clip and hand scrolling to their
content.

**Why**: a floor only guarantees the page is *at least* viewport-tall. The mechanism's first
consumer with overflowing content pushed the shell past it, and the window scrolled — the one
behaviour a filled page exists to prevent. The map the mechanism was built for is never taller than
it is told to be, so floor and ceiling agreed and the gap never showed.

**ADR:** docs/adr/0015-a-filled-page-is-bounded-not-merely-at-least-as-tall.md — graduated. It
changes a shared mechanism's behaviour for every filled page in every consuming project.

## D8 — A view's context key must not collide with a component slot name

**Unclear**: nothing, until the rendered page showed `['search', 'filter', 'create']` beside the
breadcrumbs.

**Chosen**: the table view's context key is `table_actions`, and the breadcrumb row is a plain flex
row rather than a `<c-toolbar>`.

**Why**: a Cotton slot falls through to the context variable of the same name when the caller fills
no slot. `<c-toolbar>` renders `{{ actions }}` in its trailing slot, so a context key called
`actions` printed its own repr into every toolbar on the page that did not fill that slot. Renaming
the key fixes this view; the bare row keeps it fixed whatever a project later puts in its own
context.

**ADR:** none — this is a library behaviour to document and guard, not a decision to record. The
general case reaches every component slot name (`actions`, `slot`, `above`, `below`) and every view
that adds context, so it belongs in the component documentation and a tracker issue rather than in
an architecture record. Only this view is closed today; the wider sweep is filed separately.
