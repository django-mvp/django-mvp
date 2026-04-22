"""Demo App URL configuration."""

from django.conf import settings
from django.urls import include, path

from . import views
from .views import (
    ContactFormView,
    FullShellDemoView,
    ListViewDemo,
    MVPDemoView,
    ProductCreateView,
    ProductDeleteView,
    ProductDeleteWithConfirmView,
    ProductDeleteWithRelatedView,
    ProductUpdateView,
)

urlpatterns = [
    # Main dashboard
    path("", MVPDemoView.as_view(template_name="demo/home.html"), name="home"),
    path("shell/", FullShellDemoView.as_view(), name="full_shell_demo"),
    path("layout/", views.LayoutDemoView.as_view(), name="layout_demo"),
    path("page-layout/", views.PageLayoutDemoView.as_view(), name="page_layout_demo"),
    path("widgets/", views.NavbarWidgetsView.as_view(), name="navbar_widgets_demo"),
    path("contact/", ContactFormView.as_view(), name="contact_form"),
    path(
        "contact/success/",
        MVPDemoView.as_view(template_name="demo/contact_success.html"),
        name="contact_success",
    ),
    # CRUD Views for Product model
    path("products/", ListViewDemo.as_view(), name="product-list"),
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product-update"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
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
    # 3rd Party Integration Demos
    path("datatables-demo/", views.DataTablesView.as_view(), name="datatables_demo"),
]


if settings.DEBUG:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
