"""URLconf mounting ``mvp.pwa.urls`` under ``pwa/`` instead of the root."""

from django.urls import include, path

urlpatterns = [
    path("pwa/", include("mvp.pwa.urls")),
]
