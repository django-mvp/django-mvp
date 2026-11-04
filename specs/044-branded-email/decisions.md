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

## Colours come from settings, not from the theme stylesheet

daisyUI themes are written in oklch custom properties, which mail clients cannot read. Reading
them out of a project's CSS would mean parsing and converting colours at send time, from a file
whose location the package does not own. A few hex colours in `MVP_CONFIG`, falling back to the
installable app's `theme_color`, is one setting and no parser. Sam took this option at intake.

## Sending fails without a site address

An email sent from a background worker has no request to take an address from. Sending one with
relative links and a relative logo would deliver a broken email silently. Failing with the setting
named is caught the first time a developer sends from a worker.
