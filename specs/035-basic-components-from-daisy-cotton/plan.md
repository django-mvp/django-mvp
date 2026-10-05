# Implementation Plan: The basic components come from daisy-cotton

**Branch**: `035-basic-components-from-daisy-cotton` · **Spec**: [spec.md](spec.md) ·
**Research**: [research.md](research.md) · **Decisions**: [decisions.md](decisions.md)

## Summary

Sixteen component templates are deleted from `mvp/templates/cotton/`. Their bare tags then reach
daisy-cotton's templates, which are already installed and already covered by the prebuilt
stylesheet (FS-033). Every caller in the package, the demo and the documentation moves to
daisy-cotton's attribute names. Every call a packaged template makes to a daisy-cotton component
gets Cotton's `only`, and a test fails when one is added without it. The change is breaking and
is recorded under the changelog's unreleased heading. No release is cut.

No new dependency, no model, no migration, no setting and no new Python module in the package.

## Technical context

- Python 3.12+, Django 5.2+, uv. django-cotton 2.6.1, daisy-cotton 0.1.3 as locked
  (`>=0.1.2,<0.2` as declared), daisyUI 5.7.0.
- Tests: pytest, BeautifulSoup for markup, Playwright for the few behaviours only a browser shows.
- Stylesheet: rebuilt with `uv run invoke build-stylesheet` and committed (Article XV).

## Constitution check

| Article | How the plan meets it |
|---|---|
| I, Testing | Each behaviour gets its test first. Wording and appearance get none. |
| II and III, Simplicity | Nothing is added in place of what is removed: no wrapper, no alias, no helper tag. |
| VI and XVII, Documentation | Each story updates the pages its own change makes untrue. |
| VII, Dependencies | None added. |
| VIII, Internationalization | Accessible names passed by callers stay translated strings. |
| XI, Components | The sixteen leave the package's API. The kept components keep theirs. |
| XII, Configuration | The dock still reads `MVP_CONFIG["layout"]["dock"]["class"]`. |
| XIII, Rendered markup | Tests of markup daisy-cotton owns go. Tests of what this package's call sites promise are rewritten. |
| XIV, Browser tests | Kept to the breadcrumb truncation tests that exist and one new test of the dock toggle's keys. |
| XV, Build artifacts | The stylesheet is rebuilt and committed in the story that changes the classes. |
| XVI, Compatibility | Breaking, pre-1.0, recorded in the changelog with the full table. |
| XVIII, Attribute dictionaries | `related_objects_attrs` and `page_info_actions` keep forwarding. Their documentation names the new attributes. |

No violation to justify.

## Design

### 1. What is deleted

`alert.html`, `avatar/group.html`, `badge.html`, `breadcrumbs/index.html`, `breadcrumbs/item.html`,
`button.html`, `divider.html`, `dock/index.html`, `dock/item.html`, `link.html`, `menu/index.html`,
`mockup/browser.html`, `mockup/code/index.html`, `mockup/code/line.html`, `mockup/phone.html`,
`mockup/window.html`, all under `mvp/templates/cotton/`. The now-empty directories go with them.
`cotton/icon.html` and everything under `cotton/mvp/` stay.

The `variation` and `responsive` template tags in `mvp/templatetags/mvp.py` stay: kept components
use them.

### 2. The packaged callers

Every call below also gets `only` (section 4). Nothing else about a call changes unless listed.

