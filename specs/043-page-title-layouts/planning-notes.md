# Planning notes: Page titles share one set of arguments and a choice of layouts

Notes from Sam for whoever plans and builds this feature, in his words where he gave them. The
build answers each note by name.

**Follow daisy-cotton-ext's heroes.** "All page titles should accept the same few arguments. These
arguments should reflect the same (or similar) arguments to those in the hero sections of
daisy-cotton-ext. E.g. eyebrow, title, lead, actions, etc." The heroes are
`daisy_cotton_ext/templates/cotton/hero/centred.html`, `split.html` and `showcase.html`, and their
shared contract is the "Heroes" section of daisy-cotton-ext's README. daisy-cotton-ext is a
development dependency of django-mvp only, so the layouts are built on daisy-cotton.

**Every part has a block as well as a view attribute.** "Each 'slot' must be overridable via
template blocks as well as setting view attrs."

**One attribute per part, or one dictionary?** "Can we review the way page attrs are declared?
Should we stick with single attrs for each part or should we pass a single page_title = {} dict and
pass the whole dict into the template/component? This provides less mechanical parts from our
perspective but probably less customizability for view subclasses." Settled at intake: one
attribute and one `get_*()` method per part on the view, one method that gathers them, and the
page templates hand the gathered group to the layout in one go. The four page templates currently
pass each argument to `c-mvp.page.title` one at a time; that is the mechanical cost to remove. The
group needs a context key of its own, because `page.title` is already the plain title text used by
the browser title, the share menu and the form heading.

**No deprecations.** "No need for deprecations for the time being." `page_subtitle` is renamed to
`page_lead` outright.
