"""
Demo views for testing AdminLTE layout configurations.

This view provides an interactive form for testing all layout options:
- Fixed properties (fixed_sidebar, fixed_header, fixed_footer)
- Responsive breakpoints (sidebar_expand)

View uses query parameters for stateless, shareable URL-based configuration.
"""

from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from django_tables2 import SingleTableView

from demo.forms import ContactForm
from demo.models import Product
from demo.tables import ProductTable
from mvp.views import (
    MVPCreateView,
    MVPFormView,
    MVPListViewMixin,
    MVPUpdateView,
    PageModifierMixin,
)


class LayoutConfigMixin:
    """
    Mixin that inspects request query parameters for layout configuration.

    Provides standardized layout configuration handling across all demo views.
    Configuration can be controlled via query parameters, allowing shareable URLs
    and dynamic layout switching via the demo sidebar.

    Query Parameters:
        fixed_sidebar (str): 'on' if outer sidebar should be fixed
        fixed_header (str): 'on' if outer header should be fixed
        fixed_footer (str): 'on' if outer footer should be fixed
        sidebar_collapsible (str): 'on' if outer sidebar should be collapsible
        collapsed (str): 'on' if outer sidebar should start collapsed
        fill (str): 'on' if app-wrapper should use fill mode
        sidebar_expand (str): Bootstrap breakpoint for outer sidebar (sm, md, lg, xl, xxl)

        page_fixed_sidebar (str): 'on' if inner sidebar should be sticky
        page_fixed_header (str): 'on' if inner toolbar should be sticky
        page_fixed_footer (str): 'on' if inner footer should be sticky
        page_collapsed (str): 'on' if inner sidebar should start collapsed
        page_sidebar_expand (str): Bootstrap breakpoint for inner sidebar (sm, md, lg, xl, xxl)
        page_layout (str): 6-char layout code (e.g., 'tt-ms-ff')

    Context Variables Added:
        All parsed boolean and string values from query parameters above
    """

    VALID_BREAKPOINTS = ["sm", "md", "lg", "xl", "xxl"]

    def get_context_data(self, **kwargs):
        """Add layout configuration to context from request query parameters."""
        context = super().get_context_data(**kwargs)

        # Outer layout configuration (app-wrapper level)
        context["fixed_sidebar"] = self.request.GET.get("fixed_sidebar") == "on"
        context["fixed_header"] = self.request.GET.get("fixed_header") == "on"
        context["fixed_footer"] = self.request.GET.get("fixed_footer") == "on"
        context["sidebar_collapsible"] = (
            self.request.GET.get("sidebar_collapsible") == "on"
        )
        context["collapsed"] = self.request.GET.get("collapsed") == "on"
        context["fill"] = self.request.GET.get("fill") == "on"

        # Parse outer sidebar breakpoint with fallback to 'lg'
        sidebar_expand = self.request.GET.get(
            "sidebar_expand", self.request.GET.get("breakpoint", "lg")
        )
        if sidebar_expand not in self.VALID_BREAKPOINTS:
            sidebar_expand = "lg"
        context["sidebar_expand"] = sidebar_expand
        context["breakpoint"] = sidebar_expand  # For compatibility
        context["breakpoints"] = self.VALID_BREAKPOINTS

        # Inner layout configuration (page-layout level)
        context["page_fixed_sidebar"] = (
            self.request.GET.get("page_fixed_sidebar") == "on"
        )
        context["page_fixed_header"] = self.request.GET.get("page_fixed_header") == "on"
        context["page_fixed_footer"] = self.request.GET.get("page_fixed_footer") == "on"
        context["page_collapsed"] = self.request.GET.get("page_collapsed") == "on"

        # Parse inner sidebar breakpoint with fallback to 'lg'
        page_sidebar_expand = self.request.GET.get("page_sidebar_expand", "lg")
        if page_sidebar_expand not in self.VALID_BREAKPOINTS:
            page_sidebar_expand = "lg"
        context["page_sidebar_expand"] = page_sidebar_expand

        # Parse page layout code (e.g., 'tt-ms-ff')
        context["page_layout"] = self.request.GET.get("page_layout", "")
        return context


class MVPDemoView(LayoutConfigMixin, TemplateView):
    """Base TemplateView with LayoutConfigMixin for layout configuration support."""

    pass