| Template | Change |
|---|---|
| `500.html`, `mvp/error_base.html` | `variant="ghost"` becomes `ghost` |
| `form_view.html` | `reverse` goes; the arrow icon moves into the button's slot after the text |
| `cotton/mvp/actions/login.html` | `reverse` goes, icon into the slot; `:full="full"` becomes `:block="full"`; an empty `variant` passes through unchanged. The component's own `full` attribute stays |
| `cotton/mvp/page/list/actions/create.html`, `filter.html` | `reverse` goes, icon into the slot |
| `cotton/mvp/app/header/navbar.html` | the trail gains `text-sm` in `class` |
| `menus/dock/index.html` | passes `:class="mvp_config.layout.dock.class"` |
| `menus/dock/item.html` | when the item toggles a drawer, passes `role="button"`, `tabindex="0"` and the two key handlers of section 3 |
| `menus/sidebar/container.html` | `<nav aria-label="{{ label }}" class="w-full grow">` around `<c-menu class="w-full" only>`; `label` and `grow` go |
| `cotton/mvp/actions/theme_controller.html`, `cotton/mvp/addons/share_dropdown.html` | `label="…"` becomes `aria-label="…"`; `w-full` added to `class` |
| `cotton/mvp/user/sidebar_menu.html` | `w-full` added to `class` |
| `cotton/mvp/messages.html` | unchanged attributes. The debug-to-info mapping stays. A level tag outside daisy-cotton's four draws a plain alert |
| every other caller of `c-button`, `c-alert`, `c-badge`, `c-divider`, `c-link` | attributes unchanged |

An icon moved into a button's slot is written `<c-icon name="…" />`, this package's own icon, so
it is not a daisy-cotton call and takes no `only`.

A class a caller already passes that daisy-cotton also has an attribute for (`btn-square`,
`btn-circle`) stays a class: it renders the same and is not a former attribute.

Comments and annotations that name a removed attribute are corrected where they sit
(`cotton/mvp/rule.html`, `cotton/mvp/section/index.html`, `cotton/mvp/modal.html`, the docstrings
in `mvp/renderers.py`, `mvp/views/base.py`, `mvp/views/edit.py`, `mvp/fixtures.py`).

### 3. The dock toggle answers the keyboard

`menus/dock/item.html` passes, on the toggle item only:

```html
role="button" tabindex="0"
x-on:keydown.enter.prevent="$el.click()"
x-on:keydown.space.prevent="$el.click()"
```

Alpine is already on every shell page: the drawer checkbox the label points at is bound to an
Alpine store. A click on a label flips its checkbox, so the handler needs no knowledge of the
drawer. If Cotton does not carry the dotted attribute name through, the fallback is a single
`x-on:keydown` whose expression tests `$event.key`. One browser test presses each key and reads
the checkbox (decision D14).

### 4. `only`, and the check for it

Every `<c-…>` call in a packaged template whose name is daisy-cotton's carries `only`. This
covers templates under `mvp/templates/` whether or not they are component templates
(`menus/*`, `delete_view.html`, `mvp/account/*` and the rest).

The check is one test module, `tests/test_components/test_daisy_cotton_calls.py`. It walks
`mvp/templates/**/*.html`, compiles each file with django-cotton's compiler, and reads every
compiled `{% cotton <name> … %}` tag. A name is daisy-cotton's when daisy-cotton ships
`cotton/<name as a path>.html` (or `…/index.html`) and this package ships neither. A call to such
a name without `only` fails the test with the template's path and the tag's name. The check
holds no list of component names, so the components the later features start calling are covered
the day they are called.

A second test in the same module proves the check can fail: it runs the same scan over a
directory holding one template with an unisolated call and asserts the offender is reported by
template and tag.

### 5. Breadcrumb truncation

`mvp/tailwind/base.css`: the selector `.breadcrumbs li .mvp-breadcrumb-text` becomes
`.breadcrumbs li > :is(a, span)`, with the comment above it rewritten for the new markup. The
declarations are unchanged. The three browser tests that exist decide it.

### 6. The stylesheet

Rebuilt once, in the story that changes the templates and `base.css`, with
`uv run invoke build-stylesheet`. If a class in `tests/fixtures/stylesheet_classes_0_26_0.txt` is
no longer in the built file because nothing writes it any more, that line is deleted in the same
commit and the class is named in the pull request. The safelist in `mvp/tailwind/base.css` and
`tests/fixtures/preset_safelist_0_26_0.txt` are not shortened (research, *Classes the callers now
write*). `.github/` is not touched.

