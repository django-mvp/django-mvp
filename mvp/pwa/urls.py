"""Mount at the root of the project's URLconf: ``path("", include("mvp.pwa.urls"))``."""

from django.urls import path

from mvp.pwa import views

urlpatterns = [
    path("manifest.webmanifest", views.manifest, name="mvp-pwa-manifest"),
    path("sw.js", views.service_worker, name="mvp-pwa-service-worker"),
]
