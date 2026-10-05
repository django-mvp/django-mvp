# Research: Every component this package keeps moves under the mvp. prefix

Investigated on 2026-10-05 against `main` at `bd63880`. The component directory matches the
specification's tables: 84 templates under `mvp/templates/cotton/`, 67 that move and 17 that stay.

## Planning notes, answered by name

### "Places a component name appears outside a tag"

**Adopted, and extended.** All five places were confirmed, and a sixth and seventh found.

| Where | What it holds | What changes |
|---|---|---|
| `mvp/config.py:92` | default navbar widget list, `["actions.theme-controller", "actions.login"]` | the two names take the prefix (FR-008) |
| `mvp/config.py:75` | a comment showing the short form | rewritten to the full name |
| `mvp/config.py:171,182` | the removed-setting warning names `templates/cotton/app/sidebar/footer.html` | the path becomes `templates/cotton/mvp/app/sidebar/footer.html` |
| `mvp/templatetags/mvp.py:505,535` | renders `cotton/documentation.html` by path | `cotton/mvp/documentation.html` |
| `mvp/fixtures.py` | docstring examples | examples use the new names (FR-011) |
| `mvp/templates/cotton/app/header/navbar.html:42,50` | `<c-component :is="widget" />` | nothing: the name is used as written (FR-009) |
| `mvp/templates/cotton/page/list/actions/index.html:14` | `<c-component is="page.list.actions.{{ action_item }}" />` | **found here, not in the notes.** The literal prefix becomes `mvp.page.list.actions.`. A view's `list_actions` entries (`"search"`, `"sort"`…) are short keys the component completes, not component names, so they do not change. |
| `tests/settings.py:37` | the test project's navbar widget list | the packaged names take the prefix |

Path strings handed to `render_to_string` or `get_template` in the tests
(`"cotton/form/render.html"`, `"cotton/page/list/actions/filter.html"`,
`"cotton/app/sidebar/index.html"`, `"cotton/documentation.html"`) move with their templates.
Comments in `mvp/tailwind/base.css` and `assets/js/layout.js` that name a template path are
updated so they still point at a file that exists. No selector, class or script hook changes.

`mvp/views/htmx.py` documents `htmx_success_component` with a project's own component as its
example (`"ui.product-created"`). It names no packaged component and is not changed.

### "Tests that read the component directory"

**Adopted.** `test_render_all.py` and `test_declared_attributes.py` both walk
`mvp/templates/cotton` with `rglob("*.html")` and build names from the relative path, so they
find every template at any depth and neither has a notion of a component called `mvp`. The only
edit either needs is the key of `test_render_all.py`'s `SKIP` entry, which becomes
`mvp/addons/django_table.html`. Both inventories must still count 84 after the move; the plan
makes that an explicit check.

### "How Cotton resolves a name"

**Adopted as stated.** Confirmed in the resolved package, django-cotton 2.6.1
(`site-packages/django_cotton/utils.py:40-52` and `templatetags/_component.py:142-143`): a
dotted name becomes a path, a hyphen in a segment becomes an underscore, and `<name>.html` is
tried before `<name>/index.html`. So
`<c-mvp.data-field>` reaches `cotton/mvp/data_field.html` and `<c-mvp.card>` reaches
`cotton/mvp/card/index.html`. There is no template at `cotton/mvp/index.html` and none is added,
so `<c-mvp>` alone is not a component.

### "Split directories"

**Adopted.** Three directories split: `avatar/` (`index.html` moves, `group.html` stays),
`menu/` (`item`, `group`, `collapse`, `divider` move, `index.html` stays), and the dock
(`app/dock.html` moves, `dock/` stays). A moved component that calls a staying one keeps the bare
tag.

### "Size of the change"

**Adopted, with current counts.** Mentions of a component name (tags and prose) per area: 444 in
`mvp/`, 764 in `demo/`, 432 in `tests/`, 262 in `docs/` outside the decision records, 108 in
`CONTEXT.md`, 12 each in `README.md` and `skills/`, 2 in `CONTRIBUTING.md`. That is too many to
edit by hand reliably, which decides the method below.

### "Sibling work in progress"

**Adopted.** The tables in the specification are not changed by this plan. The exception list the
guard test holds is the hand-over to #435, which shortens it as it removes each basic component.

## What had to be settled

### R1. The rename is done by one script, run once, and not committed

A mapping from old name to new name is a pure function of the name:

- split the name on `.`; look at the first segment
- `icon`, `alert`, `badge`, `breadcrumbs`, `button`, `divider`, `dock`, `link`, `mockup`: never
  prefixed
