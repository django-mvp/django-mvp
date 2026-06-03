"""Demo App URL configuration."""

from django.conf import settings
from django.urls import include, path

from mvp.views import MVPHomeView, MVPTemplateView

from . import views
from .views import (
    CategoryDeleteWithRelatedView,
    CategoryUpdateView,
    ComponentView,
    ContactFormView,
    ErrorPagePreviewView,
    FullShellDemoView,
    HtmxProductCreateView,
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
    path(
        "buttons/",
        MVPTemplateView.as_view(template_name="demo/buttons.html"),
        name="buttons",
    ),
    path("components/", ComponentView.as_view(), name="custom-components"),
    path("i18n/", include("django.conf.urls.i18n")),
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
    # HTMX Form Mixin Demo
    path(
        "htmx-demo/",
        HtmxProductCreateView.as_view(),
        name="htmx_demo",
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
    # Theming demos
    path(
        "theming/scss-variables/",
        views.ThemeCustomizationView.as_view(),
        name="scss_variables_demo",
    ),
    # Error page previews — developer convenience routes
    path(
        "errors/400/",
        ErrorPagePreviewView.as_view(template_name="400.html"),
        name="error-preview-400",
    ),
    path(
        "errors/403/",
        ErrorPagePreviewView.as_view(template_name="403.html"),
        name="error-preview-403",
    ),
    path(
        "errors/404/",
        ErrorPagePreviewView.as_view(template_name="404.html"),
        name="error-preview-404",
    ),
    path(
        "errors/500/",
        ErrorPagePreviewView.as_view(
            template_name="500.html",
            extra_context={"support_email": settings.DEFAULT_FROM_EMAIL or None},
        ),
        name="error-preview-500",
    ),
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
