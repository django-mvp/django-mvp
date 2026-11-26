# ADR 0031 — daisy-cotton is a runtime dependency

**Status:** accepted

## Decision

`daisy-cotton` is declared in `[project].dependencies` with the range `>=0.3,<0.4`. A project
adds `daisy_cotton` to its own `INSTALLED_APPS`, directly below `mvp`. The package never edits a
project's settings.

Installing it changed nothing on any page by itself. At the time both packages shipped Cotton
components under the same names, Cotton takes the first app that has one, and `mvp` is listed
first. Since then this package has stopped shipping its own basic components (the button, the
alert and the like), so those tags now reach daisy-cotton's. The icon is the one name both
packages still ship.

`django-cotton` is pinned to one release, `2.9.0`.

## Why

This package is moving its basic components, such as badges, tabs and tooltips, into a separate
package, daisy-cotton, over several releases. It has to depend on daisy-cotton before it can stop
shipping its own copies, so the dependency lands first, on its own, where it can be checked against
the two installed packages.

The justification Article VII asks for is that the package will draw its own pages with those
components. They are part of how it renders, not an optional integration, so there is nothing to
guard an import behind and no fallback to degrade to.

daisy-cotton is not yet at 1.0, and it says its component names, attributes and emitted classes can
change between minor versions. The floor is the release this package was last tested against:
`0.3` requires django-cotton 2.9 and puts a caller's classes straight after a component's base
class. The upper bound stops a new minor version arriving unannounced. Moving it is a decision
made when that release is tested with this package.

django-cotton is pinned to one release rather than a range because this package depends on more
than its documented tags. `mvp/templatetags/mvp.py` and the test fixtures in `mvp/fixtures.py`
compile templates with django-cotton's own compiler class, which is not a public interface, and
the packaged templates have had to change for point releases before: 2.7 changed how `<c-vars>`
defaults are compiled, 2.8 renamed the context isolation setting, and 2.9 added the portal the
formset component loads its script through. Each new release is tested with this package before
the pin moves, which is what Dependabot's pull requests are for.

The project lists the app itself because Django finds an app's templates only when the project
names the app. This is the same arrangement as `crispy_forms` and `mvp_forms` in
[ADR 0029](0029-forms-are-drawn-by-django-mvp-forms.md).

`daisy_cotton` goes below `mvp` because the first app listed wins where both packages ship a
component under the same name. That is now the icon alone: this package's icon looks a name up
in the configured icon packs, and daisy-cotton's own components draw their icons through it.
Listed above `mvp`, daisy-cotton's plain icon would answer instead.

## Revisit if

A daisy-cotton release `0.4` or later is tested with this package, or this package stops shipping
a component of the same name as one in daisy-cotton and the order no longer decides anything.
For django-cotton: this package stops importing its compiler, and django-cotton reaches a release
that promises its template behaviour holds across minor versions.
