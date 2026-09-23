"""URLConf for a project that provides no ``account_logout`` name.

Used by tests/test_components/test_sidebar_user_menu_admin_link.py to prove the
shell's log-out row is absent rather than dead when the name does not resolve.

The landing page is wired up directly rather than by including ``mvp.urls``:
that URLconf registers ``account_logout`` beside it, so including it here would
supply the very name this configuration exists to withhold.
"""

from django.contrib import admin
from django.urls import path

from mvp.views.account import AccountCenterView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("account/", AccountCenterView.as_view(), name="account-center"),
]
