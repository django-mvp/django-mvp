"""
Demo views for testing AdminLTE layout configurations.

This view provides an interactive form for testing all layout options:
- Fixed properties (fixed_sidebar, fixed_header, fixed_footer)
- Responsive breakpoints (sidebar_expand)

View uses query parameters for stateless, shareable URL-based configuration.
"""

from django_filters.views import FilterView

from demo.models import Category, Product
from demo.tables import ProductTable
from mvp.integrations.django_tables.views import MVPTableViewMixin
from mvp.views import (
    MVPCreateView,
    MVPDeleteView,
    MVPDetailView,
    MVPHomeView,
    MVPTemplateView,
    MVPUpdateView,
)
from mvp.views.htmx import HtmxFormMixin
from mvp.views.list import MVPListViewMixin

from .forms import ProductForm


class DemoHomeView(MVPHomeView):
    landing_template_name = "demo/landing.html"
    dashboard_template_name = "demo/dashboard.html"


class DemoTemplateView(MVPTemplateView):
    def get_template_names(self):
        return [
            f"demo/{self.template_name}",
            self.template_name,
        ]

    def get_breadcrumbs(self):
        return [{"text": "Home", "href": "/"}, {"text": self.page_title}]


components_demo = DemoTemplateView.as_view(
    template_name="components.html", page_title="Components"
)
layout_demo = DemoTemplateView.as_view(
    template_name="layout.html", page_title="Layout Demo"
)
theme_customization_demo = DemoTemplateView.as_view(
    template_name="theme_customization.html", page_title="Theme Customization"
)
E400 = DemoTemplateView.as_view(template_name="400.html")
E403 = DemoTemplateView.as_view(template_name="403.html")
E404 = DemoTemplateView.as_view(template_name="404.html")
E500 = DemoTemplateView.as_view(template_name="500.html")


class ProductListView(MVPListViewMixin, FilterView):
    """
    Demo page showing a list view of Products.

    User Story 1: Viewing Product List Page

    Features:
        - List of products with name and price
        - Bootstrap 5 responsive styling
        - Layout configuration via query parameters

    Template: mvp/list_view.html
    URL Pattern: /list-view/
    """

    model = Product
    create_form_class = ProductForm
    has_create_permission = True
    page_subtitle = "Check out our amazing products!"
    list_item_template = "cards/product_card.html"
    grid = {"cols": 1, "md": 2, "xl": 3, "gap": 2}
    paginate_by = 10
    filterset_fields = ["name", "price"]
    search_fields = ["name", "description"]
    order_by = [
        ("name_asc", "Name (A-Z)", "name"),
        ("name_desc", "Name (Z-A)", "-name"),
        ("price_asc", "Price (Low to High)", "price"),
        ("price_desc", "Price (High to Low)", "-price"),
    ]


# ======== CRUD Views for Product model ========


class ProductCreateView(MVPCreateView):
    """
    Demo product creation form for MVPCreateView verification.

    Tests model form create view with auto-detection of form renderer
    and AdminLTE card-based layout integration.
    """

    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock", "status"]
    has_list_permission = True
    has_detail_permission = True
    has_update_permission = True


class ProductDetailView(MVPDetailView):
    """
    Demo product detail page for CRUDDirectoryMixin verification.

    Demonstrates permission-gated directory URLs: staff users see edit/delete
    buttons; read-only users do not. The list link is always visible.
    """

    model = Product
    directory = ["list", "detail", "update", "delete"]
    has_list_permission = True
    has_detail_permission = True

    def has_update_permission(self, user):
        return user.is_staff

    def has_delete_permission(self, user):
        return user.is_staff


class ProductUpdateView(MVPUpdateView):
    """
    Demo product edit form for MVPUpdateView verification.

    Tests model form edit view with pre-populated data, auto-detection
    of form renderer, and AdminLTE card-based layout integration.
    """

    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock", "status"]
    has_list_permission = True
    has_detail_permission = True
    has_delete_permission = True


class ProductDeleteView(MVPDeleteView):
    """
    Demo product delete confirmation view for MVPDeleteView verification.

    Tests model form delete view with auto-detection of form renderer
    and AdminLTE card-based layout integration.
    """

    model = Product
    has_list_permission = True


class ProductDeleteWithRelatedView(MVPDeleteView):
    """Delete confirmation that summarises cascade-deleted related records."""

    model = Product
    show_related_objects = True
    has_list_permission = True


class ProductDeleteWithConfirmView(MVPDeleteView):
    """Delete confirmation that requires the user to type the product name."""

    model = Product
    require_confirmation = True
    has_list_permission = True


# ======== HTMX Form Mixin Demo ========


class HtmxProductCreateView(HtmxFormMixin, MVPCreateView):
    """Demo view for HtmxFormMixin: create a product with htmx-powered form submission.

    The form only shows the ``name`` field for simplicity. On a valid htmx POST
    the success partial is swapped in; on an invalid htmx POST the form partial
    with validation errors is swapped in. Non-htmx submissions fall back to the
    standard redirect.

    Template: htmx_demo.html
    URL Pattern: /htmx-demo/
    """

    model = Product
    fields = ["name"]
    template_name = "htmx_demo.html"
    htmx_form_component = "demo.htmx-product-form"
    htmx_success_component = "demo.htmx-product-created"
    success_url = "list"
    page_title = "HTMX Form Demo"
    page_subtitle = "Partial form rendering with HtmxFormMixin"
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "HTMX Form Demo"}]
    has_list_permission = True

    def form_valid(self, form):
        """Fill in required Product fields not exposed in the demo form, then delegate."""
        import re
        import uuid

        instance = form.instance
        if not instance.slug:
            slug_base = re.sub(r"[^\w\s-]", "", instance.name.lower())
            slug_base = re.sub(r"[\s_-]+", "-", slug_base).strip("-")
            # Ensure uniqueness by appending a short timestamp if needed
            from django.utils import timezone

            instance.slug = f"{slug_base}-{int(timezone.now().timestamp())}"
        if not instance.sku:
            instance.sku = str(uuid.uuid4())[:8].upper()
        if not instance.description:
            instance.description = "(Demo product created via HTMX form)"
        if instance.price is None:
            instance.price = "0.00"
        if instance.category_id is None:
            demo_cat, _ = Category.objects.get_or_create(
                slug="htmx-demo",
                defaults={"name": "HTMX Demo"},
            )
            instance.category = demo_cat
        return super().form_valid(form)


class CategoryUpdateView(MVPUpdateView):
    """Demo category update view — no delete view registered (US4 verification).

    Used by E2E tests to verify the delete button is hidden when no delete
    view is configured (has_delete_permission defaults to False).
    """

    model = Category
    fields = ["name", "slug"]


class CategoryDeleteWithRelatedView(MVPDeleteView):
    """Delete confirmation for Category — shows cascade-deleted Products as related objects.

    Uses a low cap (3) to allow overflow testing without creating large datasets.
    """

    model = Category
    show_related_objects = True
    related_objects_max_per_group = 3
    success_url = "/"  # No category list URL; redirect to home after deletion
    has_list_permission = False  # no category list URL registered


# ==================== Addons ======================
# Additional views that support third-party packages


class DataTablesView(MVPTableViewMixin, FilterView):
    """Django Tables2 demo page showing Product table with sorting and pagination."""

    model = Product
    table_class = ProductTable
    paginate_by = 25
    search_fields = ["name", "description"]
    has_create_permission = True
    filterset_fields = ["name", "category__name", "price", "stock", "status"]
