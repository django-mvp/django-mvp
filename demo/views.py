"""
Demo views: the concrete views behind the demo site's pages.

Most of these instantiate a packaged django-mvp view directly (MVPListView,
MVPDetailView, MVPCreateView, …) to show what a project gets with no
customization. A few, like ``layout_demo`` and ``theme_customization_demo``,
are plain ``DemoTemplateView`` instances that render a static demo page.
"""

from django.forms import modelformset_factory
from django.http import Http404
from django_filters.views import FilterView

from demo.component_docs import COMPONENTS, COMPONENTS_BY_SLUG
from demo.models import Article, Category, OrderLine, Product
from demo.tables import ProductTable
from mvp.integrations.django_tables.views import MVPTableViewMixin
from mvp.views import (
    MVPCreateView,
    MVPDeleteView,
    MVPDetailView,
    MVPHomeView,
    MVPInlineUpdateView,
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


class ComponentIndexView(DemoTemplateView):
    """Landing page for the component documentation: a card per component."""

    template_name = "components/index.html"
    page_title = "Components"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["components"] = COMPONENTS
        return context


class ComponentDocView(DemoTemplateView):
    """Render a single component's documentation page from its slug.

    Templates live at ``demo/components/<slug>.html``. The slug must be a known
    component; anything else is a 404.
    """

    def setup(self, request, *args, slug=None, **kwargs):
        super().setup(request, *args, **kwargs)
        self.component = COMPONENTS_BY_SLUG.get(slug)
        if self.component is None:
            raise Http404(f"Unknown component: {slug!r}")
        self.template_name = f"components/{slug}.html"
        self.page_title = self.component.label

    def get_breadcrumbs(self):
        return [
            {"text": "Home", "href": "/"},
            {"text": "Components", "href": "/components/"},
            {"text": self.component.label},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["components"] = COMPONENTS
        context["component"] = self.component
        if self.component.slug == "formset":
            # <c-form.formset> needs a real, bound formset — the standalone case
            # (no parent record, unlike the inline formset in the worked example).
            OrderLineFormSet = modelformset_factory(
                OrderLine, fields=["product", "quantity"], extra=2
            )
            context["formset"] = OrderLineFormSet(queryset=OrderLine.objects.none())
        return context


components_demo = ComponentIndexView.as_view()
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
    show_create_action = True
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
    show_list_action = True
    show_detail_action = True
    show_update_action = True


class ProductDetailView(MVPDetailView):
    """
    Demo product detail page that supplies its own body.

    The edit and delete buttons come from the packaged template and are gated on the
    flags below, so staff users see them and read-only users do not. Hiding a button
    is all these flags do: this demo leaves the update and delete views open so the
    flows can be browsed without an account. A real project puts an access mixin on
    those views as well — see "Action links are not access control" in docs/views.md.
    Only demo/product_detail.html's page.content block is written by hand.
    """

    model = Product
    show_list_action = True
    show_detail_action = True

    def show_update_action(self, user):
        return user.is_staff

    def show_delete_action(self, user):
        return user.is_staff


class ArticleDetailView(MVPDetailView):
    """
    Demo article detail page with no template override at all.

    Shows what MVPDetailView gives a project for free: breadcrumbs, the object's
    own title as the heading, and an empty body waiting to be filled.
    """

    model = Article


class ProductUpdateView(MVPUpdateView):
    """
    Demo product edit form for MVPUpdateView verification.

    Tests model form edit view with pre-populated data, auto-detection
    of form renderer, and AdminLTE card-based layout integration.
    """

    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock", "status"]
    show_list_action = True
    show_detail_action = True
    show_delete_action = True


class ProductOrderLinesView(MVPInlineUpdateView):
    """A product and its order lines, validated and saved together.

    The worked example docs/formsets.md walks through: one view, no template
    markup for the rows, no code to build, validate or save the set.
    """

    model = Product
    fields = ["name", "category"]
    inline_model = OrderLine
    inline_fields = ["quantity"]
    inline_extra = 1
    success_url = "list"
    show_list_action = True
    show_detail_action = True


class ProductDeleteView(MVPDeleteView):
    """
    Demo product delete confirmation view for MVPDeleteView verification.

    Tests model form delete view with auto-detection of form renderer
    and AdminLTE card-based layout integration.
    """

    model = Product
    show_list_action = True


class ProductDeleteWithRelatedView(MVPDeleteView):
    """Delete confirmation that summarises cascade-deleted related records."""

    model = Product
    show_related_objects = True
    show_list_action = True


class ProductDeleteWithConfirmView(MVPDeleteView):
    """Delete confirmation that requires the user to type the product name."""

    model = Product
    require_confirmation = True
    show_list_action = True


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
    show_list_action = True

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
    view is configured (show_delete_action defaults to False).
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
    show_list_action = False  # no category list URL registered


# ==================== Addons ======================
# Additional views that support third-party packages


class DataTablesView(MVPTableViewMixin, FilterView):
    """Django Tables2 demo page showing Product table with sorting and pagination."""

    model = Product
    table_class = ProductTable
    paginate_by = 25
    search_fields = ["name", "description"]
    show_create_action = True
    filterset_fields = ["name", "category__name", "price", "stock", "status"]
