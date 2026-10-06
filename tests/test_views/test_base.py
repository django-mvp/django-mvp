"""Tests for BaseTemplateNameMixin and PageMixin in mvp.views.base."""

import pytest
from django import forms as django_forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models as db_models
from django.test import RequestFactory
from django.utils.safestring import SafeString, mark_safe
from django.views.generic import TemplateView

from demo.models import Category, Product
from mvp.views.base import BaseTemplateNameMixin, ModelInfoMixin, PageMixin
from mvp.views.extra import MVPHomeView


class ConcreteTemplateView(BaseTemplateNameMixin, TemplateView):
    """Concrete subclass with base_template_name set — happy-path fixture."""

    base_template_name = "base.html"
    template_name = "specific.html"


class BareTemplateNameMixin(BaseTemplateNameMixin, TemplateView):
    """Subclass that deliberately leaves base_template_name as None (error case)."""

    template_name = "specific.html"


class NoTemplateNameView(BaseTemplateNameMixin, TemplateView):
    """base_template_name set, template_name unset — MVPFormView's own shape.

    Django's TemplateResponseMixin.get_template_names() raises when
    template_name is None, unlike the model-based SingleObject/MultipleObject
    variants CreateView/UpdateView/DetailView build on, which degrade to a
    model-derived name instead. Regression for #311: this is the shape every
    plain MVPFormView subclass is in, and nothing had ever rendered one.
    """

    base_template_name = "base.html"


class ConcretePage(PageMixin, TemplateView):
    """Minimal concrete PageMixin subclass with no overrides."""

    template_name = "page.html"


class TestBaseTemplateNameMixin:
    def test_raises_when_base_template_name_is_none(self):
        view = BareTemplateNameMixin()
        view.request = None  # not needed for template resolution
        with pytest.raises(ImproperlyConfigured):
            view.get_template_names()

    def test_returns_specific_template_first(self):
        view = ConcreteTemplateView()
        names = view.get_template_names()
        assert names[0] == "specific.html"

    def test_returns_base_template_last(self):
        view = ConcreteTemplateView()
        names = view.get_template_names()
        assert names[-1] == "base.html"

    def test_returns_base_template_alone_when_no_template_name_is_set(self):
        view = NoTemplateNameView()
        assert view.get_template_names() == ["base.html"]


class TestPageMixinGetPageContext:
    def test_get_page_context_returns_dict_with_required_keys(self):
        view = ConcretePage()
        ctx = view.get_page_context()
        assert set(ctx.keys()) == {
            "title",
            "subtitle",
            "class",
            "breadcrumbs",
            "info",
            "info_actions",
        }

    def test_get_page_context_delegates_to_getters(self):
        view = ConcretePage()
        view.page_title = "Test"
        view.page_subtitle = "Sub"
        view.page_class = "extra"
        view.breadcrumbs = [{"text": "Home"}]
        ctx = view.get_page_context()
        assert ctx["title"] == "Test"
        assert ctx["subtitle"] == "Sub"
        assert ctx["breadcrumbs"] == [{"text": "Home"}]


class TestPageMixinPageInfo:
    def test_no_info_by_default(self):
        assert ConcretePage().get_page_info() == ""

    def test_no_actions_by_default(self):
        assert ConcretePage().get_page_info_actions() == []

    def test_attribute_reaches_the_page_context(self):
        view = ConcretePage()
        view.page_info = "What this page is for."
        assert view.get_page_context()["info"] == "What this page is for."

    def test_actions_attribute_reaches_the_page_context(self):
        view = ConcretePage()
        view.page_info_actions = [{"text": "Docs", "href": "/docs/"}]
        assert view.get_page_context()["info_actions"] == [
            {"text": "Docs", "href": "/docs/"}
        ]

    def test_override_supplies_rich_text(self):

        class RichInfoPage(ConcretePage):
            def get_page_info(self):
                return mark_safe("<p>Built at <strong>request time</strong>.</p>")

        ctx = RichInfoPage().get_page_context()
        assert ctx["info"] == "<p>Built at <strong>request time</strong>.</p>"
        assert isinstance(ctx["info"], SafeString)

    def test_override_supplies_actions(self):
        class ActionPage(ConcretePage):
            def get_page_info_actions(self):
                return [{"text": "Guide", "href": "/guide/"}]

        assert ActionPage().get_page_context()["info_actions"] == [
            {"text": "Guide", "href": "/guide/"}
        ]


