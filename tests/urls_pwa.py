"""URLconf mounting ``mvp.pwa.urls`` at the root, the way a project does."""

from django.urls import include, path

urlpatterns = [
    path("", include("mvp.pwa.urls")),
]
