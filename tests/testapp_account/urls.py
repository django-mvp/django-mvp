"""URLs for the Account Center fixture app (US-2).

Mounted by tests via ``override_settings(ROOT_URLCONF=...)`` alongside
``mvp.urls`` — never through ``demo/urls.py``, which stays untouched by this
story.
"""

from django.urls import path

from . import views

app_name = "testapp_account"

urlpatterns = [
    path("plain/", views.FixturePlainView.as_view(), name="plain"),
    path("grouped/", views.FixtureGroupedView.as_view(), name="grouped"),
]
