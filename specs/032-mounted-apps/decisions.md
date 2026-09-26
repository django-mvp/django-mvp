# Decisions: Mount one django-mvp app inside another

Rationale too long to inline in `spec.md`, and the ambiguities resolved while specifying.

## D1. The host mounts an app in its own URLs, not through a setting

**Chosen:** a host project mounts an app with one line in its own `urls.py` (FR-002). The package
keeps track of which apps are mounted from that line.

**Rejected:** a setting listing each app with its mount path, which the package's own URLs would
loop over. That puts the mount path in two places, the setting and the address the app answers
at. It also moves the URL prefix, the pattern order and the namespace out of the project's URLs,
which is where a Django developer looks for them.

**ADR:** docs/adr/0028-a-mounted-app-is-known-by-the-view-its-mount-resolved.md

## D2. A page belongs to an app because of the URLs it was served through

**Chosen:** the package decides which app a page belongs to from the URL patterns that matched the
request (FR-006).

**Rejected:** comparing the request's path with each app's mount prefix. A prefix comparison breaks
on language-prefixed URLs and on a project served under a sub-path. It also cannot tell two mounts
apart when one prefix begins with the other, and it misreads an app mounted at the site root as
owning every page.

**ADR:** docs/adr/0028-a-mounted-app-is-known-by-the-view-its-mount-resolved.md

## D3. The back link and the title use the site name

**Chosen:** the back link reads "Back to <site name>" and the title reads
`<page title> | <app name> | <site name>` (FR-007, FR-008). The site name is the one the page title
already ends with.

**Rejected:** the sidebar title, which is empty unless a project sets it. A back link that could
read "Back to" with nothing after it is worse than one that uses a name the page is already
guaranteed to show.

The maintainer asked for `<app name> | <site name>` on an app's pages. Keeping the page's own title
in front follows the shape every page already has, and a page with no title of its own reads
exactly as asked.

**ADR:** none — a presentation choice local to the shell's title and back link.

## D4. A failed visibility check refuses the way Django already does

**Chosen:** an anonymous visitor goes to the sign-in page and a signed-in person gets a forbidden
response (FR-013).

**Rejected:** answering "not found" to hide that the app exists. Django's own access mixins answer
this way, so a project gets the error pages and sign-in flow it already has, and a person who
could gain access by signing in is told how.

**ADR:** none — it follows Django's own access mixins, so nothing about it is non-obvious.

## D5. Mounting inside a mounted app is refused; mounting one app twice is left alone

The maintainer has no current use for either, and ruled both out of scope until one appears.
Mounting an app inside another mounted app is refused at startup, because the sidebar would then
have two apps to choose between on one page. Mounting the same app twice is not supported, but
it isn't prevented either: the maintainer does not want a restriction placed on it, and a project
that wants to experiment with it can.

**ADR:** docs/adr/0028-a-mounted-app-is-known-by-the-view-its-mount-resolved.md

## D6. A standalone deployment names a main app

**Chosen:** a project names one mounted app as its main app, and that app's menu is the sidebar on
every page outside other mounted apps (FR-016, FR-017).

**Why this is needed:** the motivating packages are each deployable on their own, and a package
that wrote its entries into the host's menu when imported would leak them into every project that
mounts it. The package therefore never touches the host's menu (FR-003), and a standalone project
needs a way to say "this app's menu is my menu". Mounting the app at the site root does not say
that, because the project's other pages, and pages of apps like the Account Center, are not the
app's pages.

**ADR:** none — covered by D11 and documented in docs/mounted-apps.md.

## D7. The Account Center loses its second navigation panel

The maintainer wants the Account Center to behave as a mounted app and has never liked the panel
beside its pages. Once the sidebar carries the Account Center menu, a second copy beside the
content would draw the same links twice. The layout's content block keeps its name, so a page an
app has written against the layout renders unchanged (FR-021). The package is pre-1.0, so
Article XVI allows the change to the layout with a changelog entry (FR-025).

**ADR:** none — a layout change recorded in the changelog. No future work has to abide by it.

## D8. The Account Center carries no visibility check

