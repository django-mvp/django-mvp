"""The emails the preview page lists, declared by the packages that send them.

A package declares its emails in an ``email_previews.py`` module, which Django MVP
imports at start-up while ``DEBUG`` is on::

    from mvp.email.previews import register

    register(
        "shop/email/receipt_message.html",
        "Receipt",
        {"total": "€14.28"},
        subject="shop/email/receipt_subject.txt",
        text="shop/email/receipt_message.txt",
        group="Payments",
    )

Django MVP renders what is declared and sends nothing.
"""

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class EmailPreview:
    """One email the preview page can show.

    Attributes:
        template: The full name of the HTML template. It identifies the preview.
        label: What the page's list calls the email.
        context: What the templates are rendered with.
        subject: The full name of the subject template, if the email has one.
        text: The full name of the plain-text template, if the email has one.
        group: The heading the page lists the email under, or an empty string for none.
    """

    template: str
    label: str
    context: dict[str, Any] = field(default_factory=dict)
    subject: str | None = None
    text: str | None = None
    group: str = ""

    registry: ClassVar[dict[str, "EmailPreview"]] = {}

    @classmethod
    def all(cls) -> list["EmailPreview"]:
        """Every registered preview, in the order it was registered.

        Returns:
            The previews.
        """
        return list(cls.registry.values())

    @classmethod
    def get(cls, template: str) -> "EmailPreview | None":
        """Look a preview up by its HTML template.

        Args:
            template: The full name of the HTML template.

        Returns:
            The preview, or ``None`` when nothing was registered for ``template``.
        """
        return cls.registry.get(template)


def register(
    template: str,
    label: str,
    context: dict[str, Any],
    *,
    subject: str | None = None,
    text: str | None = None,
    group: str = "",
) -> EmailPreview:
    """Declare an email for the preview page.

    Registering the same ``template`` again replaces its preview.

    Args:
        template: The full name of the HTML template.
        label: What the page's list calls the email.
        context: What the templates are rendered with.
        subject: The full name of the subject template, if the email has one.
        text: The full name of the plain-text template, if the email has one.
        group: The heading to list the email under.

    Returns:
        The preview that was recorded.
    """
    preview = EmailPreview(template, label, context, subject, text, group)
    EmailPreview.registry[template] = preview
    return preview
