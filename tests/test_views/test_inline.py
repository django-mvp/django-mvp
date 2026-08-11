"""Tests for InlineFormSet, InlinesMixin, MVPInlineCreateView and MVPInlineUpdateView.

Covers User Story 1 (specs/025-multiple-related-sets): a row set declared as
its own class, one set end to end — the parent's form and one related
model's rows rendered, validated and saved together on one page.

Source: mvp/views/inline.py
Spec: specs/025-multiple-related-sets/spec.md
"""

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from demo.models import Project, ProjectNote, ProjectTask
from mvp.views.inline import (
    InlineFormSet,
    InlinesMixin,
    MVPInlineCreateView,
    MVPInlineUpdateView,
)
from tests.factories import ProjectFactory, ProjectNoteFactory, ProjectTaskFactory


def _build_request(method="GET", data=None):
    """Return a request carrying working session and messages storage.

    ``as_view()`` is called directly (no middleware runs), but ``form_valid``
    needs ``request._messages`` to queue the success flash, so session and
    messages middleware are applied to the request by hand.
    """
    rf = RequestFactory()
    request = rf.post("/", data=data or {}) if method == "POST" else rf.get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    MessageMiddleware(lambda r: None).process_request(request)
    return request


def _dispatch(view_cls, method="GET", data=None, view_kwargs=None):
    """Build a request and run it through ``view_cls`` via ``as_view()``."""
    request = _build_request(method=method, data=data)
    response = view_cls.as_view()(request, **(view_kwargs or {}))
    return request, response


def _rendered_html(response):
    """Render a ``TemplateResponse`` and return its decoded content."""
    response.render()
    return response.content.decode()


def _field_value(html, field_name):
    """Return the ``value`` of the first field named ``field_name``, or None."""
    soup = BeautifulSoup(html, "html.parser")
    field = soup.find(attrs={"name": field_name})
    if field is None:
        return None
    if field.name == "textarea":
        return field.text
    return field.get("value")


class TaskInline(InlineFormSet):
    """The worked one-set declaration used across US1's view-level tests."""

    model = ProjectTask
    fields = ["title"]


def _stub_attrs(**overrides):
    """The shared stub configuration: a Project parent with ProjectTask rows.

    ``tests/test_components/test_form_formset.py`` imports the two view-class
    builders below alongside ``_field_value``/``_dispatch``/``_rendered_html``
    — they predate this story and exercised the removed ``inline_*``
    attributes against ``Product``/``OrderLine``. Kept here, re-pointed at
    this story's ``InlineFormSet`` surface and fixtures, so that file still
    *collects* rather than erroring on import; the handful of its own tests
    that assert on the old attribute names or Product/OrderLine field
    prefixes now fail honestly, which is correct — that configuration no
    longer exists. See this story's completion report for the concern this
    is reported under.
    """
    return {
        "model": Project,
        "fields": ["name"],
        "inlines": [TaskInline],
        "template_name": "form_view.html",
        "show_detail_action": False,
        "show_list_action": False,
        **overrides,
    }


def _inline_update_view_class(**attrs):
    return type("StubInlineUpdateView", (MVPInlineUpdateView,), _stub_attrs(**attrs))


def _inline_create_view_class(**attrs):
    return type("StubInlineCreateView", (MVPInlineCreateView,), _stub_attrs(**attrs))


class _StubInlinesView(InlinesMixin):
    """A bare object mixing in ``InlinesMixin``, for testing its methods in
    isolation from the rest of the view stack."""

    def __init__(self, model, object, queryset=None):
        self.model = model
        self.object = object
        self.queryset = queryset

    def get_queryset(self):
        return self.queryset

# ---------------------------------------------------------------------------
# T001 — fixture models and factories for the whole feature
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRowSetFixtures:
    """The fixture models this feature's tests build on: a parent (``Project``)
    with two distinct related models (``ProjectTask``, ``ProjectNote``), one of
    which (``ProjectNote``) reaches the parent by a second relation."""

    def test_project_task_belongs_to_a_project(self):
        project = ProjectFactory()
        task = ProjectTaskFactory(project=project)

        assert task.project == project
        assert task in project.tasks.all()

    def test_project_note_reaches_the_parent_by_two_relations(self):
        project = ProjectFactory()
        other = ProjectFactory()
        note = ProjectNoteFactory(project=project, related_project=other)

        assert note.project == project
        assert note.related_project == other
        assert note in project.notes.all()
        assert note in other.cross_notes.all()

    def test_project_task_and_project_note_are_distinct_related_models(self):
        assert ProjectTask is not ProjectNote
        assert Project._meta.get_field("name")


# ---------------------------------------------------------------------------
# T002 — a declaration naming no model raises ImproperlyConfigured (FR-006)
# ---------------------------------------------------------------------------