FS-028 decided that the Account Center gates its own landing page and nothing else, and that a page
another app contributes answers access for itself. A check on the whole app would gate those pages
too, which would change behaviour an app has already been written against. The landing page keeps
its own requirement for a signed-in person (FR-022).

**ADR:** none — carries FS-028's existing access rule forward unchanged.

## D9. A mounted app is marked on the matched view, not found by namespace or route

**Chosen:** `mount()` returns a URL resolver that wraps the view it resolves. The wrapper
carries the app and runs the app's check (research R3, R6). The same mechanism answers "which
app is this page in" and "may this person see it".

**Rejected:** namespaces, because the Account Center's landing page is deliberately
un-namespaced. Route strings, because they are prefix comparisons under another name. A
middleware, because it would be a second edit for the host.

**ADR:** docs/adr/0028-a-mounted-app-is-known-by-the-view-its-mount-resolved.md

## D10. The set of mounted apps is read from the URL tree

`mount()` writes nothing global. The registry is found by walking the resolved URLconf and is
cached on its resolver, so it follows `ROOT_URLCONF` changes and per-request URLconfs (research
R4).

**ADR:** none. It follows from D1 and D9 and is local to `mvp/mounted.py`.

## D11. The main app is a flag on its mount line

`mount("", app, main=True)` (research R8). The design review agreed it is the simplest shape the
spec allows. FR-016 and FR-018 require the main app to be mounted, and overriding the sidebar
block would break US-3 scenario 3.

FR-018's second refusal, naming an app the project has not mounted, has nothing to refuse under
this design: the flag exists only on a mount. Its test proves `main` is a `mount()` argument and
nothing else. **Flag for the merge gate:** half of FR-018 holds by construction rather than by a
check.

In a project with a main app, `AppMenu` is not drawn. The project adds its own entries to the
main app's menu.

**ADR:** none. It is recorded in `docs/mounted-apps.md`, and D1 already carries the reasoning
for putting it in `urls.py`.

## D12. A page that draws its own Account Center panel now shows the menu twice

`django-accounts-center` extends `mvp/base.html` directly and draws `AccountCenterMenu` beside
its content, as a workaround for #358. Once the sidebar carries that menu, its pages show it
twice until it drops its panel. The pages still work (FR-021). The changelog says so, and a
follow-up is due in `django-accounts-center`. Without the panel, the Account Center layout no
longer needs `{% block content %}` for itself, which clears the cause of #358. #358 stays
separate work.

**Flag for the merge gate:** the FR-020 and FR-021 interaction with django-accounts-center.

**ADR:** none. It is a consequence of D7.

## D13. Two apps whose menus both link one page: the first mount wins

Research R7's menu rule can find two apps for one page only when two apps' menus link the same
host page. The first mount in URL order wins. Accepted rather than refused: it cannot be
detected at startup, and no current app does it. Refusing it at request time would turn a
navigation choice into an error page.

**ADR:** none. It is an edge of R7, documented on the page.

## D14. A main app whose check refuses the request is not drawn

The spec doesn't cover it. Drawing a menu whose every link answers 403 is worse than drawing the
host's own `AppMenu`, so those pages fall back to `AppMenu`.

**ADR:** none. Local to this feature.

## D15. A refused request resolves to no app anywhere

`for_request()` returns no app for a request the app's check refuses, whether a mount or a menu
claimed the page. A project's own `403.html` then cannot name the app or draw its menu to a
person it has just refused (design review SEC-001).

**ADR:** none. It is part of D9's contract and documented with it.

## D16. The demo mounts a small app

`demo/library/` has no requirement of its own behind it. It exists because the Account Center
cannot show the host's menu entry or the dock entry being current (US-1 scenarios 5 and 6), and
the walkthrough needs a running page for both.

**ADR:** none. Demo only.

## D17. With no site name the back link reads "Back"

**Decision:** the back link is labelled "Back to <site name>", and "Back" when neither `MVP_CONFIG["site_name"]` nor the current site has a name.

