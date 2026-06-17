"""Tests for BaseTemplateNameMixin and PageMixin in mvp.views.base."""

import pytest
from django import forms as django_forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import models as db_models
from django.test import RequestFactory
from django.views.generic import TemplateView

from demo.models import Category, Product
from mvp.views.base import BaseTemplateNameMixin, ModelInfoMixin, MVPHomeView, PageMixin

User = get_user_model()


# ---------------------------------------------------------------------------
# Concrete stubs for testing
# ---------------------------------------------------------------------------


class ConcreteTemplateView(BaseTemplateNameMixin, TemplateView):
    """Concrete subclass with base_template_name set — happy-path fixture."""

    base_template_name = "base.html"
    template_name = "specific.html"


class BareTemplateNameMixin(BaseTemplateNameMixin, TemplateView):
    """Subclass that deliberately leaves base_template_name as None (error case)."""

    template_name = "specific.html"


class ConcretePage(PageMixin, TemplateView):
    """Minimal concrete PageMixin subclass with no overrides."""

    template_name = "page.html"


# ---------------------------------------------------------------------------
# TestBaseTemplateNameMixin
# ---------------------------------------------------------------------------


class TestBaseTemplateNameMixin:
    def test_default_base_template_name_is_none(self):
        assert BaseTemplateNameMixin.base_template_name is None

    def test_raises_when_base_template_name_is_none(self):
        view = BareTemplateNameMixin()
        view.request = None  # not needed for template resolution
        with pytest.raises(ImproperlyConfigured):
            view.get_template_names()

    def test_error_message_includes_class_name(self):
        view = BareTemplateNameMixin()
        with pytest.raises(ImproperlyConfigured, match="BareTemplateNameMixin"):
            view.get_template_names()

    def test_returns_specific_template_first(self):
        view = ConcreteTemplateView()
        names = view.get_template_names()
        assert names[0] == "specific.html"

    def test_returns_base_template_last(self):
        view = ConcreteTemplateView()
        names = view.get_template_names()
        assert names[-1] == "base.html"

    def test_returns_list(self):
        view = ConcreteTemplateView()
        assert isinstance(view.get_template_names(), list)

    def test_base_template_name_in_list(self):
        view = ConcreteTemplateView()
        assert "base.html" in view.get_template_names()


# ---------------------------------------------------------------------------
# TestPageMixinDefaults
# ---------------------------------------------------------------------------


class TestPageMixinDefaults:
    def test_default_page_title_is_empty_string(self):
        assert PageMixin.page_title == ""

    def test_default_page_subtitle_is_empty_string(self):
        assert PageMixin.page_subtitle == ""

    def test_default_page_class_is_empty_string(self):
        assert PageMixin.page_class == ""

    def test_default_breadcrumbs_is_empty_list(self):
        assert PageMixin.breadcrumbs == []


# ---------------------------------------------------------------------------
# TestPageMixinGetters
# ---------------------------------------------------------------------------


class TestPageMixinGetters:
    def test_get_page_title_returns_page_title(self):
        view = ConcretePage()
        view.page_title = "My Title"
        assert view.get_page_title() == "My Title"

    def test_get_page_subtitle_returns_page_subtitle(self):
        view = ConcretePage()
        view.page_subtitle = "My Subtitle"
        assert view.get_page_subtitle() == "My Subtitle"

    def test_get_breadcrumbs_returns_breadcrumbs(self):
        crumbs = [{"text": "Home", "href": "/"}, {"text": "About"}]
        view = ConcretePage()
        view.breadcrumbs = crumbs
        assert view.get_breadcrumbs() == crumbs

    def test_get_page_class_prefixes_mvp_page(self):
        view = ConcretePage()
        view.page_class = "my-class"
        assert view.get_page_class() == "mvp-page my-class"

    def test_get_page_class_with_empty_page_class(self):
        view = ConcretePage()
        view.page_class = ""
        assert view.get_page_class() == "mvp-page"

    def test_get_page_class_with_none_page_class(self):
        view = ConcretePage()
        view.page_class = None
        assert view.get_page_class() == "mvp-page"