### 7. Tests that change

These fail when the templates are removed. Each is rewritten against what the package still
promises, or removed where it only asserted the removed template's markup (FR-023, decision D12).

| Test | What happens to it |
|---|---|
| `test_button.py::TestButtonCondition` | removed. `condition` is gone. The module goes if nothing else is in it |
| `test_link.py::TestLinkDefaults::test_default_href_falls_back_to_hash` and the rest of `test_link.py` | removed: the link's markup is daisy-cotton's |
| `test_mockup_code.py` | removed, same reason |
| `test_breadcrumbs_href_attribute.py::TestTheItemTextSpan` | removed. The module keeps one class: the trail a page declares renders one crumb per entry in order, a link where the entry has an address, the current page where it has none, extra attributes on the list item, `href` once |
| `test_menu.py::TestSidebarContainerTakesItsNameFromContext`, `TestTheSidebarDrawsOneNavigationLandmark` | rewritten: the name is on the `nav` around the menu, and there is one navigation landmark with that name |
| `test_app_sidebar.py::…one_navigation_landmark_beside_a_back_link`, `test_shell_renders_without_request.py::…still_draws_the_sidebar_menu` | rewritten to find the `nav` by its accessible name |
| `test_layout_config.py::…the_dock_renders_the_configured_class` | rewritten for the `nav.dock` element |
| `test_sidebar_footer.py::…log_in_button_fills_the_row…` | rewritten: reads `btn-block` and the variant from the button as rendered |
| `test_dropdown.py::…extra_attributes_configure_the_default_inner_button` | rewritten to parse the button and read its variant class and forwarded attributes, in place of matching a whole class string |
| `test_renderers.py::TestMobileDock*` | the locator `div.dock` becomes `nav.dock`. Assertions unchanged |
| `test_app_header_e2e.py` (three tests) | no edit expected. They go green when the selector in `base.css` follows the markup and the stylesheet is rebuilt |
| `test_component_prefix.py` | `PREFIX_EXCEPTIONS` becomes the icon alone |

`test_class_attribute_merge.py`, `test_responsive_safelist.py`, `test_form_field.py` and
`test_views/test_edit.py` mention the sixteen tags and pass today with the templates removed.
Each is read once: a case that asserts a removed template's own markup goes, anything else stays
as it is.

### 8. New tests

All under `tests/`, mirroring what they test, in `Test<Subject>` classes.

- **`test_components/test_basic_components.py`** (US-1). For each of the sixteen tags: the
  template the tag resolves to is inside the daisy-cotton package, and this package ships no file
  at that path. A dashed button takes effect. `full` on a button has no effect on the component
  and raises nothing. The package's menu entry renders inside daisy-cotton's menu, and its avatar
  inside daisy-cotton's avatar group. A project template at `cotton/badge.html`, in a directory
  listed in `TEMPLATES["DIRS"]`, is the one rendered.
- **`test_templates.py` or the page's own module** (US-2). One Django message at each built-in
  level draws one alert each with the message in it, debug with the info variant, and a level tag
  outside the four draws its message and raises nothing. The delete page forwards
  `related_objects_attrs`. The dock is a navigation landmark with a name, its toggle carries
  `role="button"`, `tabindex="0"` and a name, and the current page's item carries
  `aria-current="page"`. The dock takes the configured class and the default when the setting is
  absent. The theme chooser and the share menu each have an accessible name. No element on the
  shell, list, detail, delete, sign-in, sign-out and error pages carries one of the former
  attribute names as an HTML attribute.
- **`test_renderers.py`** (US-2, browser). Enter and Space on the focused dock toggle each flip
  the drawer checkbox.