**Why:** the title puts the site name last and reads as an empty segment when there is none, so it has no text to fall back to. "Back to" with nothing after it points nowhere, and "Back" is the honest remainder. Both strings are translatable.

**Revisit if:** a project with no site name wants a different label. Overriding `cotton/app/sidebar/back.html` is the route today.

**ADR:** none — a label fallback local to one template.

## D18. The back link is a menu row in a plain list

**Decision:** `cotton/app/sidebar/back.html` renders one `<c-menu.item>` inside a bare `<ul class="menu">`.

**Why:** the row lines up with the entries under it and takes the icon rail's behaviour for free (centred icon, tooltip). The label span is hidden in the rail, so the label is also set as the link's `aria-label`. `<c-menu>` is not used because it adds `role="navigation"`, and the sidebar is tested to carry one navigation landmark.

**Revisit if:** a design pass wants the back link to look unlike a menu row.

**ADR:** none — markup detail inside one template.

## D19. The demo's dock carries no library entry

An existing browser test pins the demo dock to one link. The dock entry being current on an
app's pages is proved by `tests/test_mounted.py`, so the demo keeps its sidebar entry only.

**ADR:** none. Demo only.

## D20. Pre-existing tests removed or changed because the panel is gone (FR-020)

**Decision:** the tests whose subject was the Account Center's second navigation panel are removed, and the assertions about that panel inside shared browser tests are dropped. Nothing else about those tests changed.

Removed from `tests/test_views/test_account.py`:
- `TestAccountCenterView::test_signed_in_request_shows_the_navigation_panel`
- `TestAccountLayout::test_page_content_renders_beside_the_navigation_panel`
- `TestAccountLayout::test_the_navigation_is_a_landmark_with_an_accessible_name`
- `TestAccountLayout::test_it_draws_the_entry_for_the_landing_page`
- `TestAccountLayout::test_a_persistent_card_renders_at_the_configured_breakpoint`
- `TestAccountLayout::test_a_collapsed_control_renders_below_the_breakpoint`
- `TestAccountLayout::test_the_collapsed_control_is_the_packaged_dropdown`
- `TestAccountLayout::test_the_menu_is_processed_once_for_both_sites`
- `TestAccountLayout::test_the_wide_panel_follows_the_content_and_the_collapsed_one_precedes_it`

Assertions on the panel's two regions dropped from `tests/test_components/test_responsive_visibility.py`, with the helpers that located them and the docstrings that counted four regions instead of three:
- `TestNarrowOnlyRegions::test_shown_below_hidden_at_or_above` (parametrised)
- `TestNarrowOnlyRegions::test_hidden_at_every_width_when_never`
- `TestWideOnlyRegions::test_hidden_below_shown_at_or_above` (parametrised)
- `TestWideOnlyRegions::test_shown_at_every_width_when_never`
- `TestVisibilityWithoutJavaScript::test_visibility_is_identical_with_javascript_disabled`

**Why:** the spec removes the panel (FR-020), so a test that asserts the panel is present asserts removed behaviour. The navbar regions those browser tests also cover keep every assertion.

**Revisit if:** the panel returns in any form.

**ADR:** none — a test-suite consequence of FR-020.

## D21. Two test URLconf helpers stop including `mvp.urls` a second time

**Decision:** in `tests/test_views/test_account.py`, `_urlconf()` and `_fixture_urlconf()` drop their own `path("", include("mvp.urls"))`. Each already includes `demo.urls`, which includes `mvp.urls`. No test body or assertion changed.

**Why:** the Account Center is now a mounted app, so including `mvp.urls` twice mounts it twice, which is unsupported (D5). Each helper already reached `mvp.urls` through `demo.urls`, so its own include was redundant.

**Revisit if:** a helper needs `mvp.urls` ahead of `demo.urls`. `_urlconf_with_allauth()` in the same file still includes it twice, ahead of allauth by design; the tests using it do not read the mounts, so it stays green, and it is flagged in the report.

**ADR:** none — test helpers only.

## D22. The landing's title override goes in the mount commit

**Decision:** `overview.html` loses its `{% block title %}` override in T010, not T011.

