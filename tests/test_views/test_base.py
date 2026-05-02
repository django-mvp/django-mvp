"""Tests for BaseTemplateNameMixin and PageMixin in mvp.views.base."""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.views.generic import TemplateView

from mvp.views.base import BaseTemplateNameMixin, MVPHomeView, PageMixin

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

    def test_default_page_icon_is_none(self):
        assert PageMixin.page_icon is None

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

    def test_get_page_icon_returns_page_icon(self):
        view = ConcretePage()
        view.page_icon = "fas fa-home"
        assert view.get_page_icon() == "fas fa-home"

    def test_get_page_icon_returns_none_by_default(self):
        view = ConcretePage()
        assert view.get_page_icon() is None

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
        assert set(ctx.keys()) == {"title", "subtitle", "icon", "class", "breadcrumbs"}

    def test_get_page_context_delegates_to_getters(self):
        view = ConcretePage()
        view.page_title = "Test"
        view.page_subtitle = "Sub"
        view.page_icon = "fas fa-star"
        view.page_class = "extra"
        view.breadcrumbs = [{"text": "Home"}]
        ctx = view.get_page_context()
        assert ctx["title"] == "Test"
        assert ctx["subtitle"] == "Sub"
        assert ctx["icon"] == "fas fa-star"
        assert ctx["class"] == "mvp-page extra"
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
    page_icon = "fas fa-check"
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
        assert page["icon"] == "fas fa-check"
        assert page["class"] == "mvp-page custom-view"
        assert page["breadcrumbs"] == [{"text": "Home", "href": "/"}]


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
        assert templates == ["mvp/dashboard.html"]

    def test_anonymous_user_gets_landing_template(self):
        from django.contrib.auth.models import AnonymousUser
        view = self._make_view(AnonymousUser())
        templates = view.get_template_names()
        assert templates == ["mvp/landing.html"]

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
