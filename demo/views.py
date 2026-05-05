"""
Demo views for testing AdminLTE layout configurations.

This view provides an interactive form for testing all layout options:
- Fixed properties (fixed_sidebar, fixed_header, fixed_footer)
- Responsive breakpoints (sidebar_expand)

View uses query parameters for stateless, shareable URL-based configuration.
"""

from django.views.generic import TemplateView
from django_filters.views import FilterView

from demo.forms import ContactForm
from demo.models import Category, Product
from demo.tables import ProductTable
from mvp.views import (
    MVPCreateView,
    MVPDeleteView,
    MVPDetailView,
    MVPFormView,
    MVPUpdateView,
)
from mvp.views.list import MVPListViewMixin
from mvp.views.table import MVPTableView


class MVPDemoView(TemplateView):
    """Base TemplateView with LayoutConfigMixin for layout configuration support."""

    pass


class FullShellDemoView(TemplateView):
    """Demo page that enforces the canonical full app shell configuration.

    This view provides a stable visual verification target for US1 contracts.
    It sets the expected shell attributes unless explicitly overridden by query params.
    """

    template_name = "demo/full_shell.html"

    def get_context_data(self, **kwargs):
        """Set default shell configuration for fixed header/sidebar and collapsible nav."""
        context = super().get_context_data(**kwargs)
        context["fixed_sidebar"] = self.request.GET.get("fixed_sidebar", "on") == "on"
        context["fixed_header"] = self.request.GET.get("fixed_header", "on") == "on"
        context["sidebar_collapsible"] = self.request.GET.get("sidebar_collapsible", "on") == "on"
        context["sidebar_expand"] = self.request.GET.get("sidebar_expand", "lg")
        context["breakpoint"] = context["sidebar_expand"]
        return context


class LayoutDemoView(TemplateView):
    """
    Unified layout demo view for testing all AdminLTE layout configurations.

    User Story 4: Interactive Layout Configuration Demo Page

    Features:
        - Interactive configuration form (right sidebar)
        - Real-time layout updates via query parameters
        - URL-based configuration (shareable links)
        - Bootstrap responsive breakpoint testing

    Template: demo/layout_demo.html
    URL Pattern: /layout/
    """

    template_name = "demo/layout_demo.html"


class NavbarWidgetsView(TemplateView):
    """
    Navbar widgets demonstration page.

    Shows all navbar widget components with usage examples and documentation.
    Widgets are displayed in the navbar header (top right).

    Template: demo/navbar_widgets.html
    URL Pattern: /widgets/
    """

    template_name = "demo/navbar_widgets.html"

    def get_context_data(self, **kwargs):
        """Add navbar widget sample data to context."""
        context = super().get_context_data(**kwargs)

        # Sample notifications data
        notifications = [
            {"text": "You have 3 new friend requests", "time": "2 mins ago"},
            {"text": "Server maintenance scheduled", "time": "10 mins ago"},
            {"text": "Your password expires soon", "time": "1 hour ago"},
            {"text": "New comment on your post", "time": "3 hours ago"},
            {"text": "Weekly report is ready", "time": "Yesterday"},
            {"text": "Backup completed successfully", "time": "2 days ago"},
            {"text": "System update available", "time": "3 days ago"},
        ]

        context["notifications_count"] = len(notifications)
        context["notifications"] = notifications

        return context


class PageLayoutDemoView(TemplateView):
    """
    Inner layout demonstration page.

    Interactive form for testing all inner layout options:
    - Fixed properties (fixed_header, fixed_footer, fixed_sidebar)
    - Responsive breakpoints (sidebar_expand)
    - Initial sidebar state (collapsed)
    - Layout variants (6-char layout codes)

    Template: demo/page_layout.html
    URL Pattern: /page-layout/
    """

    template_name = "demo/page_layout.html"


class ListViewDemo(MVPListViewMixin, FilterView):
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
    list_item_template = "cards/product_card.html"
    grid = {"cols": 1, "md": 2, "xl": 2, "gap": 2}
    paginate_by = 12
    filterset_fields = ["name", "price"]
    search_fields = ["name", "description"]
    order_by = [
        ("name", "Name (A-Z)"),
        ("-name", "Name (Z-A)"),
        ("price", "Price (Low to High)"),
        ("-price", "Price (High to Low)"),
    ]


class DataTablesView(MVPTableView):
    """Django Tables2 demo page showing Product table with sorting and pagination.

    User Story 2: Viewing DataTables Demo Page

    Features:
        - Product data table with 18 columns
        - Bootstrap 5 responsive styling
        - Sortable columns
        - Pagination (25 items per page)
        - Empty state message
        - Layout configuration via query parameters

    Template: demo/datatables_demo.html
    URL Pattern: /datatables-demo/
    """

    model = Product
    icon = "table"
    table_class = ProductTable
    paginate_by = 25
    search_fields = ["name", "description"]


class ContactFormView(MVPFormView):
    """
    Demo contact form for MVPFormView verification.

    Tests auto-detection of form renderer (crispy → formset → django)
    and AdminLTE card-based layout integration.
    """

    form_class = ContactForm
    page_title = "Contact Form (Auto Renderer)"
    success_url = "/contact/success/"

    def form_valid(self, form):
        """Handle successful form submission (demo only - just redirects)."""
        # In a real app, this would send email or save to database
        return super().form_valid(form)


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


class CategoryUpdateView(MVPUpdateView):
    """Demo category update view — no delete view registered (US4 verification).

    Used by E2E tests to verify the delete button is hidden when no delete
    view is configured (has_delete_permission defaults to False).
    """

    model = Category
    fields = ["name", "slug"]
    has_list_permission = False  # no category list view wired in demo
    has_detail_permission = False  # no category detail view wired in demo
    has_delete_permission = False  # intentionally no delete view — verifies US4