class TestInlineFormSetRequiresModel:
    """A declaration class that does not name a related model raises
    ``ImproperlyConfigured`` naming the declaration class (FR-006, US1 s3)."""

    def test_missing_model_raises_improperly_configured_naming_the_class(self):
        class TaskInline(InlineFormSet):
            fields = ["title"]

        with pytest.raises(ImproperlyConfigured, match="TaskInline"):
            TaskInline(parent_model=Project, request=None, instance=None, view=None)


# ---------------------------------------------------------------------------
# T004 — get_factory_kwargs() folds the shorthands in (FR-002, FR-013, R9)
# ---------------------------------------------------------------------------


class TestGetFactoryKwargs:
    """``get_factory_kwargs()`` assembles the kwargs ``inlineformset_factory``
    builds the formset class from, folding the shorthand attributes in."""

    def _declaration(self, **attrs):
        cls = type("TaskInline", (InlineFormSet,), {"model": ProjectTask, **attrs})
        return cls(parent_model=Project, request=None, instance=None, view=None)

    def test_folds_shorthand_attributes_in(self):
        declaration = self._declaration(fields=["title"], extra=2, can_delete=False)

        kwargs = declaration.get_factory_kwargs()

        assert kwargs["fields"] == ["title"]
        assert kwargs["extra"] == 2
        assert kwargs["can_delete"] is False

    def test_explicit_factory_kwargs_key_wins_over_its_shorthand(self):
        declaration = self._declaration(
            fields=["title"], factory_kwargs={"fields": ["title", "project"]}
        )

        kwargs = declaration.get_factory_kwargs()

        assert kwargs["fields"] == ["title", "project"]

    def test_validate_max_is_set_exactly_when_max_num_is(self):
        without_cap = self._declaration(fields=["title"])
        with_cap = self._declaration(fields=["title"], max_num=5)

        assert "validate_max" not in without_cap.get_factory_kwargs()
        assert with_cap.get_factory_kwargs()["validate_max"] is True
        assert with_cap.get_factory_kwargs()["max_num"] == 5

    def test_absolute_max_is_never_present(self):
        declaration = self._declaration(fields=["title"], max_num=5)

        assert "absolute_max" not in declaration.get_factory_kwargs()

    def test_validate_min_is_set_exactly_when_min_num_is(self):
        without_floor = self._declaration(fields=["title"])
        with_floor = self._declaration(fields=["title"], min_num=1)

        assert "validate_min" not in without_floor.get_factory_kwargs()
        assert with_floor.get_factory_kwargs()["validate_min"] is True
        assert with_floor.get_factory_kwargs()["min_num"] == 1


# ---------------------------------------------------------------------------
# T006 — a set declaring min_num rejects a submission with fewer rows
# (FR-023, US1 s9)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMinNumRejectsFewerRows:
    """A set declaring ``min_num`` rejects a submission carrying fewer rows
    than the minimum."""

    def _post_formset(self, project, min_rows, total_forms, quantities):
        cls = type(
            "TaskInline",
            (InlineFormSet,),
            {"model": ProjectTask, "fields": ["title"], "min_num": min_rows},
        )
        data = {
            "tasks-TOTAL_FORMS": str(total_forms),
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }
        for i, title in enumerate(quantities):
            data[f"tasks-{i}-title"] = title
        request = RequestFactory().post("/", data=data)
        declaration = cls(
            parent_model=Project, request=request, instance=project, view=None
        )
        return declaration.construct_formset()

    def test_submission_below_the_minimum_is_rejected(self):
        project = ProjectFactory()
        formset = self._post_formset(
            project, min_rows=2, total_forms=1, quantities=["Only one"]
        )

        assert not formset.is_valid()
        assert formset.non_form_errors()

    def test_submission_at_the_minimum_is_accepted(self):
        project = ProjectFactory()
        formset = self._post_formset(
            project, min_rows=2, total_forms=2, quantities=["First", "Second"]
        )

        assert formset.is_valid()


# ---------------------------------------------------------------------------
# T007 — get_formset_kwargs() (FR-004, R3, R6)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetFormsetKwargs:
    """``get_formset_kwargs()`` carries the instance-level kwargs the
    formset is constructed from."""

    def _declaration(self, request=None, **attrs):
        cls = type(
            "TaskInline", (InlineFormSet,), {"model": ProjectTask, **attrs}
        )
        return cls(
            parent_model=Project,
            request=request or RequestFactory().get("/"),
            instance=self.project,
            view=None,
        )

    @pytest.fixture(autouse=True)
    def _project(self):
        self.project = ProjectFactory()

    def test_carries_the_instance(self):
        declaration = self._declaration()

        assert declaration.get_formset_kwargs()["instance"] is self.project

    def test_get_carries_no_data_or_files(self):
        declaration = self._declaration(request=RequestFactory().get("/"))

        kwargs = declaration.get_formset_kwargs()

        assert "data" not in kwargs
        assert "files" not in kwargs

    def test_post_carries_data_and_files(self):
        request = RequestFactory().post("/", data={"tasks-TOTAL_FORMS": "0"})
        declaration = self._declaration(request=request)

        kwargs = declaration.get_formset_kwargs()

        assert kwargs["data"] is request.POST
        assert kwargs["files"] is request.FILES

    def test_declared_prefix_is_put_in(self):
        declaration = self._declaration(prefix="custom")

        assert declaration.get_formset_kwargs()["prefix"] == "custom"

    def test_unset_prefix_is_omitted_entirely(self):
        declaration = self._declaration()

        assert "prefix" not in declaration.get_formset_kwargs()

    def test_mutating_the_returned_form_kwargs_does_not_alter_the_class_attribute(
        self,
    ):
        cls = type(
            "TaskInline",
            (InlineFormSet,),
            {"model": ProjectTask, "form_kwargs": {"label_suffix": "!"}},
        )
        first = cls(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=self.project,
            view=None,
        )
        second = cls(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=self.project,
            view=None,
        )

        first_kwargs = first.get_formset_kwargs()
        first_kwargs["form_kwargs"]["label_suffix"] = "MUTATED"

        assert cls.form_kwargs == {"label_suffix": "!"}
        assert second.get_formset_kwargs()["form_kwargs"] == {"label_suffix": "!"}


