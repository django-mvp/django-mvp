# ADR 0006 — django-crispy-forms and crispy-tailwind are runtime dependencies

**Status:** accepted

## Decision

`django-crispy-forms` and `crispy-tailwind` are declared in `[project].dependencies`. They are not
extras, not optional integrations, and not guarded imports. Consuming projects must add
`crispy_forms` and `crispy_tailwind` to `INSTALLED_APPS`, which the installation documentation
states as required setup rather than an add-on.

## Why

`mvp/templates/cotton/form/render.html` has always loaded `crispy_forms_tags` and
`tailwind_filters` unconditionally. The dependency existed in the code and was absent only from the
metadata, so a project installing the package as documented and rendering a form page got a
template error. Declaring it records what was already true.

The package otherwise keeps a deliberately small runtime dependency set, and genuinely optional
integrations — django-tables2, django-filter — do live behind guarded imports in
`mvp.integrations`. Form rendering is different in kind: it is the packaged path, not one of
several, and there is no reduced-polish fallback to degrade to.

Installing the distributions is necessary but not sufficient, which is why the documentation change
is part of this decision rather than a footnote to it. Django resolves template tag libraries only
from apps in `INSTALLED_APPS`, so `{% load crispy_forms_tags %}` still raises `TemplateSyntaxError`
without the two app entries.

A Django system check reporting the missing apps at startup was considered and declined: no
requirement asked for it, and a check is a public surface of its own needing an identifier,
documentation and a changelog entry.

## Revisit if

The package stops rendering forms through crispy, or grows a genuine fallback renderer that works
without it.
