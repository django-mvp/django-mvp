"""Views for the django-sphinx-view integration."""

import mimetypes
from html import unescape
from pathlib import Path

from django.http import FileResponse, Http404, HttpResponsePermanentRedirect
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from mvp.integrations import missing_dependency
from mvp.views.base import PageMixin

try:
    from sphinx_view import DocumentationView
except ImportError as e:
    raise missing_dependency("sphinx_view", "django-sphinx-view") from e

# Folders the Sphinx build writes files into that pages link to directly.
FILE_FOLDERS = ("_images", "_downloads")


class MVPDocumentationView(PageMixin, DocumentationView):
    """Serve a Sphinx JSON build inside the application shell."""

    template_name = "mvp/sphinx_view/page.html"
    docs_title = _("Documentation")

    def get(self, request, *args, **kwargs):
        parts = Path(self.kwargs["path"]).parts
        if len(parts) > 2 and parts[1] in FILE_FOLDERS:
            return self.serve_file(parts[1], Path(*parts[2:]))
        if not self.kwargs["path"].endswith("/"):
            return HttpResponsePermanentRedirect(request.path + "/")
        return super().get(request, *args, **kwargs)

    def serve_file(self, folder, relative):
        base = (Path(self.json_build_dir) / folder).resolve()
        target = (base / relative).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            raise Http404
        content_type, _encoding = mimetypes.guess_type(target.name)
        return FileResponse(target.open("rb"), content_type=content_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = context["doc"]
        context["page"]["title"] = unescape(strip_tags(doc["title"]))
        context["page"]["breadcrumbs"] = self.get_doc_breadcrumbs(doc)
        context["docs_root"] = self.get_docs_root()
        return context

    def get_docs_root(self):
        """The URL of the documentation's front page."""
        path = self.request.path
        return path[: len(path) - len(self.kwargs["path"]) + 1]

    def get_doc_breadcrumbs(self, doc):
        if self.kwargs["path"] == "/":
            return [{"text": self.docs_title}]
        crumbs = [{"text": self.docs_title, "href": self.get_docs_root()}]
        for parent in doc.get("parents", []):
            crumbs.append(
                {"text": unescape(strip_tags(parent["title"])), "href": parent["link"]}
            )
        crumbs.append({"text": unescape(strip_tags(doc["title"]))})
        return crumbs
