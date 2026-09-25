"""The fixture app run as the site's own app: mounted at the root with ``main``.

Placed after the host's own routes, so the host's pages still resolve first.
The demo's URLs include ``mvp.urls``, which mounts the Account Center.
"""

from demo.urls import urlpatterns as demo_patterns
from mvp.mounted import mount
from tests.testapp_mounted.mounted import testapp_mounted

urlpatterns = [
    *demo_patterns,
    mount("", testapp_mounted, main=True),
]

# Django reads the error handlers off the root URLconf module.
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
