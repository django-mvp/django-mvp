"""The library app's two pages."""

from mvp.views.extra import MVPTemplateView


class CatalogueView(MVPTemplateView):
    """The landing page. Sets no title, so the tab reads ``Library | <site>``."""

    template_name = "library/catalogue.html"


class ReadingListView(MVPTemplateView):
    """A second page with a title set.

    The tab reads ``Reading list | Library | <site>``.
    """

    template_name = "library/reading_list.html"
    page_title = "Reading list"