- **`test_components/test_daisy_cotton_calls.py`** (US-3). The check of section 4.
- **`test_components/test_daisy_cotton_isolation.py`**, extended (US-3). A packaged page rendered
  with context variables named after every attribute in research's leak table draws each
  daisy-cotton element (alert, button, badge, breadcrumbs and crumbs, divider, dock and items,
  link, menu) with the same tag, attributes and classes as without them. Content the package
  puts inside an alert reads a page variable. A dismissible alert called with `only` still draws
  its dismiss button and its icon, and the icon comes from this package's lookup.
- **`test_demo/`** (US-4). Every demo page for these components answers 200. No demo template
  passes a former attribute name to one of the sixteen tags: the scan reuses the compiler-based
  reader of section 4 with a table of tag and former attribute.

What gets no test: the look of any component, the changelog's wording, the documentation's
wording, the classes a demo page passes.

### 9. Demo, documentation, changelog (US-4)

- **Demo**: `demo/templates/**` moves to the new attributes, per the table in FR-006. The avatar
  page passes `class="-space-x-6"` to the group, the one raw class allowed (D10). The button page
  shows the former `reverse` with the icon in the slot. The divider page swaps `vertical` for
  `horizontal` and `label` for `text`. Mockup lines that showed a prompt pass `prefix="$"`.
  `demo/component_docs.py` descriptions that say the package provides these components are
  corrected. Demo pages do not take `only` (D8).
- **Documentation**: `docs/components.md` gets a section saying the sixteen come from
  daisy-cotton, with a link to daisy-cotton's documentation for each, a short explanation of
  `only` and when a project needs it, and what an existing override of one of these tags now
  affects. Every example and attribute table for the sixteen moves or goes. `docs/icons.md`,
  `docs/styling.md`, `docs/account-center.md`, `docs/layout.md`, `docs/views.md` (the delete
  page's alert variants), `README.md`, `CONTEXT.md` and `skills/django-mvp/SKILL.md` are searched
  for the former names and for claims that the package ships these components.
- **Changelog**: one entry under `## [Unreleased]`, `### Changed`, marked breaking, naming all
  sixteen tags, carrying every row of FR-006's table with its replacement, and calling out the
  divider's swap on its own line.

## Story order

**US-1 and US-2 together, then US-3, then US-4. One worktree, one at a time.**

- US-1 and US-2 cannot land apart (spec). They are built in one pass: the tests of sections 7 and
  8 first, then the deletion and the callers of section 2 without `only`, then `base.css` and the
  stylesheet.
- US-3 follows: the check and the leak test are written first and are red against the calls as
  US-2 left them, then `only` goes on every call. Doing it as its own pass is what lets the check
  be seen failing for the right reason before it passes.
- US-4 last: demo, documentation, changelog.

A documentation page that US-1 and US-2 make untrue about the package's own Python surface
(the docstrings in `mvp/views/`) is corrected in that story. The component reference and the
upgrade notes are US-4's own deliverable (spec, US-4), so they are written there.

## Project structure

```text
mvp/templates/cotton/            sixteen templates removed
mvp/templates/**                 callers moved, then isolated
mvp/tailwind/base.css            one selector
mvp/static/…                     prebuilt stylesheet, rebuilt
mvp/views/base.py, edit.py       docstrings
mvp/renderers.py, fixtures.py    docstrings
demo/templates/**, demo/component_docs.py
docs/*.md, README.md, CONTEXT.md, skills/django-mvp/SKILL.md, CHANGELOG.md
tests/test_components/…          as sections 7 and 8
tests/fixtures/stylesheet_classes_0_26_0.txt   only if a class drops out
```

## Risks

- **A former attribute fails quietly.** The stray-attribute test of section 8 and the demo scan
  are the guard inside the repository. The changelog table is the guard outside it.
- **The two-pass order leaves the calls unisolated between US-2 and US-3.** Both land in one pull
  request, so no release or merge sees that state.
- **The stylesheet build is not byte-reproducible.** The rebuilt file is committed once, and the
  class fixtures are what the tests compare.
