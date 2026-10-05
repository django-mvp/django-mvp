# Planning notes: Install daisy-cotton alongside the package, with no visible change

Notes from the maintainer on how this might be built. They are not requirements. The plan answers
each one by name.

The prebuilt stylesheet already scans all of daisyUI's components and utilities, so daisyUI's own
classes are present whatever daisy-cotton builds at render time. What still needs care is the
plain Tailwind utilities daisy-cotton's templates write literally, such as `min-w-52` and `end-2`.
Scan `daisy_cotton/templates` for those.

Breakpoint-prefixed forms such as `md:menu-horizontal` are not produced by scanning daisyUI.
Safelist them in `mvp/tailwind/base.css`, as the package already does for its own components.

The entry file generator already resolves the form pack's install path for the environment it
runs in. Resolve daisy-cotton's the same way.

Pass Cotton's `only` attribute on every call this package makes to a daisy-cotton component. Do
not look for an upstream fix for page variables reaching a component.

This package pins `django-cotton==2.6.1`, and daisy-cotton's own development environment runs
2.7.2. Check that daisy-cotton's components render under the pinned version.

The required order is the project's own apps, then `mvp`, then `daisy_cotton`, then
`crispy_forms` and `mvp_forms`. A start-up check should warn when `mvp` is below `daisy_cotton`.

The `Stylesheet` workflow installs no Python, so a source path into the Python environment finds
nothing there. Do not edit anything under `.github/`. If the workflow turns out to need a change,
open an issue for it.