class LayoutDemoView(LayoutConfigMixin, TemplateView):
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


class NavbarWidgetsView(LayoutConfigMixin, TemplateView):
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


class PageLayoutDemoView(LayoutConfigMixin, TemplateView):
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


class MinimalListViewDemo(
    LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, ListView
):
    """
    Minimal list view demo showing the simplest configuration (T011 - User Story 1).

    Features:
        - Only model and list_item_template specified
        - Page title auto-generated from model verbose_name_plural
        - Default single-column grid layout
        - Pagination with entry counts
        - No search, ordering, or filtering

    This demonstrates SC-001: Fully functional list view with under 10 lines of code.

    Also used for grid configuration demos (T015-T018 - User Story 2) by overriding
    the grid attribute via .as_view(grid={...}) in URL patterns.

    Template: mvp/list_view.html
    URL Patterns:
        - /list-view/minimal/ (default single column)
        - /list-view/grid/1col/ (explicit single column)
        - /list-view/grid/2col/ (responsive 2-column)
        - /list-view/grid/3col/ (responsive 3-column)
        - /list-view/grid/responsive/ (fully responsive multi-column)
    """

    model = Product
    template_name = "mvp/list_view.html"
    list_item_template = "cards/product_card.html"
    paginate_by = 12


class BasicListViewDemo(
    LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, ListView
):
    """
    Basic list view demo with search and ordering (T025 - User Stories 3 & 4).

    Features:
        - Search across name and description fields (multi-word OR matching)
        - Ordering dropdown with multiple sort options
        - 2-column responsive grid layout
        - Pagination with entry counts
        - No advanced filtering (see ListViewDemo for FilterView example)

    This demonstrates:
        - User Story 3: Search functionality (FR-001, FR-019, FR-020)
        - User Story 4: Ordering/sorting controls (FR-002, FR-022, FR-023, FR-024)

    Template: mvp/list_view.html
    URL Pattern: /list-view/basic/
    """

    model = Product
    template_name = "mvp/list_view.html"
    list_item_template = "cards/product_card.html"
    grid = {"cols": 1, "md": 2}
    paginate_by = 12
    search_fields = ["name", "description"]
    order_by = [
        ("name", "Name (A-Z)"),
        ("-name", "Name (Z-A)"),
        ("price", "Price (Low to High)"),
        ("-price", "Price (High to Low)"),
        ("created", "Oldest First"),
        ("-created", "Newest First"),
    ]


class ListViewDemo(LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, FilterView):
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
    template_name = "mvp/list_view.html"
    list_item_template = "cards/product_card.html"
    page = {"layout": "ts-ms-ff"}
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


class DataTablesView(LayoutConfigMixin, SingleTableView):
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
    table_class = ProductTable
    template_name = "demo/datatables_demo.html"
    paginate_by = 25


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


class ProductCreateView(MVPCreateView):
    """
    Demo product creation form for MVPCreateView verification.

    Tests model form create view with auto-detection of form renderer
    and AdminLTE card-based layout integration.
    """

    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock", "status"]
    page_title = "Create Product (Model Form)"
    success_url = "/products/"

    def form_valid(self, form):
        """Handle successful form submission."""
        # In a real app, you might add flash messages here
        return super().form_valid(form)


class ProductUpdateView(MVPUpdateView):
    """
    Demo product edit form for MVPUpdateView verification.

    Tests model form edit view with pre-populated data, auto-detection
    of form renderer, and AdminLTE card-based layout integration.
    """

    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock", "status"]
    page_title = "Edit Product (Model Form)"
    success_url = "/products/"

    def form_valid(self, form):
        """Handle successful form submission."""
        # In a real app, you might add flash messages here
        return super().form_valid(form)


class ExplicitRendererDemo(MVPFormView):
    """
    Demo showing explicit form_renderer configuration.

    This view demonstrates how to override the auto-detection and
    force a specific renderer (Django's default in this case).
    Useful when you want consistent rendering regardless of which
    form libraries are installed.
    """

    form_class = ContactForm
    page_title = "Explicit Renderer (Django)"
    success_url = "/contact/success/"
    form_renderer = "django"  # Force Django renderer, ignore crispy/formset

    def form_valid(self, form):
        """Handle successful form submission."""
        return super().form_valid(form)
