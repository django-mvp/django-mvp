"""The mounted fixture app's two pages."""

from mvp.views.extra import MVPTemplateView


class IndexView(MVPTemplateView):
    """The landing page. Sets no title of its own."""

    template_name = "testapp_mounted/index.html"


class DetailView(MVPTemplateView):
    """A second page, titled ``Detail``."""

    template_name = "testapp_mounted/detail.html"
