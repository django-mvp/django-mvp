# Decisions: Branded HTML email layout

Rationale for the ambiguities settled while writing the specification. How the feature is built
is not settled here: that is research and planning, with the notes in `planning-notes.md`.

## The preview page is DEBUG-only and staff-only

A preview renders templates with example data, so it leaks nothing real. It still exposes the
names and wording of every email a project sends, and a page that exists in production is a page
someone has to remember to protect. Tying it to `DEBUG` makes it absent in production by
construction. Staff-only covers a shared staging server run with `DEBUG` on.

## Sending fails when the site's address cannot be found

An email with relative links and a relative logo is broken in every mail client, and nothing
would tell anyone. Failing is caught the first time a developer sends from a background worker.

## A colour or logo the email cannot use does not stop email

Account email (sign-in codes, password resets) has to go out even when the brand is wrong. A
problem with the brand is reported at start-up instead, where a developer sees it.
