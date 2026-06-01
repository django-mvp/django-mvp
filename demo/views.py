"""
Demo views for testing AdminLTE layout configurations.

This view provides an interactive form for testing all layout options:
- Fixed properties (fixed_sidebar, fixed_header, fixed_footer)
- Responsive breakpoints (sidebar_expand)

View uses query parameters for stateless, shareable URL-based configuration.
"""

from django_filters.views import FilterView

from demo.forms import ContactForm
from demo.models import Category, Product
from demo.tables import ProductTable
from mvp.views import (
    MVPCreateView,
    MVPDeleteView,
    MVPDetailView,
    MVPFormView,
    MVPTemplateView,
    MVPUpdateView,
)
from mvp.views.htmx import HtmxFormMixin
from mvp.views.list import MVPListViewMixin
from mvp.views.table import MVPTableViewMixin

from .forms import ProductForm


class MVPDemoView(MVPTemplateView):
    """Base TemplateView with LayoutConfigMixin for layout configuration support."""

    page_title = "MVP Demo"
    page_subtitle = "Base template view for MVP demo pages"
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "MVP Demo"}]


class ErrorPagePreviewView(MVPTemplateView):
    """Preview any error page template without triggering a real error.

    Wire via: ErrorPagePreviewView.as_view(template_name="NNN.html")
    For the 500 preview, also pass extra_context={"support_email": ...}.
    """

    page_title = "Error Page Preview"
    page_subtitle = "Preview error page templates without triggering real errors"
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "Error Page Preview"}]


class FullShellDemoView(MVPTemplateView):
    """Demo page that enforces the canonical full app shell configuration.

    This view provides a stable visual verification target for US1 contracts.
    It sets the expected shell attributes unless explicitly overridden by query params.
    """

    template_name = "demo/full_shell.html"
    page_title = "Full Shell Demo"
    page_subtitle = (
        "Stable visual verification target for US1 shell integration contracts"
    )
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "Full Shell Demo"}]

    def get_context_data(self, **kwargs):
        """Set default shell configuration for fixed header/sidebar and collapsible nav."""
        context = super().get_context_data(**kwargs)
        context["fixed_sidebar"] = self.request.GET.get("fixed_sidebar", "on") == "on"
        context["fixed_header"] = self.request.GET.get("fixed_header", "on") == "on"
        context["sidebar_collapsible"] = (
            self.request.GET.get("sidebar_collapsible", "on") == "on"
        )
        context["sidebar_expand"] = self.request.GET.get("sidebar_expand", "lg")
        context["breakpoint"] = context["sidebar_expand"]
        return context


class LayoutDemoView(MVPTemplateView):
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
    page_title = "Layout Configuration"
    page_subtitle = """This page demonstrates all AdminLTE layout configuration options
      in a single interactive view. Use the configuration form on the right
      to toggle different layout behaviors."""
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "Layout Demo"}]


class NavbarWidgetsView(MVPTemplateView):
    """
    Navbar widgets demonstration page.

    Shows all navbar widget components with usage examples and documentation.
    Widgets are displayed in the navbar header (top right).

    Template: demo/navbar_widgets.html
    URL Pattern: /widgets/
    """

    template_name = "demo/navbar_widgets.html"
    page_title = "Navbar Widgets Demo"
    page_subtitle = (
        "Interactive demonstration of all navbar widget components with usage examples"
    )
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "Navbar Widgets"}]

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


class PageLayoutDemoView(MVPTemplateView):
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
    page_title = "Page Layout Demo"
    page_subtitle = "Test all inner layout options including fixed positioning and responsive breakpoints"
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "Page Layout Demo"}]


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
    create_form_class = ProductForm
    has_create_permission = True
    page_caption = "Browse"
    page_subtitle = """Check out our amazing products!"""
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.create_form_class:
            context["create_form"] = self.create_form_class()
        return context


class DataTablesView(MVPTableViewMixin, FilterView):
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
    has_create_permission = True
    filterset_fields = ["name", "category__name", "price", "stock", "status"]


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


class CategoryDeleteWithRelatedView(MVPDeleteView):
    """Delete confirmation for Category — shows cascade-deleted Products as related objects.

    Uses a low cap (3) to allow overflow testing without creating large datasets.
    """

    model = Category
    show_related_objects = True
    related_objects_max_per_group = 3
    success_url = "/"  # No category list URL; redirect to home after deletion
    has_list_permission = False  # no category list URL registered


class ThemeCustomizationView(MVPTemplateView):
    """Live demo page showing how to override SCSS variables in a downstream project."""

    page_subtitle = "Overriding SCSS Variables in Your Project"
    page_title = "Theme Customization"
    template_name = "demo/scss_variables.html"
    breadcrumbs = [
        {"text": "Home", "href": "/"},
        {"text": "Theme Customization"},
    ]

    def get_page_context(self):
        context = super().get_page_context()
        context["caption"] = "Custom caption"
        return context


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
