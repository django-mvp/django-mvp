# Planning notes: FS-042

Suggestions from the intake discussion and the prototype review (2026-10-20 and 2026-10-21), for
the build to answer one by one. They are inputs, not instructions, except where Sam stated a rule.

**Sam's rule: any Alpine component with real behaviour lives in its own module, not in a template's
`x-data` attribute.** The panel's open, close, focus and Escape handling becomes a registered
component in `assets/js/` (for example `Alpine.data("mvpPageSide", ...)`), and the panel button a
small registered component of its own. The template passes configuration only:
`x-data="mvpPageSide({...})"`. This is how `layout.js` and `dropdown.js` already sit outside the
templates. It applies to the package from here on, not to this feature alone.

The prototype on branch `sketch/page-side` is the starting point. Sam approved its look over four
rounds; `sketch.md` lists what it settled and what it faked.

The panel keeps daisyUI's drawer inside itself rather than making every page a drawer. Sam does not
accept "nested drawers conflict with the shell" as a reason for anything: the shell's selectors
that reach nested drawers (`is-drawer-open`/`is-drawer-close` and the `.mvp-page-fill` rules in
`mvp/tailwind/base.css`) are a defect of their own, filed separately. If that defect gets in this
feature's way, fix it rather than design around it.

`breakpoint=False`, not `"never"`, for a panel that is never a column. Sam: it makes the template
logic read better (`{% if breakpoint %}`).

A list page's panel fields join the toolbar's filter form through the HTML `form` attribute
(`form="filterForm"`) on each field's widget and on the panel's apply button, set by the view rather
than the templates so it reaches widgets the developer chose, such as Tom Select. One form wrapping
the whole layout would contain the create dialog's own form, and nested forms are not valid HTML.
`list_view.js` reads `form.elements`, which includes form-associated controls, so its auto-submit
keeps working. This departs from FS-041's note that every field sits inside the form with no `form=`
attribute; that note predates a panel outside the toolbar.

The prototype found daisyUI's `drawer-end` sets `justify-items: end` on `.drawer-side`, which
shrinks the panel to its content in a column. Keep the column override that stretches it.

The prototype's focus move into the drawer has to wait until daisyUI's transition makes the panel
visible; a hidden element cannot take focus. Use `inert` on the rest of the page for containment
rather than a hand-written focus trap.

The prototype placed the panel before or after the content by searching the rendered side slot for
`data-mvp-side-position="start"`. Find a cleaner seam.
