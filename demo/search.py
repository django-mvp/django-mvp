"""The demo's search kinds: products, articles and the component pages."""

from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from mvp.search import ModelKind, Result

from .component_docs import COMPONENTS
from .models import Article, Product


class ProductKind(ModelKind):
    """Search the products."""

    name = "products"
    label = _("Products")
    icon = "box-seam"
    description = _("Products in the catalogue")
    model = Product

    def get_queryset(self, request: HttpRequest) -> QuerySet[Product]:
        """Show every product."""
        return Product.objects.all()

    def passage(self, obj: Product) -> str:
        """Show the product's short description."""
        return obj.short_description or ""


class ArticleKind(ModelKind):
    """Search the articles, leaving drafts to staff."""

    name = "articles"
    label = _("Articles")
    icon = "book"
    description = _("Articles and posts")
    model = Article

    def get_queryset(self, request: HttpRequest) -> QuerySet[Article]:
        """Show published articles, and drafts too when the user is staff."""
        articles = Article.objects.all()
        if request.user.is_staff:
            return articles
        return articles.exclude(status="draft")

    def url(self, obj: Article) -> str:
        """Link to the article's detail page."""
        return reverse("article-detail", kwargs={"pk": obj.pk})

    def passage(self, obj: Article) -> str:
        """Show the article's excerpt."""
        return obj.excerpt


def find_components(query: str, request: HttpRequest) -> list[Result]:
    """Find the component pages whose name or description has the query.

    Args:
        query: The cleaned query.
        request: The request the search is for.

    Returns:
        One result per matching component page, in the order they are listed.
    """
    needle = query.casefold()
    return [
        Result(
            title=str(component.label),
            url=reverse("component-doc", kwargs={"slug": component.slug}),
            where=str(_("Components")),
            passage=component.description,
        )
        for component in COMPONENTS
        if needle in component.label.casefold()
        or needle in component.description.casefold()
    ]
