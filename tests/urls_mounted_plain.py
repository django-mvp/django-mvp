"""A host URLconf that includes the mounted fixture app with plain ``include()``.

Proves the fixture pages render before any mounting exists (T001).
"""

from django.urls import include, path

from demo.urls import urlpatterns as demo_patterns

urlpatterns = [
    *demo_patterns,
    path("mounted/", include("tests.testapp_mounted.urls")),
]
