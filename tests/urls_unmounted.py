"""The demo's URLconf without the search mounted, for tests of a host that has none."""

from demo.urls import urlpatterns as demo_patterns

urlpatterns = [
    pattern for pattern in demo_patterns if str(pattern.pattern) != "search/"
]

# Django reads the error handlers off the root URLconf module.
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
