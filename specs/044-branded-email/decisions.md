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

## django-mvp does not send email

Sam, 2026-11-05, at the plan gate: django-mvp provides styling for the packages it wraps, and
those packages send their own email. django-mvp-accounts cannot change how allauth sends mail,
only override its templates. So the feature is a base template, email pieces and template tags,
and nothing that renders or sends. The sending helper, the subject templates, the generated plain
text and the language handling were removed from the specification and the plan. The styling is
inlined while the template renders, by a block tag in the base template, so it works whoever
renders it.

## The plan's review

The plan was reviewed before any code was written. Changes kept from it after the re-plan:

- The no-request site address fails with one clear error in every case: no sites framework, no
  `Site` for `SITE_ID`, or a `Site` with an empty domain.
- The theme reader takes a theme's colours only from rules that select the theme itself. The
  demo's `[data-theme="nord"] .mvp-sidebar` rule would otherwise have given a `nord` project the
  sidebar's colours as its email palette.
- The email's site name honours `MVP_CONFIG["site_name"]`, as the shell does.
- Previews are discovered from `email_previews.py`, because packages already have `emails.py`
  modules for sending.
- Remote stylesheets are never fetched while inlining.

## No fixed contrast ratio

Sam, 2026-11-05: "I don't like hard requirements that get in the way of nice design." In daisyUI's
`dark` theme the button's text measures 4.14:1 on the button, and the email uses it as it is. The
requirement is that text stays readable, with no ratio, and the contrast test was dropped.

## A text piece for paragraphs

Sam, 2026-11-05: `c-mvp.email.text` wraps a paragraph and turns a few named options into inline
styles, so authors do not pick spacing numbers and every email spaces paragraphs the same way.
The scale is written in the component's template, with no Python behind it.

## The demo carries no translation markup

The demo's email templates use plain text, per
https://github.com/django-mvp/django-mvp/issues/648. The package's own templates stay translatable.

## Each piece reads the brand itself

**Decision**: `c-mvp.email.button` loads `mvp_email` and calls `{% email_brand as brand %}` for its colour, instead of using the `brand` the base template put in the context. The other pieces take their colours from classes in the base template's style block.

**Why**: a project can turn on Cotton's context isolation, and then a component sees none of its parent template's variables. A button that depended on the base template's `brand` rendered with an empty `bgcolor` (test `test_the_colour_holds_where_cotton_hides_the_templates_variables_from_a_component`).

**Revisit if**: the base template and the pieces stop being rendered in the same pass.

## The sender's tests live with the other email tests

**Decision**: the base template's tests and the third-party sender's tests are in `tests/test_email/test_base_template.py`, and the `{% email_inline %}` tests are a class in `tests/test_email/test_mvp_email.py`, next to the tag tests from the earlier group. `tests/test_demo/test_email_templates.py` covers the demo's naming.

**Why**: `tests/test_templatetags.py` and `tests/test_templates.py` already exist as modules, so the `tests/test_templatetags/` and `tests/test_templates/` packages `tasks.md` names cannot be created.

**Revisit if**: `tests/test_email/` is declared in `non-mirror-paths` or the older modules are moved into packages.

## The test app is installed in the test settings

**Decision**: `tests.testapp_email` is appended to `INSTALLED_APPS` in `tests/settings.py`, the way `testapp_account` and `testapp_mounted` are, and its project override directory is added to `TEMPLATES[0]["DIRS"]` by a fixture in the one test class that needs it.

**Why**: the app's own templates are found through the app directories loader, as a third-party package's are. The override has to be found first, as a project's `DIRS` entry is, and only the tests that ask for it should see it.

**Revisit if**: a second test needs the override.
