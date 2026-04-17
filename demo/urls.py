"""Demo App URL configuration."""

from django.conf import settings
from django.urls import include, path

from . import views
from .views import (
    BasicListViewDemo,
    ContactFormView,
    ExplicitRendererDemo,
    FullShellDemoView,
    ListViewDemo,
    MinimalListViewDemo,
    MVPDemoView,
    ProductCreateView,
    ProductUpdateView,
)

urlpatterns = [
    # Main dashboard
    path("", MVPDemoView.as_view(template_name="demo/home.html"), name="home"),
    path("shell/", FullShellDemoView.as_view(), name="full_shell_demo"),
    path("layout/", views.LayoutDemoView.as_view(), name="layout_demo"),
    path("page-layout/", views.PageLayoutDemoView.as_view(), name="page_layout_demo"),
    path("widgets/", views.NavbarWidgetsView.as_view(), name="navbar_widgets_demo"),
    # List View Demos
    path("list-view/", ListViewDemo.as_view(), name="list_view_demo"),
    path("list-view/minimal/", MinimalListViewDemo.as_view(), name="minimal_list_demo"),
    path("list-view/basic/", BasicListViewDemo.as_view(), name="basic_list_demo"),
    path(
        "list-view/grid/1col/",
        MinimalListViewDemo.as_view(grid={"cols": 1}),
        name="grid_demo_1col",
    ),
    # Form View Demos
    path("contact/", ContactFormView.as_view(), name="contact_form"),
    path(
        "contact/success/",
        MVPDemoView.as_view(template_name="demo/contact_success.html"),
        name="contact_success",
    ),
    path(
        "explicit-renderer/",
        ExplicitRendererDemo.as_view(),
        name="explicit_renderer_demo",
    ),
    path("products/create/", ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path(
        "products/",
        MVPDemoView.as_view(template_name="demo/products_list.html"),
        name="products_list",
    ),
    # 3rd Party Integration Demos
    path("datatables-demo/", views.DataTablesView.as_view(), name="datatables_demo"),
]


if settings.DEBUG:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
