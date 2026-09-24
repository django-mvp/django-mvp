"""URLconf mounting ``mvp.urls`` at ``account/``, the way the demo and a project do."""

from django.urls import include, path

urlpatterns = [
    path("account/", include("mvp.urls")),
]
