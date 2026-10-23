"""Tests for BaseTemplateNameMixin and PageMixin in mvp.views.base."""

import pytest
from django import forms as django_forms
from django.core.exceptions import ImproperlyConfigured
from django.db import models as db_models
from django.test import RequestFactory
from django.utils.safestring import SafeString, mark_safe
from django.views.generic import TemplateView

from demo.models import Category, Product
from mvp.views.base import (
    BaseTemplateNameMixin,
    ModelInfoMixin,
    PageMixin,
    PageWidth,
)
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
            "title_args",
            "title_layout",
            "class",
            "breadcrumbs",
            "info",
            "info_actions",
            "width",
        }

    def test_get_page_context_delegates_to_getters(self):
        view = ConcretePage()
        view.page_title = "Test"
        view.page_lead = "Sub"
        view.page_class = "extra"
        view.breadcrumbs = [{"text": "Home"}]
        ctx = view.get_page_context()
        assert ctx["title"] == "Test"
        assert ctx["title_args"]["lead"] == "Sub"
        assert ctx["breadcrumbs"] == [{"text": "Home"}]


class TestPageTitleArgs:
    def test_the_group_names_every_argument(self):
        args = ConcretePage().get_page_title_args()

        assert set(args) == {
            "eyebrow",
            "title",
            "lead",
            "actions",
            "info",
            "info_actions",
        }

    @pytest.mark.parametrize("name", ["eyebrow", "lead", "actions"])
    def test_an_argument_is_empty_until_the_view_sets_it(self, name):
        args = ConcretePage().get_page_context()["title_args"]

        assert not args[name]

    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("eyebrow", "Inventory"),
            ("lead", "Everything in stock."),
            ("actions", [{"text": "Export", "href": "/export/"}]),
        ],
    )
    def test_an_attribute_reaches_the_group(self, name, value):
        view = ConcretePage()
        setattr(view, f"page_{name}", value)

        assert view.get_page_context()["title_args"][name] == value

    def test_an_eyebrow_method_wins_over_its_attribute(self):
        class EyebrowPage(ConcretePage):
            page_eyebrow = "From the attribute"

            def get_page_eyebrow(self):
                return "From the method"

        assert EyebrowPage().get_page_context()["title_args"]["eyebrow"] == (
            "From the method"
        )

    def test_a_lead_method_wins_over_its_attribute(self):
        class LeadPage(ConcretePage):
            page_lead = "From the attribute"

            def get_page_lead(self):
                return "From the method"

        assert LeadPage().get_page_context()["title_args"]["lead"] == "From the method"

    def test_an_actions_method_wins_over_its_attribute(self):
        class ActionsPage(ConcretePage):
            page_actions = [{"text": "From the attribute"}]

            def get_page_actions(self):
                return [{"text": "From the method"}]

        assert ActionsPage().get_page_context()["title_args"]["actions"] == [
            {"text": "From the method"}
        ]

    def test_a_subclass_changing_one_attribute_keeps_the_parents_others(self):
        class Parent(ConcretePage):
            page_title = "Parent title"
            page_eyebrow = "Parent eyebrow"
            page_lead = "Parent lead"
            page_actions = [{"text": "Parent action"}]

        class Child(Parent):
            page_lead = "Child lead"

        args = Child().get_page_context()["title_args"]

        assert args["lead"] == "Child lead"
        assert args["title"] == "Parent title"
        assert args["eyebrow"] == "Parent eyebrow"
        assert args["actions"] == [{"text": "Parent action"}]

    def test_overriding_the_group_replaces_what_the_page_carries(self):
        class GroupPage(ConcretePage):
            page_lead = "Ignored"

            def get_page_title_args(self):
                return {"title": "Computed", "lead": "Computed lead"}

        ctx = GroupPage().get_page_context()

        assert ctx["title_args"] == {"title": "Computed", "lead": "Computed lead"}

    def test_the_title_and_info_stay_in_the_page_context(self):
        view = ConcretePage()
        view.page_title = "Products"
        view.page_info = "What this page is for."
        view.page_info_actions = [{"text": "Docs"}]

        ctx = view.get_page_context()

        assert ctx["title"] == "Products"
        assert ctx["info"] == "What this page is for."
        assert ctx["info_actions"] == [{"text": "Docs"}]

    def test_the_subtitle_is_gone_from_the_page_context(self):
        assert "subtitle" not in ConcretePage().get_page_context()

    def test_a_view_still_setting_the_subtitle_draws_no_lead(self):
        class OldNamePage(ConcretePage):
            page_subtitle = "Old name"

        assert not OldNamePage().get_page_context()["title_args"]["lead"]


