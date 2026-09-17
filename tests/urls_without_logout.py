"""URLConf for a project that provides no ``account_logout`` name.

Used by tests/test_components/test_sidebar_user_menu_admin_link.py to prove the
shell's log-out row is absent rather than dead when the name does not resolve.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("account/", include("mvp.urls")),
]
