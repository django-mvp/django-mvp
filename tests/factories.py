"""factory_boy factories for the demo models.

One factory per model. Variants are expressed by overriding fields at the call
site — `ProductFactory(category=None)` — never by subclassing a factory.

Fixtures in `conftest.py` are thin wrappers over these. A one-off variation
needs no fixture: call the factory inline in the test.
"""

import factory
from factory.django import DjangoModelFactory

from demo.models import Article, Category, OrderLine, Product, Task


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = "A category for tests"


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    category = factory.SubFactory(CategoryFactory)
    description = "A product for tests"
    price = "9.99"
    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")


class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    title = factory.Sequence(lambda n: f"Article {n}")
    slug = factory.Sequence(lambda n: f"article-{n}")
    author = "Test Author"
    excerpt = "A short excerpt"
    content = "Full article content body"


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    description = "A task for tests"


class OrderLineFactory(DjangoModelFactory):
    class Meta:
        model = OrderLine

    product = factory.SubFactory(ProductFactory)
    quantity = 1