class TestPageTitleLayoutSetting:
    @staticmethod
    def _view_classes():
        from mvp.views import (
            MVPCreateView,
            MVPDeleteView,
            MVPDetailView,
            MVPFormView,
            MVPListView,
        )

        return {
            "page": ConcretePage,
            "form": MVPFormView,
            "create": MVPCreateView,
            "detail": MVPDetailView,
            "delete": MVPDeleteView,
            "list": MVPListView,
        }

    @staticmethod
    def _table_view_class():
        pytest.importorskip("django_tables2")
        from mvp.integrations.django_tables.views import MVPTableView

        return MVPTableView

    @staticmethod
    def _setting(monkeypatch, layout):
        """Leave ``MVP_CONFIG["page_title"]`` as a project's settings would.

        ``mvp.config`` deep-merges the project's value over the package default at
        import, so a dict naming one page type arrives with the others filled in.
        """
        import copy

        from mergedeep import merge

        from mvp.config import MVP_CONFIG

        merged = merge(copy.deepcopy(MVP_CONFIG["page_title"]), {"layout": layout})
        monkeypatch.setitem(MVP_CONFIG, "page_title", merged)

    @pytest.mark.parametrize(
        ("kind", "expected"),
        [
            ("page", "default"),
            ("form", "default"),
            ("create", "default"),
            ("detail", "default"),
            ("delete", "default"),
            ("list", "inline"),
        ],
    )
    def test_with_no_setting_each_page_type_draws_the_layout_it_always_has(
        self, kind, expected
    ):
        view = self._view_classes()[kind]()

        assert view.get_page_title_layout() == expected

    def test_with_no_setting_a_table_page_draws_the_compact_layout(self):
        assert self._table_view_class()().get_page_title_layout() == "compact"

    def test_the_layout_reaches_the_page_context(self):
        assert ConcretePage().get_page_context()["title_layout"] == "default"

    def test_each_view_type_names_its_page_type(self):
        views = self._view_classes()
        assert {kind: cls.page_type for kind, cls in views.items()} == {
            "page": "page",
            "form": "form",
            "create": "form",
            "detail": "detail",
            "delete": "delete",
            "list": "list",
        }
        assert self._table_view_class().page_type == "table"

    @pytest.mark.parametrize("kind", ["page", "form", "detail", "delete", "list"])
    def test_a_string_applies_to_every_page_type(self, monkeypatch, kind):
        self._setting(monkeypatch, "centred")

        assert self._view_classes()[kind]().get_page_title_layout() == "centred"

    def test_a_string_applies_to_a_table_page(self, monkeypatch):
        self._setting(monkeypatch, "centred")

        assert self._table_view_class()().get_page_title_layout() == "centred"

    @pytest.mark.parametrize(
        "named", ["page", "form", "detail", "delete", "list", "table"]
    )
    def test_a_dict_naming_one_type_changes_only_that_type(self, monkeypatch, named):
        self._setting(monkeypatch, {named: "centred"})

        defaults = {
            "page": "default",
            "form": "default",
            "detail": "default",
            "delete": "default",
            "list": "inline",
            "table": "compact",
        }
        views = {**self._view_classes(), "table": self._table_view_class()}
        resolved = {
            kind: views[kind]().get_page_title_layout() for kind in defaults
        }
        assert resolved == {**defaults, named: "centred"}

    def test_a_dict_changing_the_table_leaves_the_list_inline(self, monkeypatch):
        self._setting(monkeypatch, {"table": "default"})

        assert self._table_view_class()().get_page_title_layout() == "default"
        assert self._view_classes()["list"]().get_page_title_layout() == "inline"


