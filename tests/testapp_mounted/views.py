"""The mounted fixture app's two pages."""

from django.http import Http404
from django.shortcuts import render

from mvp.views.extra import MVPTemplateView


class IndexView(MVPTemplateView):
    """The landing page. Sets no title of its own."""

    template_name = "testapp_mounted/index.html"


class DetailView(MVPTemplateView):
    """A second page, titled ``Detail``."""

    template_name = "testapp_mounted/detail.html"


def missing(request):
    """A page that is not there, raised from inside the mounted app."""
    raise Http404("nothing here")


def forbidden(request, exception):
    """A project's own 403 page, drawn inside the shell."""
    return render(request, "testapp_mounted/forbidden.html", status=403)
