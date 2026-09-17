"""URLConf providing ``account_logout`` and nothing else the user menu draws.

Used by tests/test_components/test_sidebar_user_menu_admin_link.py to prove the
menu's divider does not render when the log-out row is the only row.
"""

from django.contrib.auth.views import LogoutView
from django.urls import path

urlpatterns = [
    path("account/logout/", LogoutView.as_view(), name="account_logout"),
]