# ---------------------------------------------------------------------------
# TestPageMixinGetPageContext
# ---------------------------------------------------------------------------


class TestPageMixinGetPageContext:
    def test_get_page_context_returns_dict_with_required_keys(self):
        view = ConcretePage()
        ctx = view.get_page_context()
        assert set(ctx.keys()) == {"title", "subtitle", "class", "breadcrumbs"}

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


# ---------------------------------------------------------------------------
# TestPageMixinGetContextData
# ---------------------------------------------------------------------------


class TestPageMixinGetContextData:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_context_data_includes_page_key(self):
        request = self.factory.get("/")
        view = ConcretePage()
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        assert "page" in context

    def test_page_key_is_dict(self):
        request = self.factory.get("/")
        view = ConcretePage()
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        assert isinstance(context["page"], dict)

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


# ---------------------------------------------------------------------------
# TestPageMixinOverridePattern (Phase 5 — Extension Points)
# ---------------------------------------------------------------------------


class DynamicTitleView(PageMixin, TemplateView):
    """Stub that overrides get_page_title() to return a dynamic value."""

    template_name = "page.html"
    _dynamic_title = "Dynamic Title"

    def get_page_title(self):
        return self._dynamic_title


class DynamicBreadcrumbView(PageMixin, TemplateView):
    """Stub that overrides get_breadcrumbs() to return dynamic breadcrumbs."""

    template_name = "page.html"

    def get_breadcrumbs(self):
        return [{"text": "Home", "href": "/"}, {"text": "Detail"}]


class SubclassedPageView(PageMixin, TemplateView):
    """Stub that sets all attributes as class attributes."""

    template_name = "page.html"
    page_title = "Static Title"
    page_subtitle = "Static Subtitle"
    page_class = "custom-view"
    breadcrumbs = [{"text": "Home", "href": "/"}]


class TestPageMixinOverridePattern:
    def test_overriding_get_page_title_is_reflected_in_context(self):
        request = RequestFactory().get("/")
        view = DynamicTitleView()
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        assert context["page"]["title"] == "Dynamic Title"

    def test_overriding_get_breadcrumbs_is_reflected_in_context(self):
        request = RequestFactory().get("/")
        view = DynamicBreadcrumbView()
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        crumbs = context["page"]["breadcrumbs"]
        assert len(crumbs) == 2
        assert crumbs[0] == {"text": "Home", "href": "/"}

    def test_class_attribute_overrides_work_end_to_end(self):
        request = RequestFactory().get("/")
        view = SubclassedPageView()
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        page = context["page"]
        assert page["title"] == "Static Title"
        assert page["subtitle"] == "Static Subtitle"
        assert page["class"] == "mvp-page custom-view"
        assert page["breadcrumbs"] == [{"text": "Home", "href": "/"}]


# ---------------------------------------------------------------------------
# Stub models, forms, and proxies for TestModelInfoMixin (T006)
# ---------------------------------------------------------------------------


class _CustomVerboseModel(db_models.Model):
    """Stub with a custom verbose_name — unmanaged, no DB table."""

    class Meta:
        app_label = "demo"
        managed = False
        verbose_name = "custom item"
        verbose_name_plural = "custom items"


class _ProductProxy(Product):
    """Proxy of Product for proxy-model resolution tests."""

    class Meta:
        app_label = "demo"
        proxy = True


class _ProductForm(django_forms.ModelForm):
    """Minimal ModelForm bound to Product."""

    class Meta:
        model = Product
        fields = []


class _PlainForm(django_forms.Form):
    """Plain (non-Model) Form — used to verify silent skipping."""

    name = django_forms.CharField()


# ---------------------------------------------------------------------------
# TestModelInfoMixin
# ---------------------------------------------------------------------------


