# Account Center

The Account Center is a place in the shell for a person to manage their own account:
a landing page, a navigation panel beside it, and a menu any installed app can add a
page or a menu entry to. django-mvp provides the area itself. Account management —
sign-in, sign-up, password and multi-factor flows — still lives in
[django-accounts-center](https://github.com/django-mvp/django-accounts-center), which
is the first app that adds pages to this area.

## Mounting it

The area ships as an includable URLconf. Include it at a prefix of your own choosing:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path("account/", include("mvp.urls")),
]
```

That is the only switch — there is no `MVP_CONFIG` key that enables, disables or
relocates it. A project that never includes the URLconf sees no failure: every reverse
of the area's URL name in shipped markup (the user menu's "Account Center" link, for
one) stays conditional, and the link is simply absent.

The landing page's URL name is `account-center`, deliberately left un-namespaced so
that markup already written against it keeps resolving.

## Signing in

The landing page requires a signed-in user and sends an anonymous visitor to your
project's configured sign-in location. The area does not gate any page a contributing
app adds to it — a contributed page decides its own access rules, the same way any
other view in your project does.

## What it looks like with nothing installed

With no app contributing anything, the landing page renders its own heading and
introduction, and an empty region where a contributed card will appear later. It does
not fall back to listing the menu — the menu is already on the page, beside the
content.

## Where the later sections go

This page will grow two more sections as the area does:

- **Adding a menu entry and a page** — an installed app appends to `AccountCenterMenu`
  (see [Navigation](navigation.md)) and writes a page that extends the area's layout.
- **Contributing a card to the landing page** — an installed app declares two optional
  attributes on its `AppConfig` to put a card on the landing page.

Both are documented here once the app that adds them exists.
