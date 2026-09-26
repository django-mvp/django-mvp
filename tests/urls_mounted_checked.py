"""The staff-only fixture app mounted at ``mounted/``, with a shell-drawn 403."""

from demo.urls import urlpatterns as demo_patterns
from mvp.mounted import mount
from tests.testapp_mounted.mounted import testapp_mounted_staff

urlpatterns = [
    *demo_patterns,
    mount("mounted/", testapp_mounted_staff),
]

# Django reads the error handlers off the root URLconf module.
handler403 = "tests.testapp_mounted.views.forbidden"
handler404 = "mvp.views.error.not_found"