@pytest.mark.django_db
class TestPageInfoRendersThroughARealPage:
    def _render(self, **attrs):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views import MVPTemplateView

        view = MVPTemplateView.as_view(template_name="page_view.html", **attrs)
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        return view(request).render().content.decode()

    def test_no_dialog_when_the_view_sets_no_info(self):
        assert "<dialog" not in self._render(page_title="Products")

    def test_dialog_carries_the_views_text(self):
        html = self._render(page_title="Products", page_info="What this page is for.")
        assert "<dialog" in html
        assert "What this page is for." in html

    def test_dialog_carries_the_views_actions(self):
        html = self._render(
            page_title="Products",
            page_info="Body",
            page_info_actions=[{"text": "Read the guide", "href": "/guide/"}],
        )
        assert 'href="/guide/"' in html
        assert "Read the guide" in html

    def test_the_title_block_carries_only_what_it_reads(self):
        html = self._render(page_title="Products")

        title_block = html[html.index('class="page-title') :]
        title_block = title_block[: title_block.index(">") + 1]
        assert "breadcrumbs" not in title_block
        assert "mvp-page" not in title_block


class TestPageMixinGetContextData:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_page_key_has_correct_shape(self):
        request = self.factory.get("/")
        view = ConcretePage()
        view.page_title = "Hello"
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        assert context["page"]["title"] == "Hello"
        assert "class" in context["page"]
        assert context["page"]["class"].startswith("mvp-page")


class _CustomVerboseModel(db_models.Model):
    """Stub with a custom verbose_name — unmanaged, no DB table."""

    class Meta:
        app_label = "demo"
        managed = False
        verbose_name = "custom item"
        verbose_name_plural = "custom items"


class _ProductForm(django_forms.ModelForm):
    """Minimal ModelForm bound to Product."""

    class Meta:
        model = Product
        fields = []


class _PlainForm(django_forms.Form):
    """Plain (non-Model) Form — used to verify silent skipping."""

    name = django_forms.CharField()


class TestModelInfoMixin:
    # --- US1: Four resolution strategies (T007–T011) -------------------------

    def test_resolves_from_model_attribute(self):
        class V(ModelInfoMixin):
            model = Product

        assert V().get_model_class() is Product

    def test_resolves_from_queryset(self):
        class V(ModelInfoMixin):
            def get_queryset(self):
                return Product.objects.all()

        assert V().get_model_class() is Product

    def test_resolves_from_form_class_attribute(self):
        class V(ModelInfoMixin):
            form_class = _ProductForm

        assert V().get_model_class() is Product

    def test_resolves_from_get_form_class(self):
        class V(ModelInfoMixin):
            def get_form_class(self):
                return _ProductForm

        assert V().get_model_class() is Product

    def test_resolves_from_object_instance(self):
        obj = Product.__new__(Product)

        class V(ModelInfoMixin):
            object = obj

        assert V().get_model_class() is Product

    # --- US1: Priority order (T012–T014) ------------------------------------

    def test_model_priority_over_queryset(self):
        class V(ModelInfoMixin):
            model = Category

            def get_queryset(self):
                return Product.objects.all()

        assert V().get_model_class() is Category

    def test_queryset_priority_over_form_class(self):
        class _CategoryForm(django_forms.ModelForm):
            class Meta:
                model = Category
                fields = []

        class V(ModelInfoMixin):
            form_class = _CategoryForm  # would resolve to Category...

            def get_queryset(self):
                return Product.objects.all()  # ...but queryset wins

        assert V().get_model_class() is Product

    def test_form_class_priority_over_object(self):
        obj = Category.__new__(Category)

        class V(ModelInfoMixin):
            form_class = _ProductForm  # form_class points to Product...
            object = obj  # ...instance is Category — form_class wins

        assert V().get_model_class() is Product

    # --- US4: Context shape (T015–T018) ------------------------------------

    def test_model_info_context_key_present(self):
        class V(ModelInfoMixin, TemplateView):
            model = Product
            template_name = "base.html"

        v = V()
        v.request = RequestFactory().get("/")
        v.kwargs = {}
        v.args = []
        assert "model_info" in v.get_context_data()

    def test_model_info_contains_all_four_fields(self):
        class V(ModelInfoMixin, TemplateView):
            model = Product
            template_name = "base.html"

        v = V()
        v.request = RequestFactory().get("/")
        v.kwargs = {}
        v.args = []
        info = v.get_context_data()["model_info"]
        assert {
            "verbose_name",
            "verbose_name_plural",
            "app_label",
            "model_name",
        } <= set(info.keys())

    def test_model_info_does_not_contain_model_class(self):
        class V(ModelInfoMixin, TemplateView):
            model = Product
            template_name = "base.html"

        v = V()
        v.request = RequestFactory().get("/")
        v.kwargs = {}
        v.args = []
        for value in v.get_context_data()["model_info"].values():
            assert not isinstance(value, type)

    def test_custom_verbose_name_appears_in_model_info(self):
        class V(ModelInfoMixin, TemplateView):
            model = _CustomVerboseModel
            template_name = "base.html"

        v = V()
        v.request = RequestFactory().get("/")
        v.kwargs = {}
        v.args = []
        assert v.get_context_data()["model_info"]["verbose_name"] == "custom item"

    # --- US1 edge cases: exception silencing (T021–T022) --------------------

    def test_get_queryset_exception_silenced(self):
        class V(ModelInfoMixin):
            form_class = _ProductForm  # fallback after queryset raises

            def get_queryset(self):
                raise RuntimeError("queryset exploded")

        assert V().get_model_class() is Product

    def test_get_form_class_exception_silenced(self):
        obj = Product.__new__(Product)

        class V(ModelInfoMixin):
            object = obj  # fallback after form_class raises

            def get_form_class(self):
                raise RuntimeError("form_class exploded")

        assert V().get_model_class() is Product

    # --- US2: Custom override point (T028–T029) -----------------------------

    def test_custom_get_model_class_override_used(self):
        class V(ModelInfoMixin, TemplateView):
            template_name = "base.html"

            def get_model_class(self):
                return Category

        v = V()
        v.request = RequestFactory().get("/")
        v.kwargs = {}
        v.args = []
        info = v.get_context_data()["model_info"]
        assert info["model_name"] == "category"
        assert info["app_label"] == "demo"

    def test_custom_override_exception_propagates(self):
        class CustomError(Exception):
            pass

        class V(ModelInfoMixin):
            def get_model_class(self):
                raise CustomError("boom")

        with pytest.raises(CustomError):
            V().get_model_class()

    # --- US3: Diagnostic error messages (T031–T034) -------------------------

    def test_raises_when_queryset_has_no_model(self):
        class _NoModelQuerySet:
            """Queryset-like object with no .model attribute."""

        class V(ModelInfoMixin):
            def get_queryset(self):
                return _NoModelQuerySet()

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    # --- get_model_class_or_none / model-less get_context_data (#311) -------

    def test_get_model_class_or_none_returns_model_when_resolvable(self):
        class V(ModelInfoMixin):
            model = Product

        assert V().get_model_class_or_none() is Product

    def test_get_model_class_or_none_returns_none_when_unresolvable(self):
        class V(ModelInfoMixin):
            form_class = _PlainForm

        assert V().get_model_class_or_none() is None

    def test_context_data_model_info_is_none_without_a_model(self):

        class V(ModelInfoMixin, TemplateView):
            form_class = _PlainForm
            template_name = "base.html"

        v = V()
        v.request = RequestFactory().get("/")
        v.kwargs = {}
        v.args = []
        assert v.get_context_data()["model_info"] is None


