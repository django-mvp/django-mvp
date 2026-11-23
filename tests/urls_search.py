"""A host URLconf that mounts the search at ``search/`` beside the demo."""

from django.urls import include, path

from demo.urls import urlpatterns as demo_patterns

urlpatterns = [
    *demo_patterns,
    path("search/", include("mvp.search.urls")),
]

# Django reads the error handlers off the root URLconf module.
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
