# Planning notes: Search the whole site from the navbar

Notes for research and planning to answer by name. None of them is settled.

## From Sam

1. "Several search-based 3rd party apps already exist for Django. Django-mvp's doctrine is mainly
   to provide UI support for well supported 3rd party apps. The session undertaking this feature
   in Django mvp will need to do proper research on what 3rd party apps are available and which
   one is best suited for us to support. Whichever we choose must be suitable for all of my
   different projects." The survey is in `research.md`, and the choice, modelsearch, is D1.
2. The package provides components and the host places them: the navbar field, the phone button,
   the dialog and the results page are components a project puts where it wants them.

## The prototype

3. The design comes from a prototype in a private project built on django-mvp. Its screens and
   the decisions recorded on it are agreed, and its look is ported, never redrawn from
   django-mvp's current components. The maintainer's build notes list each of its files and where
   it lands. In outline:

   | Prototype piece | Lands in django-mvp |
   |---|---|
   | the search field in the navbar on a wide screen, with its Ctrl K hint | a navbar component |
   | the search button on a phone | a navbar component |
   | the dialog: field, results area and Esc hint, on daisy-cotton's `c-modal` at the top | a component |
   | what the dialog shows as the reader types: groups, totals, the rest, every result | a template the dialog's request renders |
   | the hints before typing: the kinds and the keys | a template filled from the registered kinds |
   | the results page with a chip per kind and its groups | the results page's template, inside the app shell's page |
   | its styles: the pill, the rounded card under the top edge on a phone, groups, hits, the results page | the package's stylesheet |
   | its script: Ctrl K, ⌘ K, `/`, the arrows, Enter, one Esc, the ⌘ label on a Mac | the package's script |
   | its result and group records, and one search per kind | the kind registry and the model kind |
   | its results page view and the dialog's partial view | the search's views and addresses |

   The parity screens are the wide dialog after typing, the wide dialog before typing, the phone
   dialog after typing, and the results page wide and on a phone. The two result rows (compact in
   the dialog, full with an icon on the results page) become one component with a compact form.
   The small capitals section labels use one style, or the menu title class django-mvp already
   draws. Keyboard paths get tests, and the dialogs' roles are checked against WAI-ARIA's combobox
   and dialog patterns.
4. The prototype's dialog started from django-mvp-sphinx's search dialog, which the issue names as
   the look to keep. django-mvp-sphinx giving way to this search is that package's work
   (https://github.com/django-mvp/django-mvp-sphinx/issues/127), not this feature's.

## For research

5. **Dependency or integration.** A site whose only kind is a documentation index needs no
   modelsearch. Decide whether the model kind lives in a guarded integration under
   `mvp.integrations` (the registry, views and components in the core), or whether modelsearch
   becomes a runtime dependency, against Article VII and ADR 0033's reasoning for django-filter.
   modelsearch also brings `django-tasks` with it.
6. **Visibility querysets and `FilterField`.** modelsearch raises `FilterFieldError` when the
   narrowed queryset filters on a field not indexed as a `FilterField` (checked in `research.md`).
   A visibility queryset from an object-permission package filters on whatever it likes. Research
   whether the model kind should search first and intersect with the visibility queryset by
   primary key, so a developer need not index every field their permissions use, and what that
   costs in counts and ordering.
7. **As-you-type matching.** Decide when the model kind calls `.autocomplete()` and when
   `.search()`, so a partly typed last word still finds records (FR-009) without losing stemming
   on whole words.
8. **Where kinds are registered.** Settle how a kind is registered and how a package ships one so
   the host chooses it, in the style of `MountedApp` and of the navbar's component names in
   `MVP_CONFIG`. Look for what the repo and its installed packages already have before
   naming anything new.
9. **The navbar's existing search.** Decide whether `c-mvp.actions.search` becomes the wide
   navbar field or is replaced, and record the breaking change (D7).
10. **The dialog's request.** The prototype fetched the dialog's results with htmx on input, after
    a short delay, replacing any request still running. Confirm what django-mvp's shipped script
    already provides before adding any.
11. **The results page's address and its link.** The dialog's "the rest" and "every result" links
    go to the results page. Settle how the page finds the project's mounted address.
