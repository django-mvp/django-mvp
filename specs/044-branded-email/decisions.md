# Decisions: Branded HTML email layout

Rationale too long to sit in `spec.md`, and the points settled without asking.

## CSS inlining with css-inline, not MJML

Measured on 2026-11-04:

| Package | Version | Released | Downloads a month | Licence |
|---|---|---|---|---|
| css-inline | 0.23.1 | 2026-10-27 | 2.8M | MIT |
| mjml-python (wraps the Rust `mrml`) | 1.4.2 | 2026-09-01 | 413k | MIT |
| mjml (pure Python port) | 1.0.0a1 | 2026-09-12 | 306k | MIT |
| premailer | — | 2021 | — | unmaintained |

The layout is one column, written once in this package. MJML's layout engine would save little
here, and it would make every package that sends mail write its emails in a second template
language, with Django tags inside MJML. Plain Django templates with table markup, inlined at send
time, keep emails written the way every other Django template is written. premailer is out:
nothing released since 2021.

css-inline becomes a dependency of the package rather than an integration, because every email
the helper sends needs it.

## No GPL converter for the plain-text part

`html2text`, the usual HTML-to-text converter, is GPL-3.0, which FR-019 rules out. Planning picks
a permissively licensed converter or writes the small conversion the layout's own markup needs.

## The preview page is DEBUG-only and staff-only

A preview renders templates with example data, so it leaks nothing real. It still exposes the
names and wording of every email a project sends, and a page that exists in production is a page
someone has to remember to protect. Tying it to `DEBUG` makes it absent in production by
construction. Staff-only covers a shared staging server run with `DEBUG` on.

## Colours come from the theme, with no setting of their own

Sam, 2026-11-05: no new `MVP_CONFIG` option unless there is no alternative. There is one. The
names of a project's light and dark themes are already in `MVP_CONFIG["theme"]`, and every theme
is a block of CSS custom properties in a static file: the package's prebuilt ones in
`django-mvp.css`, a project's own in a plain stylesheet. The packaged values are plain `oklch()`
colours, which convert to hex arithmetically, with no dependency.

The package does not know which file holds a project's theme, because the project links it from
its own base template. So the stylesheets the static files finders can see are searched for the
theme's block, and a project's own file wins over the package's, matching the page, where a
project's unlayered stylesheet beats the package's layered one. The search runs once per process
and is cached. A value it cannot read or convert falls back to the package's and is reported by a
start-up check, so the problem shows before an email goes out.

The cost: a project that wants its email in different colours from its site has no setting for
it and overrides the base layout. That is in keeping with the email looking like the site.

## The site address comes from the request or the sites framework

An email sent from a background worker has no request to take an address from, so the helper falls
back to the current `Site`'s domain. Every project that sends account email already has the sites
framework, because allauth requires it. A `Site` holds no scheme, so the address is HTTPS, and HTTP
while `DEBUG` is on, which matches a dev server.

## Sending fails without a site address

With neither a request nor the sites framework, sending an email with relative links and a
relative logo would deliver a broken email silently. Failing is caught the first time a developer
sends from a worker.
