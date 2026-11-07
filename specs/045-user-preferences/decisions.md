# Decisions

Ambiguities resolved while the specification was written, with what was chosen and why.

## D1 — The language switcher writes the preference

The shell already has a language switcher, which posts to Django's `set_language` view and is
remembered per browser. For a signed-in person, a choice made there
also becomes their stored language preference (FR-008). The alternative, leaving the switcher
per-browser, makes the stored preference win on the next sign-in or in another browser, so the
switcher would appear to undo itself. Treating both as one choice is what a person expects.

**ADR:** none — a behaviour of one view, documented on the Account Center page.

## D2 — The theme stays in the browser

The shell's theme switch keeps its choice in the browser today. Moving it to a stored preference
would change how an existing, delivered feature behaves for every project, and nobody has asked
for it. It is left out of scope, and a later change can move it once preferences exist.

**ADR:** none — a scope boundary for this feature, nothing built on it.

## D3 — The timezone select stays a plain select

The timezone list has 599 entries. mvp-forms has a searchable select widget, but it needs Tom
Select, which the shell does not ship, and loading it from elsewhere would break G14. The choices
are grouped by region instead, which keeps the list usable without a script.

**ADR:** none — a widget choice, revisited when the shell ships a searchable select.

## D4 — The language switcher posts to a small view of django-mvp's own

Django's `set_language` cannot be told to save a preference. A view in `mvp.urls` saves the
signed-in person's choice and then calls Django's view, so the cookie, the redirect and the
validation stay Django's.

**ADR:** none — local to the language view, documented on the Account Center page.

## D5 — Preferences are for signed-in people only

A visitor who is not signed in has no account to store choices on. They keep what Django and the
shell do today: the browser's language, the language switcher's cookie, and the project's
timezone.

**ADR:** none — a scope boundary for this feature.

## D6 — The design review's findings and what was done

- **The landing page is never empty now (high).** The preferences card supersedes FS-028's empty card region. T006 updates the three tests, the docs section and the docstring that assert it.
- **The person's language is put back after each request (high).** Without `LocaleMiddleware`, nothing else resets the active language per thread. The middleware restores the previous language and sets `Content-Language` itself.
- **The language view enforces CSRF itself**, with `csrf_protect` and `require_POST`, because Django's `set_language` relies on the project's middleware.
- **`mvp.E004`'s hint names the mixin**, so an upgrading project learns both steps on its first startup.
- **The language view stores nothing when the project offers one language**, where the group has no language field.
- **The timezone choices are built once per process.**
- **No `locale_of` helper and no unloadable-zone fallback.** The first had one caller, the second could not happen. `language` is `required=False`.
- **SC-002 was wrong as written** ("no new setting"). Sam approved the correction at the plan gate: two installation lines.

**ADR:** docs/adr/0042-every-user-model-carries-preferences.md for the required field; the review's other remedies are local to this feature.

## D7 — Two existing test files change, and why

`tests/test_views/test_account.py` (three tests asserting an empty card region) and `tests/test_menus.py` (one test listing the Account Center menu's entries) assert what FS-028 delivered: an Account Center with no card and only its landing entry. FS-045 FR-001 adds the preferences card and menu entry that every project now has, so each assertion changes to expect them. No assertion was weakened: each still pins the exact list or count.

**ADR:** none — local to this feature, nothing downstream inherits it.
