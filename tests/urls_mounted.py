"""A host URLconf that mounts the fixture app at ``mounted/``."""

from demo.urls import urlpatterns as demo_patterns
from mvp.mounted import mount
from tests.testapp_mounted.mounted import testapp_mounted

urlpatterns = [
    *demo_patterns,
    mount("mounted/", testapp_mounted),
]

# Django reads the error handlers off the root URLconf module.
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
