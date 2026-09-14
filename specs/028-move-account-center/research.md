# Research — FS-028

What reading the two packages settled before planning. Every claim here names where it was read.

## The shell already reaches for an account area it does not have

`mvp/templates/cotton/user/sidebar_menu.html:12-17` reverses `account-center` and, when that name
resolves, draws a menu entry with `icon="account_center"`. Neither the URL name nor the icon key
exists in this package: `account_center` is registered in django-accounts-center's pack
(`dac/icons.py`), and the URL name comes from `dac/urls.py`. In a project without that package the
entry is skipped, so nothing raises, and the icon would render empty if it ever did.

This is why US-1 is worth delivering on its own: it closes a gap the shell already has rather than
only preparing for US-2.

## Breadcrumbs moved into the header, and django-accounts-center predates the move

`mvp/templates/cotton/app/header/navbar.html:40-42` renders `page.breadcrumbs` in the navbar, and
`mvp/views/base.py:114-171` (`PageMixin`) is what puts them in the context. The comment in
`mvp/templates/page_view.html` records the move: the trail used to open the page on a row of its
own and is now drawn in the app header.

django-accounts-center draws its own `<c-breadcrumbs>` bar inside the content
(`dac/templates/dac/base.html`), which was correct when it was written. Reproducing that here would
put two trails in two places on the same page, so the area supplies `page.breadcrumbs` instead. The
resolution logic it needs — which section the current request belongs to, including for pages below
a section's own address — is the one piece worth moving rather than rewriting
(`dac/menus.py:41-71`).

## Menus are found by name on a single global tree

`flex_menu/menu.py:572-622`: every `Menu` attaches to one module-level `root`, and
`MenuItem.get()` resolves a name with `anytree`'s `find_by_attr`, which returns the first match it
finds. `{% render_menu "AccountCenterMenu" %}` therefore resolves to whichever of two same-named
menus is encountered first, and app import order decides which. The collision with
django-accounts-center is real, silent, and not detectable from inside either package. Recorded as
D1: the name stays, the changelog carries the version relationship.

## The package ships no URLconf at all

There is no `mvp/urls.py` (`find mvp -name urls.py` returns nothing), and no documentation page
mentions including one. Every packaged view today is wired up by the project. The area therefore
introduces the package's first URLconf, which is why D2 records the namespacing choice explicitly:
un-namespaced, because the shell's own markup already reverses the bare name.

## The contribution mechanisms already exist and need no new machinery

- **Menu contribution** — `mvp/menus.py` documents a project appending to `AppMenu` from its own
  `menus.py`, imported from its app config's `ready()`. An app adding to the account menu does the
  same thing to a different menu.
- **Per-request visibility** — django-flex-menus takes a `check` callable per item, which is the
  whole of the mechanism django-accounts-center's ADR 0002 rests on. Nothing needs to be layered
  over it, and the story asserts it rather than building it.
- **Unresolvable entries** — `flex_menu/menu.py:391-399` drops an item whose URL will not resolve,
  and `mvp/menus.py` documents that behaviour already. The story asserts it.
- **Card contribution** — walking `apps.get_app_configs()` for optional attributes is what
  `dac/views.py:25-37` does, in fourteen lines, with no registry. The same shape is kept, with the
  attribute names changed off that package's prefix.

## Templates a page in the area extends

`mvp/templates/base.html` is an unqualified name the package ships as a forwarder to
`mvp/base.html`, explicitly so a project can own it and a reusable app can extend it without asking
its host (the comment in that file says so). The area's layout extends `base.html` for that reason,
where django-accounts-center extends `mvp/base.html` directly and so bypasses a project's own base.

## Nothing here needs a browser

The responsive behaviour is a class swap at the shell's configured breakpoint, and Article XIV
requires anything expressible as a rendered-template assertion to be written that way. The existing
`tests/test_components/test_layout_config.py` is the pattern for asserting breakpoint-derived
classes.
