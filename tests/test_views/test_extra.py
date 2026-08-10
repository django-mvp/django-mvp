"""Tests for mvp.views.extra — MVPTemplateView's default placeholder template.

Source: mvp/views/extra.py

Issue #187: MVPTemplateView had no default ``template_name``, so wiring up a
menu/URL structure ahead of writing templates produced a 500 rather than a
renderable placeholder.
"""

import pytest
from django.test import Client, RequestFactory, override_settings
from django.urls import include, path

from mvp.views.extra import MVPTemplateView


def _urlconf(*extra_patterns):
    """A URLconf with the demo site's own URLs plus the given extra patterns.

    The shared page chrome renders a sidebar menu that reverses named URLs from
    ``demo.urls`` (e.g. ``component-doc``), so a bare URLconf breaks a full-page
    render with ``NoReverseMatch``. Tests that render the placeholder end to end
    need the real URL graph underneath their one extra path.
    """
    patterns = list(extra_patterns) + [path("", include("demo.urls"))]
    return type("_URLConf", (), {"urlpatterns": patterns})


class _UnwiredView(MVPTemplateView):
    """A subclass that deliberately sets nothing but page_title — the exact
    rapid-prototyping scenario from the issue: a menu entry wired to a view
    before its template exists."""

    page_title = "Unwired Page"


@pytest.mark.django_db
class TestMVPTemplateViewDefaultTemplate:
    """An MVPTemplateView subclass with no ``template_name`` renders a placeholder, not a 500."""

    def test_unconfigured_subclass_renders_200_not_500(self):
        """A subclass that never sets template_name still returns 200."""
        urlconf = _urlconf(path("unwired/", _UnwiredView.as_view()))
        with override_settings(ROOT_URLCONF=urlconf):
            response = Client().get("/unwired/")
        assert response.status_code == 200

    def test_placeholder_reads_as_a_placeholder(self):
        """The rendered page says it is a placeholder, not finished content."""
        urlconf = _urlconf(path("unwired/", _UnwiredView.as_view()))
        with override_settings(ROOT_URLCONF=urlconf):
            content = Client().get("/unwired/").content.decode()
        assert "template yet" in content.lower() or "placeholder" in content.lower()

    def test_explicit_template_name_still_wins(self):
        """A subclass that sets its own template_name is unaffected by the default."""
        request = RequestFactory().get("/")
        view = MVPTemplateView()
        view.template_name = "mvp/dashboard.html"
        view.request = request
        view.kwargs = {}
        view.args = []
        assert view.get_template_names() == ["mvp/dashboard.html"]

    @override_settings(DEBUG=True)
    def test_debug_true_names_the_rendering_view_and_path(self):
        """Under DEBUG, the placeholder names the view class and the URL path."""
        urlconf = _urlconf(path("unwired/", _UnwiredView.as_view()))
        with override_settings(ROOT_URLCONF=urlconf, DEBUG=True):
            content = Client().get("/unwired/").content.decode()
        assert "_UnwiredView" in content
        assert "/unwired/" in content

    @override_settings(DEBUG=False)
    def test_debug_false_hides_the_view_and_path_detail(self):
        """Outside DEBUG, the placeholder does not leak the view's class name."""
        urlconf = _urlconf(path("unwired/", _UnwiredView.as_view()))
        with override_settings(ROOT_URLCONF=urlconf, DEBUG=False):
            content = Client().get("/unwired/").content.decode()
        assert "_UnwiredView" not in content
