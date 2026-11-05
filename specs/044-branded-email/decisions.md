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

## The plan's review

The plan was reviewed before any code was written. Changes made to the plan from it:

- An email sent without a language renders in the active language. Django's
  `translation.override(None)` switches translation off, so it is never called with `None`.
- The no-request site address fails with one clear error in every case: no sites framework, no
  `Site` for `SITE_ID`, or a `Site` with an empty domain.
- The theme reader takes a theme's colours only from rules that select the theme itself. The
  demo's `[data-theme="nord"] .mvp-sidebar` rule would otherwise have given a `nord` project the
  sidebar's colours as its email palette.
- The email's site name honours `MVP_CONFIG["site_name"]`, as the shell does.
- Plain-text links are written `text (address)`, not inscriptis's Markdown form.
- Previews are discovered from `email_previews.py`, because packages already have `emails.py`
  modules for sending.
- Remote stylesheets are never fetched while inlining.

## Open: the dark button's contrast

In daisyUI's `dark` theme, the package's default dark theme, the button's text on the button
measures 4.14:1 (`#edf1fe` on `#605dff`). FR-013 asks for 4.5:1 with the default themes, and
FR-009 asks for the theme's own colours. No colour in that theme reaches 4.5:1 on its primary.
This needs Sam's ruling before the build.
