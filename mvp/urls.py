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
"""

from django.urls import path

from .views.account import AccountCenterView, SignInView, SignOutView

urlpatterns = [
    path("", AccountCenterView.as_view(), name="account-center"),
    path("login/", SignInView.as_view(), name="account_login"),
    path("logout/", SignOutView.as_view(), name="account_logout"),
]
