"""Demo App URL configuration."""

from django.conf import settings
from django.urls import include, path

from . import views
from .views import (
    E400,
    E403,
    E404,
    E500,
    CategoryDeleteWithRelatedView,
    CategoryUpdateView,
    DemoHomeView,
    ProductCreateView,
    ProductDeleteView,
    ProductDeleteWithConfirmView,
    ProductDeleteWithRelatedView,
    ProductDetailView,
    ProductListView,
    ProductUpdateView,
)

urlpatterns = [
    path("", DemoHomeView.as_view(), name="home"),
    path("layout/", views.layout_demo, name="layout"),
    path("theme/", views.theme_customization_demo, name="customization"),
    path("components/", views.components_demo, name="custom-components"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product-update"),
    path(
        "products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"
    ),
    path(
        "products/<int:pk>/delete/related/",
        ProductDeleteWithRelatedView.as_view(),
        name="product-delete-related",
    ),
    path(
        "products/<int:pk>/delete/confirm/",
        ProductDeleteWithConfirmView.as_view(),
        name="product-delete-confirm",
    ),
    # Category CRUD (partial — update only, no delete, used for US4 E2E verification)
    path(
        "categories/<int:pk>/edit/",
        CategoryUpdateView.as_view(),
        name="category-update",
    ),
    path(
        "categories/<int:pk>/delete/related/",
        CategoryDeleteWithRelatedView.as_view(),
        name="category-delete-related",
    ),
    path("django-tables2/", views.DataTablesView.as_view(), name="djangotables2"),
    path("errors/400/", E400, name="error-preview-400"),
    path("errors/403/", E403, name="error-preview-403"),
    path("errors/404/", E404, name="error-preview-404"),
    path("errors/500/", E500, name="error-preview-500"),
    path("i18n/", include("django.conf.urls.i18n")),
]


if settings.DEBUG:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))

# Auth URLs (provides login, logout, password change, etc.)
urlpatterns += [path("accounts/", include("django.contrib.auth.urls"))]

# Django error handlers — must be set on root URLconf module
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
