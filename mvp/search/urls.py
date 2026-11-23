"""The search's addresses. Mount them with ``include("mvp.search.urls")``."""

from django.urls import path

from mvp.search import views

urlpatterns = [
    path("", views.SearchView.as_view(), name="mvp-search"),
    path("panel/", views.search_panel, name="mvp-search-panel"),
]