# ---------------------------------------------------------------------------
# T009 — get_title() defaults to verbose_name_plural (FR-011)
# ---------------------------------------------------------------------------


class TestGetTitle:
    """``get_title()`` defaults to the related model's ``verbose_name_plural``
    and an explicit ``title`` overrides it."""

    def _declaration(self, **attrs):
        cls = type("TaskInline", (InlineFormSet,), {"model": ProjectTask, **attrs})
        return cls(parent_model=Project, request=None, instance=None, view=None)

    def test_defaults_to_verbose_name_plural(self):
        declaration = self._declaration()

        assert declaration.get_title() == ProjectTask._meta.verbose_name_plural

    def test_explicit_title_overrides_the_default(self):
        declaration = self._declaration(title="Custom heading")

        assert declaration.get_title() == "Custom heading"

    def test_get_description_has_no_default(self):
        declaration = self._declaration()

        assert declaration.get_description() is None

    def test_explicit_description_is_returned(self):
        declaration = self._declaration(description="Help text")

        assert declaration.get_description() == "Help text"


# ---------------------------------------------------------------------------
# T011 — get_parent_model() resolution (FR-007, US1 s5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetParentModel:
    """``get_parent_model()`` resolves the parent the way Django's own
    model-form pages resolve it: ``self.model``, then the loaded object's
    class, then the queryset's model."""

    def test_resolves_from_model_attribute(self):
        stub = _StubInlinesView(model=Project, object=None)

        assert stub.get_parent_model() is Project

    def test_resolves_from_a_loaded_object_when_model_is_unset(self):
        project = ProjectFactory()
        stub = _StubInlinesView(model=None, object=project)

        assert stub.get_parent_model() is Project

    def test_resolves_from_queryset_alone(self):
        stub = _StubInlinesView(model=None, object=None)
        stub.queryset = Project.objects.all()

        assert stub.get_parent_model() is Project


# ---------------------------------------------------------------------------
# T013 — an update page with one declaration renders the parent form and the
# set's rows through the packaged components, from a real request (US1 s1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineUpdatePageRendering:
    """A GET renders the parent's form and the declared set's rows through
    the packaged formset components (US1 s1)."""

    def test_renders_parent_form_and_existing_rows(self):
        project = ProjectFactory(name="Website revamp")
        ProjectTaskFactory(project=project, title="Design mockups")
        ProjectTaskFactory(project=project, title="Build the homepage")
        view_cls = _inline_update_view_class(success_url="/done/")

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)
        soup = BeautifulSoup(html, "html.parser")

        assert soup.find(attrs={"name": "name"}).get("value") == "Website revamp"
        titles = [
            tag.get("value")
            for tag in soup.find_all(attrs={"name": lambda n: n and n.endswith("-title")})
        ]
        assert "Design mockups" in titles
        assert "Build the homepage" in titles

    def test_context_carries_the_inlines_list(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(success_url="/done/")

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        assert len(response.context_data["inlines"]) == 1
        assert response.context_data["inlines"][0].title == "project tasks"


# ---------------------------------------------------------------------------
# T016 — a row form whose widget carries media renders that media
# (S3R SPEC-004, Article XIII)
# ---------------------------------------------------------------------------


class _WidgetWithMedia(forms.TextInput):
    class Media:
        css = {"all": ["custom-row-widget.css"]}
        js = ["custom-row-widget.js"]


class _TaskFormWithMedia(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ["title"]
        widgets = {"title": _WidgetWithMedia}


class TaskInlineWithMedia(InlineFormSet):
    model = ProjectTask
    form = _TaskFormWithMedia


@pytest.mark.django_db
class TestInlineRowMediaRenders:
    """A row form whose widget carries media renders that media on the page
    — the media blocks iterate the sets as well as the standalone formset,
    so a list of inlines does not silently drop them."""

    def test_row_widget_media_renders_on_the_page(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInlineWithMedia]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)

        assert "custom-row-widget.css" in html
        assert "custom-row-widget.js" in html
