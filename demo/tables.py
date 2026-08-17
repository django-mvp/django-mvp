"""Django-tables2 table definitions for Demo App."""

import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor

from demo.models import Product


class ProductTable(tables.Table):
    """Product table with Bootstrap 5 styling and ARIA compliance."""

    # A static footer label, so the demo shows the footer row pinned to the
    # bottom of the table area alongside the pinned heading (issue #254).
    name = tables.LinkColumn("product-update", args=[A("pk")], footer="Total")

    # Column configurations with Bootstrap 5 alignment classes
    price = tables.Column(attrs={"td": {"class": "text-end"}})
    stock = tables.Column(attrs={"td": {"class": "text-end"}})
    rating = tables.Column(attrs={"td": {"class": "text-end"}})
    status = tables.Column(attrs={"td": {"class": "text-center"}})
    priority = tables.Column(attrs={"td": {"class": "text-center"}})
    is_featured = tables.BooleanColumn(attrs={"td": {"class": "text-center"}})
    is_available = tables.BooleanColumn(attrs={"td": {"class": "text-center"}})
    short_description = tables.Column(verbose_name="Description")
    sku = tables.Column(verbose_name="SKU")

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap5-mvp.html"
        fields = (
            "name",
            "sku",
            "category",
            "short_description",
            "price",
            "stock",
            "rating",
            "status",
            "priority",
            "is_featured",
            "is_available",
            "tags",
            "barcode",
            "release_date",
            "created_at",
            "updated_at",
        )
        empty_text = "No products available. Run 'poetry run python manage.py generate_dummy_data' to create sample data."


class ColumnBehaviourTable(tables.Table):
    """One column per behaviour class documented in docs/styling.md, against
    data long enough to make each effect obvious (issue #255)."""

    sku = tables.Column(attrs={"td": {"class": "mvp-col-shrink"}})
    name = tables.Column(attrs={"td": {"class": "mvp-col-grow mvp-col-nowrap"}})
    short_description = tables.Column(
        verbose_name="Description",
        attrs={"td": {"class": "mvp-col-wrap mvp-col-max-md"}},
    )
    release_date = tables.Column(attrs={"td": {"class": "mvp-col-nowrap"}})

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap5-mvp.html"
        fields = ("sku", "name", "short_description", "release_date")
        empty_text = "No products available. Run 'poetry run python manage.py generate_dummy_data' to create sample data."
