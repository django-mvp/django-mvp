"""Django-tables2 table definitions for Demo App."""

import django_tables2 as tables

from demo.models import Product


class ProductTable(tables.Table):
    """Product table with Bootstrap 5 styling and ARIA compliance."""

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
        """Meta configuration for ProductTable."""

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
        attrs = {
            "class": "table table-striped table-hover",
        }
        empty_text = (
            "No products available. Run 'poetry run python manage.py generate_dummy_data' "
            "to create sample data."
        )
