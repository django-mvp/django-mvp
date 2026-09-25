"""URLs for the mounted fixture app.

Declares ``app_name`` so the landing reverses as ``testapp_mounted:index``
wherever a host mounts it.
"""

from django.urls import path

from . import views

app_name = "testapp_mounted"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("detail/", views.DetailView.as_view(), name="detail"),
    path("missing/", views.missing, name="missing"),
]
