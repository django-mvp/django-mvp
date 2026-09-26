"""The library app's URLs. ``app_name`` makes the landing ``library:catalogue``
wherever a project mounts it."""

from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.CatalogueView.as_view(), name="catalogue"),
    path("reading-list/", views.ReadingListView.as_view(), name="reading-list"),
]
