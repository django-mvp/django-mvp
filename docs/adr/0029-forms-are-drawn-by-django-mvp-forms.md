# ADR 0029 — Forms are drawn by django-mvp-forms

**Status:** accepted

## Decision

`django-crispy-forms` and `django-mvp-forms` are declared in `[project].dependencies`, and every
packaged form is drawn with the `daisyui` template pack django-mvp-forms provides. Consuming
projects add `crispy_forms` and `mvp_forms` to `INSTALLED_APPS` and set both
`CRISPY_ALLOWED_TEMPLATE_PACKS` and `CRISPY_TEMPLATE_PACK` to the pack, which the installation
documentation states as required setup.

The package ships no template of the pack's and overrides none. What a field, a fieldset or a
layout object looks like is whatever django-mvp-forms draws. A project that wants one of them drawn
differently replaces that template itself, the way django-mvp-forms documents.

This replaces [ADR 0006](0006-crispy-forms-is-a-runtime-dependency.md), which named
`crispy-tailwind` as the pack. Its reasoning for a hard dependency carries over unchanged: form
rendering is the packaged path, not one of several, and there is no fallback to degrade to.

## Why

crispy-tailwind writes plain Tailwind utility classes with fixed greys and reds. Every other page
element the package ships is a daisyUI component that follows the project's theme, so forms were
the one part of a page that did not. It has also had no release since February 2024, and it predates
the `aria-describedby` ids Django 5.2 writes on a control.

Living with that took five template overrides in this package: two for the error ids, one for help
text, one for fieldsets and one for selects whose widget has a template of its own. Each one had to
sit at crispy-tailwind's own path and be found first, which is why `mvp` had to be listed above
`crispy_tailwind` in `INSTALLED_APPS` while a project's own apps had to be listed above `mvp`.

django-mvp-forms draws daisyUI components, writes the ids Django expects, renders a widget's own
template, and is tested against the Django and daisyUI versions this package supports. All five
overrides and the ordering rule go with the switch.

The overrides are not carried across as overrides of the new pack. Two definitions of how a
fieldset looks, one in each package, is the situation the switch removes. The divider a `Fieldset`
used to be drawn with is gone, and a `Fieldset` is a daisyUI `fieldset` with a visible legend.

A startup check that reports a project still configured for the old pack was considered and
declined. The upgrade is three lines of settings, and the release notes carry them.

[ADR 0003](0003-the-packaged-component-owns-formset-structure.md) is unaffected. django-mvp-forms
can draw a whole formset, but adding and removing rows, row headers and the tabular grid belong to
`<c-form.formset>`, which goes on rendering one field at a time through the pack.

## Revisit if

The package stops rendering forms through django-crispy-forms, or a project needs to choose a
different template pack for the packaged form pages.
