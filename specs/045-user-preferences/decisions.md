# Decisions

Ambiguities resolved while the specification was written, with what was chosen and why.

## The language switcher writes the preference

The shell already has a language switcher, which posts to Django's `set_language` view and is
remembered per browser. For a signed-in person, a choice made there
also becomes their stored language preference (FR-008). The alternative, leaving the switcher
per-browser, makes the stored preference win on the next sign-in or in another browser, so the
switcher would appear to undo itself. Treating both as one choice is what a person expects.

## The theme stays in the browser

The shell's theme switch keeps its choice in the browser today. Moving it to a stored preference
would change how an existing, delivered feature behaves for every project, and nobody has asked
for it. It is left out of scope, and a later change can move it once preferences exist.

## Preferences are for signed-in people only

A visitor who is not signed in has no account to store choices on. They keep what Django and the
shell do today: the browser's language, the language switcher's cookie, and the project's
timezone.
