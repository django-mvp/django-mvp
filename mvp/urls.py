"""The Account Center's URLs.

A project includes this at a prefix of its own choosing::

    from django.urls import include, path

    urlpatterns = [
        path("account/", include("mvp.urls")),
    ]

The landing page's URL name is left un-namespaced, ``account-center``
(decision D2): the shell's own user menu already reverses that bare name, and
namespacing it would break every page already written against it. Do not add
an ``app_name`` here.

Mounting this also registers ``account_login`` and ``account_logout`` — a
development-only sign-in and sign-out, so a page guarded by
``LoginRequiredMixin`` is reachable before a project installs an
account-management app. See docs/account-center.md.

Once allauth's account application is installed, this URLconf contributes
neither name. Django resolves a request by taking the first matching
pattern and reverses a name by taking the last registration of it, so a
name registered by both this URLconf and allauth's would answer a request
from whichever is mounted first while every link built with ``reverse()``
points at allauth's registration — and every documented way of mounting the
two puts this URLconf first. Standing the packaged entries down entirely
keeps which view answers those addresses independent of mount order.
"""

from django.urls import path

from .utils import app_is_installed
from .views.account import AccountCenterView, SignInView, SignOutView

urlpatterns = [
    path("", AccountCenterView.as_view(), name="account-center"),
]

if not app_is_installed("allauth.account"):
    urlpatterns += [
        path("login/", SignInView.as_view(), name="account_login"),
        path("logout/", SignOutView.as_view(), name="account_logout"),
    ]
