"""The email preview page and the frame it shows an email in.

Both views render the templates a package declared with
``mvp.email.previews.register``. Only a signed-in staff member can open them,
and ``mvp.urls`` adds their routes only while ``DEBUG`` is on.
"""

import re
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from django.views import View

from mvp.views.extra import MVPTemplateView

from .previews import EmailPreview

SRC_ATTRIBUTE = re.compile(r'src="[^"]*"')


class EmailPreviewMixin(UserPassesTestMixin):
    """Staff-only access, the choices in the query string, and rendering a preview."""

    request: HttpRequest

    #: Each control's values, the first being the default.
    choices = {
        "part": ["html", "text"],
        "scheme": ["light", "dark"],
        "images": ["on", "off"],
        "width": ["desktop", "phone"],
    }

    def test_func(self) -> bool:
        """Allow staff members only.

        Returns:
            Whether the signed-in user is staff.
        """
        return bool(getattr(self.request.user, "is_staff", False))

    def get_options(self, preview: EmailPreview | None = None) -> dict[str, str]:
        """Read the controls from the query string, ignoring values they do not offer.

        Args:
            preview: The selected email. Without a plain-text template, ``part`` stays ``html``.

        Returns:
            The value of each control, and ``lang`` when ``settings.LANGUAGES`` offers a choice.
        """
        query = self.request.GET
        options = {
            key: query[key] if query.get(key) in values else values[0]
            for key, values in self.choices.items()
        }
        if preview is not None and not preview.text:
            options["part"] = "html"
        options["lang"] = (
            query["lang"]
            if query.get("lang") in dict(settings.LANGUAGES)
            else translation.get_language()
        )
        return options

    def render_parts(self, preview: EmailPreview, language: str) -> dict[str, str]:
        """Render an email's templates in a language.

        Args:
            preview: The email to render.
            language: The language code to render it in.

        Returns:
            ``subject`` (one line), ``html`` and ``text``; the two a template is missing for are empty.

        Raises:
            TemplateDoesNotExist: If a template the email names does not exist.
        """
        context = {**preview.context, "request": self.request}
        with translation.override(language):

            def render(name: str | None) -> str:
                return (
                    render_to_string(name, context, request=self.request)
                    if name
                    else ""
                )

            return {
                "subject": " ".join(render(preview.subject).split()),
                "html": render(preview.template),
                "text": render(preview.text),
            }


class EmailPreviewView(EmailPreviewMixin, MVPTemplateView):
    """The list of previews beside the selected email."""

    template_name = "mvp/email/preview.html"

    def get_page_title(self) -> str:
        """Name the page.

        Returns:
            The page title.
        """
        return _("Emails")

    def get_page_lead(self) -> str:
        """Describe the page.

        Returns:
            The sentence under the title.
        """
        return _("Every email with a preview, rendered as it will be sent.")

    def link(self, **change: str) -> str:
        """The page's own query string with some values changed.

        Args:
            **change: The query values to set.

        Returns:
            A query string beginning with ``?``.
        """
        query = self.request.GET.copy()
        for key, value in change.items():
            query[key] = value
        return "?" + query.urlencode()

    def get_toggles(
        self, preview: EmailPreview, options: dict[str, str]
    ) -> list[dict[str, Any]]:
        """The controls the page offers for an email.

        Args:
            preview: The selected email.
            options: The current value of each control.

        Returns:
            One dict per control: its ``key``, ``label`` and ``choices``, each choice with its
            ``value``, ``text``, ``url`` and whether it is ``active``.
        """
        parts = [("html", _("HTML"))] + (
            [("text", _("Plain text"))] if preview.text else []
        )
        controls = [
            ("part", _("Part"), parts),
            (
                "scheme",
                _("Colour scheme"),
                [("light", _("Light")), ("dark", _("Dark"))],
            ),
            ("images", _("Images"), [("on", _("Shown")), ("off", _("Blocked"))]),
            ("width", _("Width"), [("desktop", _("Desktop")), ("phone", _("Phone"))]),
        ]
        if len(settings.LANGUAGES) > 1:
            controls.append(("lang", _("Language"), list(settings.LANGUAGES)))
        return [
            {
                "key": key,
                "label": label,
                "choices": [
                    {
                        "value": value,
                        "text": text,
                        "url": self.link(email=preview.template, **{key: value}),
                        "active": options[key] == value,
                    }
                    for value, text in choices
                ],
            }
            for key, label, choices in controls
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the previews, the selected one rendered, and the controls.

        Args:
            **kwargs: The context the parent view built.

        Returns:
            The context, with ``rendered`` or ``error`` set for the selected email.
        """
        context = super().get_context_data(**kwargs)
        previews = EmailPreview.all()
        selected = EmailPreview.get(self.request.GET.get("email", "")) or (
            previews[0] if previews else None
        )
        options = self.get_options(selected)
        context.update(
            previews=previews,
            selected=selected,
            opts=options,
            toggles=[],
            email_links=[],
        )
        if selected is None:
            return context
        try:
            context["rendered"] = self.render_parts(selected, options["lang"])
        except Exception as error:
            context["error"] = f"{type(error).__name__}: {error}"
        context["frame_url"] = reverse(
            "mvp-email-preview-frame", args=[selected.template]
        ) + self.link(email=selected.template)
        context["toggles"] = self.get_toggles(selected, options)
        context["email_links"] = [
            {
                "preview": preview,
                "url": self.link(email=preview.template),
                "active": preview == selected,
            }
            for preview in previews
        ]
        return context


class EmailPreviewFrameView(EmailPreviewMixin, View):
    """One email's HTML, for the page to show in an iframe."""

    def get(self, request: HttpRequest, template: str) -> HttpResponse:
        """Render an email's HTML, as a mail client in the chosen scheme would show it.

        Args:
            request: The request.
            template: The full name of the email's HTML template.

        Returns:
            The HTML. In the dark scheme the dark rules apply at any width, and with images
            blocked every ``src`` is empty.

        Raises:
            Http404: If no preview was registered for ``template``.
        """
        preview = EmailPreview.get(template)
        if preview is None:
            raise Http404
        options = self.get_options(preview)
        html = self.render_parts(preview, options["lang"])["html"]
        if options["scheme"] == "dark":
            html = html.replace("@media (prefers-color-scheme: dark)", "@media all")
        if options["images"] == "off":
            html = SRC_ATTRIBUTE.sub('src=""', html)
        return HttpResponse(html)
