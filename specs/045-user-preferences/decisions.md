# Decisions

Ambiguities resolved while the specification was written, with what was chosen and why.

## D1 — The language switcher writes the preference

The shell already has a language switcher, which posts to Django's `set_language` view and is
remembered per browser. For a signed-in person, a choice made there
also becomes their stored language preference (FR-008). The alternative, leaving the switcher
per-browser, makes the stored preference win on the next sign-in or in another browser, so the
switcher would appear to undo itself. Treating both as one choice is what a person expects.

## D2 — The theme stays in the browser

The shell's theme switch keeps its choice in the browser today. Moving it to a stored preference
would change how an existing, delivered feature behaves for every project, and nobody has asked
for it. It is left out of scope, and a later change can move it once preferences exist.

## D3 — The timezone select stays a plain select

The timezone list has 599 entries. mvp-forms has a searchable select widget, but it needs Tom
Select, which the shell does not ship, and loading it from elsewhere would break G14. The choices
are grouped by region instead, which keeps the list usable without a script.

## D4 — The language switcher posts to a small view of django-mvp's own

Django's `set_language` cannot be told to save a preference. A view in `mvp.urls` saves the
signed-in person's choice and then calls Django's view, so the cookie, the redirect and the
validation stay Django's.

## D5 — Preferences are for signed-in people only

A visitor who is not signed in has no account to store choices on. They keep what Django and the
shell do today: the browser's language, the language switcher's cookie, and the project's
timezone.
