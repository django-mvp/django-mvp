"""Template tags for HTML email: the site's address and name, and the brand's colours.

An email is read outside the site, so every link and image in it has to be an
absolute address. These tags give a template that address and the site's name
without the sender passing anything but, where it has one, a ``request``.
"""

from dataclasses import replace
from urllib.parse import urljoin, urlsplit

from css_inline import CSSInliner
from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.template import Context
from django.urls import reverse

from mvp.config import MVP_CONFIG
from mvp.email.brand import EmailBrand
from mvp.utils import app_is_installed, site_name

register = template.Library()


class EmailSite:
    """The site as an email has to say it: its absolute address and its name."""

    @staticmethod
    def current():
        """Find the current ``Site``.

        Returns:
            The ``Site`` that ``SITE_ID`` names.

        Raises:
            ImproperlyConfigured: If ``django.contrib.sites`` is not installed, or
                no ``Site`` matches ``SITE_ID``.
        """
        problem = "django.contrib.sites is not installed"
        if app_is_installed("django.contrib.sites"):
            from django.contrib.sites.models import Site

            try:
                return Site.objects.get_current()
            except (Site.DoesNotExist, ImproperlyConfigured):
                problem = "no Site matches SITE_ID"
        raise ImproperlyConfigured(
            f"An email rendered without a request can't tell where the site is: {problem}. "
            "Add django.contrib.sites to INSTALLED_APPS, set SITE_ID, and give that Site "
            "the site's domain, or render the email with a request in its context."
        )

    @staticmethod
    def request_of(context: Context) -> HttpRequest | None:
        """Find the request a template is rendered for.

        Args:
            context: The template context.

        Returns:
            The ``request`` variable, or else the request a ``RequestContext`` holds, which
            it keeps when a component isolates its context; ``None`` outside a request.
        """
        return context.get("request") or getattr(context, "request", None)

    @classmethod
    def address(cls, request) -> str:
        """Find the site's address.

        Args:
            request: The request being answered, or ``None`` when the email is
                rendered outside one.

        Returns:
            The address with a trailing slash. From a request it is the request's
            own scheme and host. Otherwise it is the current ``Site`` over ``https``,
            or ``http`` while ``DEBUG`` is on.

        Raises:
            ImproperlyConfigured: If there is no request and the ``Site`` can't be
                found or has no domain.
        """
        if request is not None:
            return request.build_absolute_uri("/")
        site = cls.current()
        if not site.domain:
            raise ImproperlyConfigured(
                f"The Site that SITE_ID names (id {site.pk}) has an empty domain, "
                "so an email rendered without a request can't tell where the site is. "
                "Give that Site its domain in django.contrib.sites."
            )
        return f"{'http' if settings.DEBUG else 'https'}://{site.domain}/"

    @classmethod
    def name(cls, request) -> str:
        """Find the site's name.

        Args:
            request: The request being answered, or ``None``.

        Returns:
            ``MVP_CONFIG["site_name"]`` when set, otherwise the name of the request's
            or the current ``Site``.

        Raises:
            ImproperlyConfigured: If there is no request and the ``Site`` can't be found.
        """
        if configured := MVP_CONFIG["site_name"]:
            return str(configured)
        if request is not None:
            return site_name(request)
        site = cls.current()
        return site.name or site.domain

    @classmethod
    def absolute(cls, request, target: str, *args, **kwargs) -> str:
        """Make a path or a URL name into an absolute address on the site.

        Args:
            request: The request being answered, or ``None``.
            target: A path, an address, or a URL name.
            *args: Positional arguments for reversing a URL name.
            **kwargs: Keyword arguments for reversing a URL name.

        Returns:
            An address that names a host is returned as it is. A path is joined to
            the site's address. Anything else is reversed as a URL name.

        Raises:
            NoReverseMatch: If ``target`` is a URL name that does not reverse.
            ImproperlyConfigured: If the site's address is needed and can't be found.
        """
        if urlsplit(target).netloc:
            return target
        if not target.startswith("/"):
            target = reverse(target, args=args, kwargs=kwargs)
        return urljoin(cls.address(request), target)


@register.simple_tag(takes_context=True)
def email_url(context: Context, target: str, *args, **kwargs) -> str:
    """Give an absolute address on the site for a path or a URL name.

    Takes a URL name and arguments the way ``{% url %}`` does. An address that
    already names a host is returned unchanged.

    Args:
        context: The template context. Its ``request`` is used when it has one.
        target: A path, an address, or a URL name.
        *args: Positional arguments for reversing a URL name.
        **kwargs: Keyword arguments for reversing a URL name.

    Returns:
        The absolute address.
    """
    return EmailSite.absolute(
        EmailSite.request_of(context), str(target), *args, **kwargs
    )


@register.simple_tag(takes_context=True)
def email_site_name(context: Context) -> str:
    """Give the site's name.

    Args:
        context: The template context. Its ``request`` is used when it has one.

    Returns:
        ``MVP_CONFIG["site_name"]`` when set, otherwise the request's or the current
        ``Site``'s name.
    """
    return EmailSite.name(EmailSite.request_of(context))


@register.simple_tag(takes_context=True)
def email_brand(context: Context) -> EmailBrand:
    """Give the email's light and dark palettes and its logos as absolute addresses.

    Use it with ``as``: ``{% email_brand as brand %}``.

    Args:
        context: The template context. Its ``request`` is used when it has one.

    Returns:
        The brand, with ``logo`` and ``logo_dark`` made absolute.
    """
    request = EmailSite.request_of(context)
    brand = EmailBrand.current()
    return replace(
        brand,
        logo=EmailSite.absolute(request, brand.logo),
        logo_dark=EmailSite.absolute(request, brand.logo_dark)
        if brand.logo_dark
        else None,
    )


class EmailInlineNode(template.Node):
    """Renders its contents, then moves the style block's rules onto the markup they match."""

    #: Rules that can't be inlined, such as ``@media``, stay in the style block.
    inliner = CSSInliner(keep_at_rules=True, load_remote_stylesheets=False)

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context: Context) -> str:
        """Render the contents and inline their styles.

        Args:
            context: The template context.

        Returns:
            The rendered HTML, with each rule in its ``<style>`` blocks written
            into the ``style`` attribute of the elements it matches.
        """
        return self.inliner.inline(self.nodelist.render(context))


@register.tag
def email_inline(parser, token):
    """Inline the styles of everything between ``{% email_inline %}`` and ``{% endemail_inline %}``.

    The contents are rendered first, so blocks a child template fills are
    included. Rules for ``@media`` and other at-rules stay in the style block.
    Stylesheets the markup links to are not fetched.

    Args:
        parser: The template parser.
        token: The tag's token.

    Returns:
        The node that renders and inlines the contents.
    """
    nodelist = parser.parse(("endemail_inline",))
    parser.delete_first_token()
    return EmailInlineNode(nodelist)
