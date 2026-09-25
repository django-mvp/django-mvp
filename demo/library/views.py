"""The library app's two pages."""

from django.utils.translation import gettext_lazy as _

from mvp.views.extra import MVPTemplateView


class CatalogueView(MVPTemplateView):
    """The landing page. Sets no title, so the tab reads ``Library | <site>``."""

    template_name = "library/catalogue.html"


class ReadingListView(MVPTemplateView):
    """A second page with a title, so the tab reads
    ``Reading list | Library | <site>``."""

    template_name = "library/reading_list.html"
    page_title = _("Reading list")
