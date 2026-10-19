"""Tests for the filters a list page's filterset declares its search and sort with.

Source: mvp/filters.py
"""

import django_filters
import pytest
from django.core.paginator import Paginator
from django.db.models.functions import Lower

from demo.models import Category, Product
from mvp.filters import SearchFilter, SortFilter
from tests.factories import CategoryFactory, ProductFactory


class ProductSearch(django_filters.FilterSet):
    q = SearchFilter(fields=["name", "description"])

    class Meta:
        model = Product
        fields: list[str] = []


class CategorySearch(django_filters.FilterSet):
    q = SearchFilter(fields=["name", "products__name"])

    class Meta:
        model = Category
        fields: list[str] = []


class ProductSort(django_filters.FilterSet):
    o = SortFilter(
        options=[
            ("name", "Name", Lower("name")),
            ("-name", "Name, reversed", "-name"),
            ("name_then_pk", "Name, newest first", [Lower("name"), "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields: list[str] = []


def names(filterset):
    return sorted(filterset.qs.values_list("name", flat=True))


@pytest.mark.django_db
class TestSearchFilter:
    def test_a_word_in_any_named_field_matches(self):
        ProductFactory(name="Alpha", description="")
        ProductFactory(name="Beta", description="has alpha inside")
        ProductFactory(name="Gamma", description="")

        filterset = ProductSearch({"q": "alpha"}, queryset=Product.objects.all())

        assert names(filterset) == ["Alpha", "Beta"]

    def test_any_word_of_the_term_matches(self):
        ProductFactory(name="Alpha", description="")
        ProductFactory(name="Beta", description="")
        ProductFactory(name="Gamma", description="")

        filterset = ProductSearch({"q": "alpha beta"}, queryset=Product.objects.all())

        assert names(filterset) == ["Alpha", "Beta"]

    def test_case_is_ignored(self):
        ProductFactory(name="Django Framework", description="")

        filterset = ProductSearch({"q": "DJANGO"}, queryset=Product.objects.all())

        assert names(filterset) == ["Django Framework"]

    def test_a_record_matching_in_two_fields_is_shown_once(self):
        ProductFactory(name="Python Widget", description="python tools")

        filterset = ProductSearch({"q": "python"}, queryset=Product.objects.all())

        assert filterset.qs.count() == 1

    def test_a_record_matching_across_a_join_is_shown_once(self):
        category = CategoryFactory(name="Tools")
        ProductFactory(name="Hammer one", category=category)
        ProductFactory(name="Hammer two", category=category)

        filterset = CategorySearch({"q": "hammer"}, queryset=Category.objects.all())

        assert list(filterset.qs) == [category]

    def test_only_the_first_ten_words_are_searched(self):
        ProductFactory(name="Alpha", description="")
        ProductFactory(name="Omega", description="")
        words = ["alpha", *[f"w{i}" for i in range(9)], "omega"]

        filterset = ProductSearch(
            {"q": " ".join(words)}, queryset=Product.objects.all()
        )

        assert names(filterset) == ["Alpha"]

    def test_an_eleventh_word_alone_matches_nothing(self):
        ProductFactory(name="Omega", description="")
        words = [*[f"w{i}" for i in range(10)], "omega"]

        filterset = ProductSearch(
            {"q": " ".join(words)}, queryset=Product.objects.all()
        )

        assert names(filterset) == []

    def test_max_words_raises_the_limit(self):
        ProductFactory(name="Omega", description="")

        class LongSearch(ProductSearch):
            q = SearchFilter(fields=["name"], max_words=50)

        words = [*[f"w{i}" for i in range(10)], "omega"]
        filterset = LongSearch({"q": " ".join(words)}, queryset=Product.objects.all())

        assert names(filterset) == ["Omega"]

    @pytest.mark.parametrize("term", ["", "   "])
    def test_an_empty_term_narrows_nothing(self, term):
        ProductFactory(name="Alpha", description="")
        ProductFactory(name="Beta", description="")

        filterset = ProductSearch({"q": term}, queryset=Product.objects.all())

        assert names(filterset) == ["Alpha", "Beta"]

    def test_no_fields_narrows_nothing(self):
        ProductFactory(name="Alpha", description="")
        ProductFactory(name="Beta", description="")

        class NoFields(ProductSearch):
            q = SearchFilter()

        filterset = NoFields({"q": "alpha"}, queryset=Product.objects.all())

        assert names(filterset) == ["Alpha", "Beta"]

    def test_it_has_a_label_without_being_given_one(self):
        assert SearchFilter(fields=["name"]).label is not None

    def test_a_label_it_is_given_is_kept(self):
        assert SearchFilter(fields=["name"], label="Find").label == "Find"


@pytest.mark.django_db
class TestSortFilter:
    def test_an_option_orders_by_its_column(self):
        ProductFactory(name="Beta")
        ProductFactory(name="alpha")
        ProductFactory(name="Gamma")

        filterset = ProductSort({"o": "name"}, queryset=Product.objects.all())

        assert [p.name for p in filterset.qs] == ["alpha", "Beta", "Gamma"]

    def test_the_key_need_not_name_the_column(self):
        ProductFactory(name="Beta")
        ProductFactory(name="Alpha")

        filterset = ProductSort({"o": "-name"}, queryset=Product.objects.all())

        assert [p.name for p in filterset.qs] == ["Beta", "Alpha"]

    def test_later_columns_decide_ties_so_each_record_is_on_exactly_one_page(self):
        tied = [ProductFactory(name="Same") for _ in range(5)]
        ProductFactory(name="After")

        filterset = ProductSort(
            {"o": "name_then_pk"}, queryset=Product.objects.all()
        )
        paginator = Paginator(filterset.qs, 3)
        seen = [p.pk for n in paginator.page_range for p in paginator.page(n)]

        assert sorted(seen) == sorted(Product.objects.values_list("pk", flat=True))
        assert seen[1:] == [p.pk for p in reversed(tied)]

    def test_an_unknown_key_is_invalid_for_the_field(self):
        filterset = ProductSort({"o": "price"}, queryset=Product.objects.all())

        assert filterset.form.has_error("o", code="invalid_choice")

    def test_an_unknown_key_leaves_the_queryset_unordered_by_it(self):
        ProductFactory(name="Beta")
        ProductFactory(name="Alpha")
        default = list(Product.objects.all())

        filterset = ProductSort({"o": "name; drop"}, queryset=Product.objects.all())

        assert list(filterset.qs) == default
        assert filterset.qs.query.order_by == Product.objects.all().query.order_by

    def test_it_has_a_label_without_being_given_one(self):
        assert SortFilter(options=[("name", "Name", "name")]).label is not None

    def test_it_offers_no_empty_choice(self):
        filterset = ProductSort(queryset=Product.objects.all())

        keys = [key for key, _label in filterset.form.fields["o"].choices]
        assert keys == ["name", "-name", "name_then_pk"]
