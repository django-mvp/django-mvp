class BaseTemplateNameMixin:
    base_template_name = ""

    def get_template_names(self):
        """Determine the template to use for rendering the form.

        Returns:
            list[str]: List of template names to search, with the most specific first
        """
        template_names = super().get_template_names()
        template_names.append(self.base_template_name)
        return template_names


class PageMixin:
    """Combined mixin for adding both page modifiers and breadcrumbs to the template context."""

    page_title: str = ""
    page_icon: str | None = None

    def get_context_data(self, **kwargs):
        """Inject form renderer and page title into template context.

        Returns:
            dict: Context with form_renderer and page_title added
        """
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.get_page_title()
        context["breadcrumbs"] = self.get_breadcrumbs()
        context["page_icon"] = self.get_page_icon()
        return context

    def get_page_title(self):
        """Return the page title for the form.

        Returns:
            str: Page title from page_title attribute
        """
        return self.page_title

    def get_page_icon(self) -> str | None:
        """Return the icon name for the page.

        Returns:
            str or None: Icon name from icon attribute
        """
        return self.page_icon

    def get_breadcrumbs(self):
        """Return the list of breadcrumb items.

        Returns:
            list[dict]: List of breadcrumb items with 'text' and optional 'href'
        """
        return []


from django.utils.http import url_has_allowed_host_and_scheme


class NextURLMixin:
    """Mixin to determine the next URL to redirect to after form submission."""

    def get_next_url(self):
        """Return a validated ``next`` URL from the current request, or ``None``.

        On POST requests reads from POST data; on GET requests reads from the
        query string. The candidate URL is validated against the current host
        via ``url_has_allowed_host_and_scheme`` to prevent open redirects.

        Returns:
            str | None: Validated URL, or ``None`` if absent or unsafe.
        """
        if self.request.method == "POST":
            candidate = self.request.POST.get("next")
        else:
            candidate = self.request.GET.get("next")

        if candidate and url_has_allowed_host_and_scheme(
            url=candidate,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return candidate
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.get_next_url()
        return context