- `avatar`: prefixed unless the name is `avatar.group`
- `menu`: prefixed only for `menu.item`, `menu.group`, `menu.collapse`, `menu.divider`
- a first segment that is one of this package's other component directories or files
  (`actions`, `addons`, `app`, `backdrop`, `brand`, `card`, `container`, `data-field`,
  `documentation`, `dropdown`, `entrance`, `form`, `grid`, `group`, `layout`, `messages`,
  `modal`, `page`, `pagination`, `placeholder`, `rule`, `section`, `text`, `toolbar`, `user`):
  prefixed
- anything else (`vars`, `slot`, `component`, the demo's `components.*`, `demo.*` and
  `navbar.*`, a project example such as `myapp.*` or `billing.*`): untouched

The script applies it to opening and closing tags, to `c-…` names written in prose and comments,
and moves the 67 files with `git mv` so history follows them. Everything a regular expression
cannot be trusted with (names passed as Python strings, template paths, the `is="…"` literal) is
a short list found by search and edited by hand; the table above is that list for the package,
and the tests have 17 calls to the rendering fixtures to go through.

**Rejected: committing the script.** It is useful exactly once. The lasting protection is the
guard test (FR-016), not a tool nobody will run again.

**Rejected: a hand edit.** About 1,600 mentions across 300 files.

### R2. How "the same output as before" is shown

SC-003 compares two points in time, which a test in the suite cannot do. Two things carry it:

1. **The existing tests.** `tests/test_components/` and the view tests pin the markup of the
   components and the packaged pages. They are edited only where they name a component or a
   template path, and must pass. This is the lasting proof.
2. **A before-and-after capture while building.** Before the move, render every component
   template the way `test_render_all.py` does and fetch every demo URL the smoke tests fetch,
   and write the output to a scratch directory outside the repository. After the move, do it
   again and compare. Component output must be byte-identical. Page output must be identical
   except where a gallery page prints a component's own tag as text. The comparison is recorded
   in the build log as evidence and is not committed.

### R3. Old names must fail, and the test has to survive daisy-cotton arriving

US1 scenario 3 is conditioned on daisy-cotton not being installed. #433 installs it in the test
project, possibly before this merges. A test that renders `<c-card>` and expects an error would
start failing the day that lands. The test therefore uses moved names that daisy-cotton 0.1.2
does not ship (`page`, `toolbar`, `data-field`), which fail to resolve either way.

### R4. Names shared with daisy-cotton 0.1.2

Read from the published wheel (`daisy_cotton-0.1.2`, `daisy_cotton/templates/cotton/`): it ships
82 templates. All 17 of this package's bare names are among them (`alert`, `avatar/group`,
`badge`, `breadcrumbs/index`, `breadcrumbs/item`, `button`, `divider`, `dock/index`, `dock/item`,
`icon`, `link`, `menu/index`, `mockup/browser`, `mockup/code/index`, `mockup/code/line`,
`mockup/phone`, `mockup/window`), and it ships nothing under `mvp/`. So after the move the shared
set is exactly the exception list, which is FR-007.

The test for it compares the two template directories when `daisy_cotton` can be imported, and is
skipped (at class level, per the testing standard's project addition) when it cannot. Until #433
merges the comparison above is the evidence; after it, the test runs on every build.

### R5. Showing that an override follows its component

FR-010 needs a project template placed above the package's. The test project's fixture apps come
after `mvp` in `INSTALLED_APPS`, so they cannot override it. `tests/test_templates.py` already
builds its own template engine to control lookup order; the override tests do the same thing
with `override_settings(TEMPLATES=…)`, adding a directory under `tests/fixtures/` to `DIRS`,
which Django searches before any app. The fixture directory holds one template at a prefixed
path and one at an old path.

### R6. The stylesheet is not rebuilt

The prebuilt stylesheet is generated from the class names in the templates. No class name
changes, and Tailwind's source detection walks `mvp/` recursively, so the templates are still
found one directory deeper. The committed CSS is left as it is.

### R7. Records are not rewritten

`docs/adr/` (8 mentions of a component name), `docs/ROADMAP.md` (6), the released sections of
`CHANGELOG.md` and everything under `specs/` describe the package as it was when they were
written, or describe this very rename in terms of the old names. They are left alone. See D16.

### R8. The demo's gallery

`demo/component_docs.py` registers a documentation page per component by slug, and the gallery
templates show each component's tag as text through `{% cotton:verbatim %}` blocks. The script
rewrites those like any other tag, so each page shows the current name. URL slugs
(`components/card/`) identify gallery pages, not components, and stay as they are. The demo's own
components (`components.section`, `demo.*`, `navbar.test-widget`) keep their names.

### R9. Nothing a script selects on changes

`assets/js/` and the stylesheet select on classes, ids, `data-` attributes and Alpine store
names. None of them reads a component name or a template path except in comments.
