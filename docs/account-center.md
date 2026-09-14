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

from mvp.views.account import AccountPageMixin
from mvp.views.extra import MVPTemplateView


class NotificationsView(LoginRequiredMixin, AccountPageMixin, MVPTemplateView):
    template_name = "yourapp/notifications.html"
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

`AccountPageMixin` supplies `page.breadcrumbs` from `mvp.menus.get_active_section(request)`
— the trail above the content, naming the area and, once the entry above resolves to a
section, that section. It imposes no access rule of its own: compose your own,
`LoginRequiredMixin` here, because the area does not decide another app's access rules.

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

### Declaring section membership for pages below a section

A page below your entry's own address still names your section in the trail, and links back
to it, once your entry declares the URL-name prefixes of the pages beneath it in
`extra_context["url_names"]`:

```python
# yourapp/urls.py
urlpatterns = [
    path("", NotificationsView.as_view(), name="notifications"),
    path("<int:pk>/", NotificationDetailView.as_view(), name="notifications-detail"),
]
```

```python
AccountCenterMenu.append(
    MenuItem(
        name="notifications",
        view_name="yourapp:notifications",
        extra_context={
            "label": "Notifications",
            "icon": "bell",
            "url_names": ("notifications",),
        },
    )
)
```

The prefixes in `url_names` match against `request.resolver_match.url_name` — the pattern's
own `name=`, without the app's namespace — so a request on `notifications-detail` resolves
to "Notifications" in the trail, linked back to the entry's own page. On the entry's own
page, the same crumb renders unlinked, because it names the page you're already on. An entry
with no `url_names` is only ever its own section, never a page below it. Because the match is
unnamespaced, pick a prefix distinctive enough that another installed app's URL names won't
also start with it.

## Where the next section goes

**Contributing a card to the landing page** — an installed app declares two optional
attributes on its `AppConfig` to put a card on the landing page. Documented here once the
app that adds it exists.