class TestModelInfoMixin:
    """All ModelInfoMixin tests. Pure Python unit tests — no database access required."""

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
        assert {"verbose_name", "verbose_name_plural", "app_label", "model_name"} <= set(info.keys())

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

    # --- US1 edge cases: plain Form skipped (T023) --------------------------

    def test_plain_form_class_skipped(self):
        """form_class with no _meta.model is skipped silently; ImproperlyConfigured raised."""

        class V(ModelInfoMixin):
            form_class = _PlainForm

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    # --- US1 edge cases: None object skipped (T024) -------------------------

    def test_none_object_skipped(self):
        class V(ModelInfoMixin):
            object = None

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    # --- US1 edge cases: proxy model (T025) ---------------------------------

    def test_proxy_model_returns_proxy_not_concrete(self):
        class V(ModelInfoMixin):
            model = _ProductProxy

        result = V().get_model_class()
        assert result is _ProductProxy
        assert result is not Product

    # --- US1 edge cases: all four strategies present (T026) -----------------

    def test_all_four_strategies_present_model_wins(self):
        obj = Category.__new__(Category)

        class _CategoryForm(django_forms.ModelForm):
            class Meta:
                model = Category
                fields = []

        class V(ModelInfoMixin):
            model = Product  # should win
            form_class = _CategoryForm
            object = obj

            def get_queryset(self):
                return Category.objects.all()

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

    def test_raises_improperly_configured_with_no_config(self):
        class V(ModelInfoMixin):
            pass

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    def test_error_message_contains_view_class_name(self):
        class MyUnconfiguredView(ModelInfoMixin):
            pass

        with pytest.raises(ImproperlyConfigured, match="MyUnconfiguredView"):
            MyUnconfiguredView().get_model_class()

    def test_error_message_describes_configuration_options(self):
        class V(ModelInfoMixin):
            pass

        with pytest.raises(ImproperlyConfigured) as exc_info:
            V().get_model_class()
        msg = str(exc_info.value)
        assert "model" in msg
        assert "queryset" in msg
        assert "form_class" in msg
        assert "get_model_class" in msg

    def test_raises_when_queryset_has_no_model(self):
        class _NoModelQuerySet:
            """Queryset-like object with no .model attribute."""

        class V(ModelInfoMixin):
            def get_queryset(self):
                return _NoModelQuerySet()

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()


# ---------------------------------------------------------------------------
# TestMVPHomeView (covers MVPHomeView branches in mvp.views.base)
# ---------------------------------------------------------------------------


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
    def test_authenticated_user_gets_dashboard_template(self):
        user = User.objects.create_user(username="dashuser", password="pass")
        view = self._make_view(user)
        templates = view.get_template_names()
        assert templates == [view.dashboard_template_name]

    def test_anonymous_user_gets_landing_template(self):
        from django.contrib.auth.models import AnonymousUser

        view = self._make_view(AnonymousUser())
        templates = view.get_template_names()
        assert templates == [view.landing_template_name]

    @pytest.mark.django_db
    def test_authenticated_context_calls_dashboard_context(self):
        user = User.objects.create_user(username="dashuser2", password="pass")
        view = self._make_view(user)
        # get_context_data raises no errors and returns a dict
        context = view.get_context_data()
        assert isinstance(context, dict)

    def test_unauthenticated_context_includes_hero_content(self):
        from django.contrib.auth.models import AnonymousUser

        view = self._make_view(AnonymousUser())
        context = view.get_context_data()
        assert "hero_content" in context


# ---------------------------------------------------------------------------
# TestMVPHomeViewDefaults (T031, T032 — US2)
# ---------------------------------------------------------------------------


