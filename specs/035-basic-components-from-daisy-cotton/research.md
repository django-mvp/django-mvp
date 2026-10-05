# Research: The basic components come from daisy-cotton

Read against `main` at `6b5f98f` on 2026-10-05, with daisy-cotton 0.1.3, django-cotton 2.6.1 and
daisyUI 5.7.0 as the lockfiles resolve them. Paths into daisy-cotton are relative to
`.venv/lib/python3.13/site-packages/daisy_cotton/templates/cotton/`.

## Planning notes, answered

**Dock class.** Adopted. daisy-cotton's dock declares `class` with no default
(`dock/index.html:7`), so `mvp/templates/menus/dock/index.html` passes
`mvp_config.layout.dock.class` itself. `mvp/renderers.py:34` already puts `mvp_config` in that
template's context for exactly this value.

**Dock toggle.** Not adopted. The note suggests the caller pass `role="button"` and
`tabindex="0"`, which daisy-cotton's dock item would forward (`dock/item.html:10-14`). A browser
probe on `main` showed what those attributes buy: the label takes focus, and neither Enter nor
Space flips the checkbox, because a `<label>` is not activated from the keyboard and nothing in
`assets/js/` handles the key. Making it work from this package would be a workaround for a gap in
daisy-cotton's component, so nothing is passed. The gap is raised as django-mvp/daisy-cotton#135
and carried as unmet (decision D14).

**Breadcrumb truncation.** Adopted. daisy-cotton's crumb puts the text straight inside `<a>` or
inside `<span aria-current="page">` (`breadcrumbs/item.html:8-12`). The rule at
`mvp/tailwind/base.css:700` moves from `.breadcrumbs li .mvp-breadcrumb-text` to
`.breadcrumbs li > :is(a, span)`. The trail's `text-sm` now comes from the caller in
`cotton/mvp/app/header/navbar.html:26`. Three browser tests in `test_app_header_e2e.py` decide
whether the rule still works, and they go red when the old template is removed.

**Breadcrumb attributes.** Adopted. `href` is a declared attribute of daisy-cotton's item, so it
cannot be written twice. `test_breadcrumbs_href_attribute.py` is rewritten: the span tests go
(the span is gone), and one test of the trail a page declares stays.

**Sidebar menu.** Adopted. `menus/sidebar/container.html` wraps the menu in
`<nav aria-label="{{ label }}">`, which carries `w-full grow`, and the menu inside it carries
`w-full`. The old `role="navigation"` on the list goes with the old template.

**Other menu callers.** Adopted. `actions/theme_controller.html:25` and
`addons/share_dropdown.html:19` pass `aria-label` in place of `label`. daisy-cotton's menu
forwards it to the list (`menu/index.html:8-9`). `user/sidebar_menu.html:20` passed no label and
had no accessible name, so it gains none. Each of the three passes `w-full`, which the old
template wrote for every menu.

**Button callers.** Partly wrong, and corrected here. `reverse` is not demo-only: it is passed in
`form_view.html:35`, `cotton/mvp/actions/login.html:16`, `cotton/mvp/page/list/actions/create.html:23`
and `.../filter.html:43`. `full` is passed in `actions/login.html:19`. `variant="ghost"` is in
`500.html:16` and `mvp/error_base.html:25`. No packaged template passes `condition` or `align`.
On the Python side, `page_info_actions` (`mvp/views/base.py:145`, `:309`) and the dropdown's
forwarded attributes (`cotton/mvp/dropdown/index.html:24`) hand dictionaries to the button, so
their documentation names daisy-cotton's attributes. `mvp.actions.login` keeps its own `full`
attribute, since it is a kept component, and passes `:block="full"` on.

**Divider direction.** Adopted. No packaged template passes `vertical`. The one packaged divider
(`cotton/mvp/form/formset/index.html:32`) is horizontal by default in both libraries. The demo's
divider page is where the swap lands.

**Alert under `only`.** Checked. `<c-alert variant="info" dismissible only>` renders the dismiss
control through daisy-cotton's button and the icon through this package's `cotton/icon.html`
(output carried the `bi bi-info-circle-fill` class from the easy-icons lookup).

**Mockups.** Adopted as the spec's assumption has it: the frames follow daisy-cotton. The demo
page is the only caller and passes any centring it wants through `class` or its own slot markup.

**Tests that glob the component directory.** Checked. `test_render_all.py` and
`test_declared_attributes.py` walk the directory and shrink by themselves. `PREFIX_EXCEPTIONS` in
`test_component_prefix.py` is the one hard-coded list, and it shortens to the icon.

**Classes the callers now write.** Partly adopted. The safelist entries for the divider and the
menu stay: daisy-cotton builds `md:divider-horizontal` and `lg:menu-horizontal` while a template
renders (`divider.html:14`, `menu/index.html:8`), so they are needed at least as much as before.
The stylesheet is rebuilt, and any class that drops out of it is removed from
`tests/fixtures/stylesheet_classes_0_26_0.txt` in the same commit and named in the pull request.

## What was verified by running it

With the sixteen templates set aside and nothing else changed:

- Each of the sixteen tags resolves to daisy-cotton's template.
- `:attrs="dictionary"` works together with `only`
  (`<c-alert :attrs="d" only>` with `{"variant": "warning"}` renders `alert-warning`).
- `:block="full"` with a false value writes no class.
- A variant outside the component's list renders with no variant class and no icon, and raises nothing
  (`<c-alert variant="primary">`, `<c-button variant="ghost">`).
- A former attribute name lands on the element as an HTML attribute
  (`<button class="btn" full reverse align="start" condition="x">`).
- The package's menu entries render inside daisy-cotton's menu, and its avatar inside
  daisy-cotton's avatar group.
- An icon placed in the button's slot after the text renders after the text.
- The full suite: 28 tests fail, all in the package's own tests and none in the demo's. They are
  the list in the plan under *Tests that change*.

## Which attributes can leak

Cotton fills an attribute the caller did not pass from the surrounding context only when the
component declares it with no default. Among the sixteen that is:

| Component | Declared with no default |
|---|---|
| breadcrumbs | `items`, `class`, `aria-label` |
| breadcrumbs.item | `text`, `class`, `href` |
| divider | `class` |
| dock | `size`, `class`, `aria-label` |
| dock.item | `icon`, `label`, `class` |
| link | `text`, `variant`, `hover`, `class` |
| menu | `size`, `horizontal`, `paged`, `class` |
| mockup.* | `class` (and `url` has a default) |

Alert, badge, button and avatar.group give every attribute a default, so they cannot leak today.
They still get `only`, because the rule is about the call and a later daisy-cotton release may
change a default.

The same leak exists for this package's own components, many of which declare attributes with no
default. That is outside FR-017, which covers calls to daisy-cotton's components (decision D15).

## Finding the calls for the check

`<c-…>` tags are recognised by django-cotton's own compiler, which this package's fixtures
already use (`mvp/fixtures.py`). The check compiles each packaged template with it and reads the
component name and the `only` flag from the compiled `{% cotton … %}` tags, so a tag that spans
lines, or holds `>` inside an attribute value, is read the way Cotton reads it. Text inside
`{# … #}` and `{% comment %}` never reaches the compiler's output as a tag, so the examples in
annotations are not counted. A name is daisy-cotton's when daisy-cotton ships a template for it
and this package does not, which keeps the icon out and takes in every component the later
features start calling.

## Unknowns that remain

None that block the plan.
