# Planning notes: Every component this package keeps moves under the mvp. prefix

Things found while specifying that bear on how this is built. None of them changes what the
specification asks for. The plan answers each one by name.

## Places a component name appears outside a tag

A search for tags will not find these.

- `mvp/config.py` holds the default navbar widget lists as component names, and a comment beside
  them shows the short form.
- `mvp/config.py` also warns about a removed sidebar footer setting, and the warning tells the
  project which template path to override. That path moves.
- `mvp/templatetags/mvp.py` renders the documentation block by template path.
- `mvp/fixtures.py` uses component names in its docstring examples.
- The navbar renders its widgets with `<c-component :is="…">`, so the names reach Cotton as
  strings.

## Tests that read the component directory

`tests/test_components/test_render_all.py` and `tests/test_components/test_declared_attributes.py`
walk `mvp/templates/cotton`. Check that both still cover every component once most of them sit
one directory deeper, and that neither treats `mvp` as a component of its own.

## How Cotton resolves a name

`<c-a.b>` resolves to `cotton/a/b.html`, then `cotton/a/b/index.html`, in the first installed app
that has it. A template cannot call the component it shadows, because the name resolves back to
itself. After this feature the icon is the only component whose behaviour depends on this package
sitting above daisy-cotton in `INSTALLED_APPS`.

## Split directories

`cotton/avatar/group.html`, `cotton/menu/index.html` and `cotton/dock/` stay where they are while
their neighbours move. #435 removes them.

## Size of the change

Roughly 390 component tags in the package's templates, 750 in the demo, 155 in the documentation,
400 in the tests, and a dozen each in the README and the assistant skill. Not all of them are for
components that move.

## Sibling work in progress

#433 and #435 to #440 are being specified alongside this one. #435 and #436 are written against
the names this feature introduces, so a change to the tables in the specification has to be
carried to them.