class TestMVPHomeViewDefaults:
    def test_mvp_home_view_default_landing_template_name(self):
        from mvp.views.base import MVPHomeView

        assert MVPHomeView.landing_template_name == "mvp/landing.html"

    def test_mvp_home_view_default_dashboard_template_name(self):
        from mvp.views.base import MVPHomeView

        assert MVPHomeView.dashboard_template_name == "mvp/dashboard.html"

    def test_mvp_home_view_default_page_title(self):
        from django.utils.translation import gettext_lazy as _

        from mvp.views.base import MVPHomeView

        assert str(MVPHomeView.page_title) == str(_("Home"))

    def test_landing_template_none_raises_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.landing_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="landing_template_name"):
            view.get_template_names()

    def test_landing_template_none_error_message_contains_class_name(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.landing_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="MVPHomeView"):
            view.get_template_names()

    @pytest.mark.django_db
    def test_dashboard_template_none_raises_for_authenticated(self):
        user = User.objects.create_user(username="guardtest1", password="pass")
        request = RequestFactory().get("/")
        request.user = user
        from mvp.views.base import MVPHomeView

        view = MVPHomeView()
        view.dashboard_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="dashboard_template_name"):
            view.get_template_names()

    def test_dashboard_template_none_no_error_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.dashboard_template_name = None
        view.request = request
        # Should not raise — anonymous users get the landing template
        templates = view.get_template_names()
        assert templates == [view.landing_template_name]

    def test_both_none_anonymous_raises_on_landing_template_name(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.landing_template_name = None
        view.dashboard_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="landing_template_name"):
            view.get_template_names()


# ---------------------------------------------------------------------------


class _CustomVerboseModel(db_models.Model):
    """Stub with a custom verbose_name — unmanaged, no DB table."""

    class Meta:
        app_label = "demo"
        managed = False
        verbose_name = "custom item"
        verbose_name_plural = "custom items"


class _ProductProxy(Product):
    """Proxy of Product for proxy-model resolution tests."""

    class Meta:
        app_label = "demo"
        proxy = True


class _ProductForm(django_forms.ModelForm):
    """Minimal ModelForm bound to Product."""

    class Meta:
        model = Product
        fields = []


class _PlainForm(django_forms.Form):
    """Plain (non-Model) Form — used to verify silent skipping."""

    name = django_forms.CharField()


# ---------------------------------------------------------------------------
# TestModelInfoMixin
# ---------------------------------------------------------------------------


class TestModelInfoMixin:
    """All ModelInfoMixin tests. Pure Python unit tests — no database access required."""

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
        assert {"verbose_name", "verbose_name_plural", "app_label", "model_name"} <= set(info.keys())

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

    # --- US1 edge cases: plain Form skipped (T023) --------------------------

    def test_plain_form_class_skipped(self):
        """form_class with no _meta.model is skipped silently; ImproperlyConfigured raised."""

        class V(ModelInfoMixin):
            form_class = _PlainForm

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    # --- US1 edge cases: None object skipped (T024) -------------------------

    def test_none_object_skipped(self):
        class V(ModelInfoMixin):
            object = None

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    # --- US1 edge cases: proxy model (T025) ---------------------------------

    def test_proxy_model_returns_proxy_not_concrete(self):
        class V(ModelInfoMixin):
            model = _ProductProxy

        result = V().get_model_class()
        assert result is _ProductProxy
        assert result is not Product

    # --- US1 edge cases: all four strategies present (T026) -----------------

    def test_all_four_strategies_present_model_wins(self):
        obj = Category.__new__(Category)

        class _CategoryForm(django_forms.ModelForm):
            class Meta:
                model = Category
                fields = []

        class V(ModelInfoMixin):
            model = Product  # should win
            form_class = _CategoryForm
            object = obj

            def get_queryset(self):
                return Category.objects.all()

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

    def test_raises_improperly_configured_with_no_config(self):
        class V(ModelInfoMixin):
            pass

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()

    def test_error_message_contains_view_class_name(self):
        class MyUnconfiguredView(ModelInfoMixin):
            pass

        with pytest.raises(ImproperlyConfigured, match="MyUnconfiguredView"):
            MyUnconfiguredView().get_model_class()

    def test_error_message_describes_configuration_options(self):
        class V(ModelInfoMixin):
            pass

        with pytest.raises(ImproperlyConfigured) as exc_info:
            V().get_model_class()
        msg = str(exc_info.value)
        assert "model" in msg
        assert "queryset" in msg
        assert "form_class" in msg
        assert "get_model_class" in msg

    def test_raises_when_queryset_has_no_model(self):
        class _NoModelQuerySet:
            """Queryset-like object with no .model attribute."""

        class V(ModelInfoMixin):
            def get_queryset(self):
                return _NoModelQuerySet()

        with pytest.raises(ImproperlyConfigured):
            V().get_model_class()


