"""The package's URLs.

A project includes this once, at the site root::

    from django.urls import include, path

    urlpatterns = [
        path("", include("mvp.urls")),
    ]

Each route here chooses its own address, so a project never has to put the
package's pages behind a prefix it picked for one of them. The Account
Center's pages live under ``account/``. The installable-app files sit at the
root, where a service worker has to be served from to control every page.

The landing page's URL name is left un-namespaced, ``account-center``
(decision D2): the shell's own user menu already reverses that bare name, and
namespacing it would break every page already written against it. Do not add
an ``app_name`` here.

Mounting this also registers ``account_login`` and ``account_logout`` — a
development-only sign-in and sign-out, so a page guarded by
``LoginRequiredMixin`` is reachable before a project installs an
account-management app. See docs/account-center.md.

While ``MVP_CONFIG["pwa"]`` is set, mounting this also serves the
installable-app files, ``manifest.webmanifest`` and ``sw.js``. With the setting
off those two routes do not exist. See docs/installable-app.md.

Once allauth's account application is installed, this URLconf contributes
neither name, so which view answers those two addresses never depends on the
order two URLconfs were mounted in. The reasoning is in
docs/adr/0024-a-stand-in-page-withdraws-when-the-real-app-arrives.md.
"""

from django.urls import path

from .config import MVP_CONFIG
from .pwa.views import manifest, service_worker
from .utils import app_is_installed
from .views.account import AccountCenterView, SignInView, SignOutView

urlpatterns = [
    path("account/", AccountCenterView.as_view(), name="account-center"),
]

if MVP_CONFIG["pwa"]:
    urlpatterns += [
        path("manifest.webmanifest", manifest, name="mvp-pwa-manifest"),
        path("sw.js", service_worker, name="mvp-pwa-service-worker"),
    ]

if not app_is_installed("allauth.account"):
    urlpatterns += [
        path("account/login/", SignInView.as_view(), name="account_login"),
        path("account/logout/", SignOutView.as_view(), name="account_logout"),
    ]