**Why:** T010's title test (`Account Center | <site name>` exactly) cannot pass while the override is there, and each commit has to leave the tree green.

**Revisit if:** never; the change is the one T011 asks for, made one commit earlier.

**ADR:** none — commit ordering only.

## D23. The main app's check is read through `MountedApp.has_permission()`

D14 says a main app whose check refuses the request is not drawn. The lookup of the menu to
draw calls `MountedApp.has_permission(request)` and falls back to `AppMenu` when it returns
false. The same method is what the view wrapper, the host's menu entry and the request's app
lookup ask (D26).

**ADR:** none — the name of one method, local to mvp/mounted.py.

## D24. The check runs synchronously in an async view's wrapper

**Decision:** `bind()`'s async wrapper calls `has_permission()` directly rather than through `sync_to_async`. The docstring on `MountedApp` says a check must not touch the database from an async view.

**Why:** `asgiref` is not a declared dependency, and importing it is refused by deptry. Adding a dependency is outside this story.

**Revisit if:** `asgiref` is declared. A check reading `request.user` on a lazily loaded session user would then be safe in an async view.

**ADR:** none — a documented limitation local to bind(). Revisit with the asgiref question.

## D25. `for_request()` returns `None` for a refused request, after the lookup

**Decision:** `for_request()` resolves the app as before, then answers `None` when that app's `has_permission()` is false. `claiming_menu()` also skips an app whose check fails, so the next app whose menu marks the page current can claim it.

**Why:** D15. A refused request shows no app in any template, including a project's own 403 page. Skipping in `claiming_menu()` keeps a refusing app from hiding a page another app's menu also links.

**Revisit if:** never.

**ADR:** none — part of D15's contract, local to for_request().

## D26. The package declares a class, and the host mounts an instance it can adjust

**Decision:** a package declares its app as a `MountedApp` subclass, with `name`, `icon`,
`menu`, `urls`, `landing` and `check` as class attributes. The host always mounts an instance:
`mount("literature/", LiteratureApp(icon="journal"))`. It changes the name, icon, menu or check
without touching the package, either per instance, through keyword arguments that must name an
attribute the class already defines (anything else is a `TypeError` naming the keyword), or by
subclassing. `check` is a bool or a callable. `has_permission(self, request)` decides access and
is the method a subclass overrides, calling `super()` if it wants the declared check too. By
default it calls `check` with the request when it is callable, and otherwise uses its truth
value. The callable test comes first, because a function is always truthy. The host builds its
menu entry from the same instance it mounted: `literature.menu_item()`.

**Why:** an app instantiated by its own package left the host no say. A host whose icons clash, or
which wants its own rule about who may see the app, had to fork or monkey-patch. This follows two
Django precedents a Django developer already knows. Class-based views take per-instance settings
through `as_view(**initkwargs)`, which refuses a keyword the class does not define, and they take
larger changes through subclassing. `ModelAdmin` decides access in `has_*_permission` methods that
a subclass overrides.

**ADR:** docs/adr/0028-a-mounted-app-is-known-by-the-view-its-mount-resolved.md

## D27. The current app reaches templates through the package's context processor

**Decision:** `mvp.context_processors.mvp_config`, which every project using the shell already
installs, adds the current request's mounted app and the menu the sidebar should draw, as lazy
values. Neither is computed unless a template reads it. `<c-app.sidebar>` reads them from context
the way it already reads `mvp_config`, and `mvp/base.html` appends the app's name to the title with
an `{% if %}`. There is no template tag or filter for it.

**Why:** the maintainer asked for the context processor when the idea was first discussed, and
does not want the template tag library to grow. The first build used a tag and a title filter
with no decision recorded for either. The filter existed only to drop the leading separator on a
page with no title. The title now reads the way a title-less page already reads, which removes
the filter's reason to exist. Cotton passes the parent context to a component, and under context
isolation it builds a `RequestContext` for the request, which runs the processors again. So the
values reach the sidebar in both modes without `base.html` passing them down.

**ADR:** none — how a value reaches the templates, local to the shell and recorded here.

