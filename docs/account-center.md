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

## Giving people a way there

Mounting the URLconf puts the area at an address. It does not put a link to it on screen:
the sidebar footer ships empty, so nothing draws one until you say so. The packaged user
menu is the route the shell already knows about — it renders an Account Center row for a
signed-in person, and nothing at all for a visitor:

```python
# settings.py
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "footer": [
                "actions.login",       # the visitor's half: renders only when signed out
                "user.sidebar-menu",   # the signed-in half: account centre, then log out
            ],
        },
    },
}
```

Those two are complements, and a project that configures one without the other leaves the
other state with nothing. The demo application configures both, which is the quickest place
to see the result.

## The landing page view

The URLconf points at `AccountCenterView`, exported from `mvp.views`. Most projects never
name it: including the URLconf is enough. Reach for it when you want the area's landing
page to say something of your own — a different title, or context your own template needs:

```python
# urls.py
from django.urls import path
from mvp.views import AccountCenterView


class MyAccountCenterView(AccountCenterView):
    page_title = "Your account"


urlpatterns = [
    path("account/", MyAccountCenterView.as_view(), name="account-center"),
]
```

Keep the `account-center` name if you do this, because the shell's user menu and every
contributed page's trail reverse it.

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

## Adding a menu entry and a page

An installed app appends to `AccountCenterMenu` from its own `menus.py` and writes a page
that extends the area's layout. It installs nothing else, imports from no other account
package and extends none of its templates.

### A menu entry

```python
# yourapp/menus.py
from flex_menu import MenuItem

from mvp.menus import AccountCenterMenu

AccountCenterMenu.append(
    MenuItem(
        name="notifications",
        view_name="yourapp:notifications",
        extra_context={"label": "Notifications", "icon": "bell"},
    )
)
```

Import this module the same way `AppMenu` picks up an app's own entries — autodiscovery,
or an explicit import in `AppConfig.ready()`. See [Navigation](navigation.md).

### A page against the layout

```python
# yourapp/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from mvp.views.extra import MVPTemplateView


class NotificationsView(LoginRequiredMixin, MVPTemplateView):
    template_name = "yourapp/notifications.html"

    def get_breadcrumbs(self):
        return [
            {"text": "Account Center", "href": reverse("account-center")},
            {"text": "Notifications"},
        ]
```

```django
{# yourapp/templates/yourapp/notifications.html #}
{% extends "mvp/account/base.html" %}
{% block account.content %}
  <c-page>
    <c-page.title title="Notifications" />
    ...
  </c-page>
{% endblock account.content %}
```

The area supplies no mixin for the trail: a page declares its own `breadcrumbs`, the same
way any other page built on `PageMixin` does — a static list for a fixed trail, or
`get_breadcrumbs()` where a crumb needs the request or another view's state, as above.
`NotificationsView` composes its own access-control mixin, `LoginRequiredMixin` here,
because the area does not decide another app's access rules.

### Per-request visibility

A menu entry carrying a `check` is shown only to the requests it answers yes for; an entry
with no `check` is always shown:

```python
AccountCenterMenu.append(
    MenuItem(
        name="billing",
        view_name="yourapp:billing",
        check=lambda request, **kwargs: request.user.has_perm("yourapp.view_billing"),
        extra_context={"label": "Billing", "icon": "credit-card"},
    )
)
```

An entry whose `view_name` cannot be resolved is dropped without affecting the rest of the
menu — the same rule every django-mvp menu already follows, not something the Account
Center adds.

### A page below your entry's own address

A page below your entry — a detail view, say — names its own trail the same way: declare
`breadcrumbs` or `get_breadcrumbs()` on that view too, linking back to the entry above it.
There's nothing to declare on the menu entry itself for this; the area resolves no trail
from the menu at all (Refined 2026-09-14).

```python
class NotificationDetailView(LoginRequiredMixin, MVPTemplateView):
    template_name = "yourapp/notification_detail.html"

    def get_breadcrumbs(self):
        return [
            {"text": "Account Center", "href": reverse("account-center")},
            {"text": "Notifications", "href": reverse("yourapp:notifications")},
            {"text": "Detail"},
        ]
```

## Contributing a card

An installed app puts a card on the landing page by shipping its own copy of the landing
page's template, extending the same name, and adding to its card block — no menu entry, no
`AppConfig` attribute, and no import from any other account package required:

```django
{# yourapp/templates/mvp/account/overview.html #}
{% extends "mvp/account/overview.html" %}
{% load i18n %}
{% block account.cards %}
  {{ block.super }}
  <c-card title="{% trans "Your Things" %}" icon="overview">
    <c-text>{% trans "Keep track of what you own." %}</c-text>
    <c-slot name="footer">
      <c-button href="{% url 'yourapp:things' %}" text="{% trans "Manage" %}" />
    </c-slot>
  </c-card>
{% endblock account.cards %}
```

Django resolves `{% extends "mvp/account/overview.html" %}` to the *next* template of that
name in the loader path, not back to itself — so several apps can each ship this same
filename, each adding their own card, chaining through `{{ block.super }}`. Put
`{{ block.super }}` first in the block, as above, so your card appears after whatever an
earlier app in the chain already added; put it last to appear before. The chain always ends
at django-mvp's own template, which declares the block empty, so an app that ships no
override changes nothing.

**Ordering matters.** The template loader returns the *first* app in your project's
`INSTALLED_APPS` that ships a template with this name — that's the copy the view actually
renders, and the one whose `{% extends %}` starts the chain. List an app that contributes a
card *before* `"mvp"` in `INSTALLED_APPS`; an app listed after it is never reached, and its
card never renders. This is the ordinary Django convention for overriding a packaged
template from your own app, not something the Account Center adds — most projects already
list their own apps ahead of their third-party ones.

A card's template is part of the same render as the rest of the page — the same context,
not a context of its own. `request`, `user`, `page` and anything your project's context
processors provide are all visible to it, the same as any other block on the page. If your
card needs data beyond what that context already carries, fetch it in the template — a
custom template tag or filter is the natural place — since the block shares its context
with the page around it rather than getting one of its own.
