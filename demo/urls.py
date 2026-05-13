"""Demo App URL configuration."""

from django.conf import settings
from django.urls import include, path

from mvp.views import MVPHomeView, MVPTemplateView

from . import views
from .views import (
    CategoryDeleteWithRelatedView,
    CategoryUpdateView,
    ContactFormView,
    FullShellDemoView,
    ListViewDemo,
    MVPDemoView,
    ProductCreateView,
    ProductDeleteView,
    ProductDeleteWithConfirmView,
    ProductDeleteWithRelatedView,
    ProductDetailView,
    ProductUpdateView,
)

urlpatterns = [
    # Main home — landing for guests, dashboard for authenticated users
    path(
        "",
        MVPHomeView.as_view(
            landing_template_name="demo/landing.html",
            dashboard_template_name="demo/dashboard.html",
        ),
        name="home",
    ),
    # About page — MVPTemplateView demo
    path(
        "about/",
        MVPTemplateView.as_view(
            template_name="demo/about.html",
            page_title="About Us",
            page_subtitle="Learn more",
            page_icon="info-circle",
            breadcrumbs=[{"text": "Home", "href": "/"}, {"text": "About"}],
        ),
        name="about",
    ),
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
    # 3rd Party Integration Demos
    path("datatables-demo/", views.DataTablesView.as_view(), name="datatables_demo"),
]


if settings.DEBUG:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))

# Auth URLs (provides login, logout, password change, etc.)
urlpatterns += [path("accounts/", include("django.contrib.auth.urls"))]