# ---------------------------------------------------------------------------
# TestMVPHomeView (covers MVPHomeView branches in mvp.views.base)
# ---------------------------------------------------------------------------


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
    def test_authenticated_user_gets_dashboard_template(self):
        user = User.objects.create_user(username="dashuser", password="pass")
        view = self._make_view(user)
        templates = view.get_template_names()
        assert templates == [view.dashboard_template_name]

    def test_anonymous_user_gets_landing_template(self):
        from django.contrib.auth.models import AnonymousUser

        view = self._make_view(AnonymousUser())
        templates = view.get_template_names()
        assert templates == [view.landing_template_name]

    @pytest.mark.django_db
    def test_authenticated_context_calls_dashboard_context(self):
        user = User.objects.create_user(username="dashuser2", password="pass")
        view = self._make_view(user)
        # get_context_data raises no errors and returns a dict
        context = view.get_context_data()
        assert isinstance(context, dict)

    def test_unauthenticated_context_includes_hero_content(self):
        from django.contrib.auth.models import AnonymousUser

        view = self._make_view(AnonymousUser())
        context = view.get_context_data()
        assert "hero_content" in context


# ---------------------------------------------------------------------------
# TestMVPHomeViewDefaults (T031, T032 — US2)
# ---------------------------------------------------------------------------


class TestMVPHomeViewDefaults:
    def test_mvp_home_view_default_landing_template_name(self):
        from mvp.views.base import MVPHomeView

        assert MVPHomeView.landing_template_name == "mvp/landing.html"

    def test_mvp_home_view_default_dashboard_template_name(self):
        from mvp.views.base import MVPHomeView

        assert MVPHomeView.dashboard_template_name == "mvp/dashboard.html"

    def test_mvp_home_view_default_page_title(self):
        from django.utils.translation import gettext_lazy as _

        from mvp.views.base import MVPHomeView

        assert str(MVPHomeView.page_title) == str(_("Home"))

    def test_landing_template_none_raises_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.landing_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="landing_template_name"):
            view.get_template_names()

    def test_landing_template_none_error_message_contains_class_name(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.landing_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="MVPHomeView"):
            view.get_template_names()

    @pytest.mark.django_db
    def test_dashboard_template_none_raises_for_authenticated(self):
        user = User.objects.create_user(username="guardtest1", password="pass")
        request = RequestFactory().get("/")
        request.user = user
        from mvp.views.base import MVPHomeView

        view = MVPHomeView()
        view.dashboard_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="dashboard_template_name"):
            view.get_template_names()

    def test_dashboard_template_none_no_error_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.dashboard_template_name = None
        view.request = request
        # Should not raise — anonymous users get the landing template
        templates = view.get_template_names()
        assert templates == [view.landing_template_name]

    def test_both_none_anonymous_raises_on_landing_template_name(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views.base import MVPHomeView

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view = MVPHomeView()
        view.landing_template_name = None
        view.dashboard_template_name = None
        view.request = request
        with pytest.raises(ImproperlyConfigured, match="landing_template_name"):
            view.get_template_names()


# ---------------------------------------------------------------------------
# TestMVPTemplateViewLayoutIntegration (T042 — US4)
# Integration tests using Django test client to verify layout config attributes
# flow through to rendered HTML.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPTemplateViewLayoutIntegration:
    """Integration tests: MVPTemplateView layout config attributes appear in rendered HTML."""

    def test_page_class_in_container_element(self):
        """page_class value flows through get_page_class() with mvp-page prefix."""
        from mvp.views import MVPTemplateView

        request = RequestFactory().get("/")
        view = MVPTemplateView(
            template_name="page_view.html",
            page_class="sidebar-collapse",
        )
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        assert "sidebar-collapse" in context["page"]["class"]
        assert context["page"]["class"].startswith("mvp-page")

    def test_all_layout_attributes_in_context(self):
        """All page_* attributes are present in the page context dict."""
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
