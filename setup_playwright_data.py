"""Setup script for Playwright verification data."""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

from django.contrib.auth import get_user_model

from demo.models import Category, Product

User = get_user_model()

cat, _ = Category.objects.get_or_create(name="Test", slug="test")
prod, created = Product.objects.get_or_create(
    slug="test-product",
    defaults={
        "name": "Test Product",
        "category": cat,
        "description": "A test product",
        "price": "9.99",
        "stock": 10,
    },
)
print(f"Product pk: {prod.pk} created: {created}")

staff, _ = User.objects.get_or_create(username="staffuser")
staff.is_staff = True
staff.is_active = True
staff.set_password("testpass123")
staff.save()

regular, _ = User.objects.get_or_create(username="regularuser")
regular.is_staff = False
regular.is_active = True
regular.set_password("testpass123")
regular.save()

print(f"Staff pk: {staff.pk}, Regular pk: {regular.pk}")
print(f"Detail URL: /products/{prod.pk}/")