class TestMVPHomeView:
    def _make_view(self, user):
        """Return a configured MVPHomeView instance for the given user."""
        request = RequestFactory().get("/")
        request.user = user
        view = MVPHomeView()
        view.request = request
        view.kwargs = {}
        view.args = []
        return view

    @pytest.mark.django_db
    def test_authenticated_user_gets_dashboard_template(self, make_user):
        user = make_user(username="dashuser", password="pass")
        view = self._make_view(user)
        templates = view.get_template_names()
        assert templates == [view.dashboard_template_name]

    def test_anonymous_user_gets_landing_template(self):
        from django.contrib.auth.models import AnonymousUser

        view = self._make_view(AnonymousUser())
        templates = view.get_template_names()
        assert templates == [view.landing_template_name]


# TestMVPTemplateViewLayoutIntegration


@pytest.mark.django_db
class TestMVPTemplateViewLayoutIntegration:
    def test_all_layout_attributes_in_context(self):
        from mvp.views import MVPTemplateView

        request = RequestFactory().get("/")
        view = MVPTemplateView(
            template_name="page_view.html",
            page_title="T",
            page_subtitle="S",
            page_class="sidebar-collapse",
            breadcrumbs=[{"text": "Home", "href": "/"}],
        )
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        page = context["page"]
        assert page["title"] == "T"
        assert page["subtitle"] == "S"
        assert "sidebar-collapse" in page["class"]
        assert page["breadcrumbs"] == [{"text": "Home", "href": "/"}]


# US2: MVPHomeView — guest/dashboard template switch


@pytest.mark.django_db
class TestLoginReturnJourney:
    def test_full_login_and_return_journey(self, client, make_user):
        user = make_user(username="journeyuser", password="pass123!")

        # Step 1: Anonymous visit to /
        response = client.get("/")
        assert response.status_code == 200

        # Step 2: Authenticate
        client.force_login(user)

        # Step 3: Visit / as authenticated user
        response = client.get("/")
        assert response.status_code == 200

        # Step 5: Confirm sidebar and navbar are present on dashboard
        assert b"mvp-sidebar" in response.content, "Sidebar missing from dashboard"
        assert b"mvp-header" in response.content, "Navbar missing from dashboard"
