"""URLconf mounting ``mvp.urls`` at the site root, the way the demo and a project do."""

from django.urls import include, path

urlpatterns = [
    path("", include("mvp.urls")),
]