class TestPageTitleLayoutOnTheView:
    @staticmethod
    def _setting(monkeypatch, layout):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["page_title"], "layout", layout)

    def test_a_view_names_no_layout_by_default(self):
        assert ConcretePage.page_title_layout is None

    def test_the_attribute_wins_over_the_setting(self, monkeypatch):
        self._setting(monkeypatch, "inline")

        class CompactPage(ConcretePage):
            page_title_layout = "compact"

        assert CompactPage().get_page_title_layout() == "compact"
        assert CompactPage().get_page_context()["title_layout"] == "compact"

    def test_a_view_without_one_takes_the_setting(self, monkeypatch):
        self._setting(monkeypatch, "inline")

        assert ConcretePage().get_page_title_layout() == "inline"

    def test_the_method_wins_over_the_attribute_and_the_setting(self, monkeypatch):
        self._setting(monkeypatch, "inline")

        class MethodPage(ConcretePage):
            page_title_layout = "compact"

            def get_page_title_layout(self):
                return "centred"

        assert MethodPage().get_page_context()["title_layout"] == "centred"

    def test_an_unknown_name_raises_naming_the_value_and_the_view(self):
        class MistypedPage(ConcretePage):
            page_title_layout = "no_such_layout"

        with pytest.raises(ImproperlyConfigured) as error:
            MistypedPage().get_page_context()

        assert "no_such_layout" in str(error.value)
        assert "MistypedPage" in str(error.value)

    @pytest.mark.django_db
    def test_an_unknown_name_raises_when_the_page_is_rendered(self):
        from django.contrib.auth.models import AnonymousUser

        from mvp.views import MVPTemplateView

        class MistypedPage(MVPTemplateView):
            template_name = "page_view.html"
            page_title_layout = "no_such_layout"

        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        with pytest.raises(ImproperlyConfigured, match="MistypedPage"):
            MistypedPage.as_view()(request).render()

    @pytest.mark.usefixtures("project_components")
    def test_a_project_component_is_accepted(self):
        class OwnLayoutPage(ConcretePage):
            page_title_layout = "fixture_title_file"

        assert OwnLayoutPage().get_page_context()["title_layout"] == (
            "fixture_title_file"
        )

    def test_an_unknown_name_in_the_setting_raises_naming_the_value_and_the_view(
        self, monkeypatch
    ):
        self._setting(monkeypatch, "no_such_layout")

        with pytest.raises(ImproperlyConfigured) as error:
            ConcretePage().get_page_context()

        assert "no_such_layout" in str(error.value)
        assert "ConcretePage" in str(error.value)


class TestPageMixinPageWidth:
    def test_a_page_is_wide_unless_it_says_otherwise(self):
        assert ConcretePage().get_page_width() is PageWidth.WIDE

    @pytest.mark.parametrize("width", list(PageWidth))
    def test_attribute_reaches_the_page_context(self, width):
        view = ConcretePage()
        view.page_width = width
        assert view.get_page_context()["width"] is width

    def test_the_context_value_renders_as_the_name_a_template_compares(self):
        view = ConcretePage()
        view.page_width = PageWidth.NARROW
        assert f"{view.get_page_context()['width']}" == "narrow"

    def test_a_width_outside_the_list_is_refused(self):
        view = ConcretePage()
        view.page_width = "enormous"
        with pytest.raises(ValueError, match="enormous"):
            view.get_page_width()


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
            page_lead="S",
            page_class="sidebar-collapse",
            breadcrumbs=[{"text": "Home", "href": "/"}],
        )
        view.request = request
        view.kwargs = {}
        view.args = []
        context = view.get_context_data()
        page = context["page"]
        assert page["title"] == "T"
        assert page["title_args"]["lead"] == "S"
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
