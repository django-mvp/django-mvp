"""Template tags and filters for MVP navbar widgets."""

import textwrap

from django import template
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django_cotton.compiler_regex import CottonCompiler

from ..config import MVP_AVATAR_URL_FUNC, MVP_ICON_URL_FUNC, MVP_LOGO_URL_FUNC

register = template.Library()

compiler = CottonCompiler()


@register.simple_tag(takes_context=True)
def avatar_url(context, size):
    """Returns the URL for a user's avatar image for a given size. Size is specified as "sm", "md", "lg", etc. The actual implementation is determined by the MVP_AVATAR_URL_FUNCTION setting, which should point to a function that accepts a user and size and returns a URL string.

    Note: The default implementation of avatar_url returns None, which will cause the avatar component to fall back to displaying an anonymouse user svg icon.
    """
    func = import_string(MVP_AVATAR_URL_FUNC)
    return func(context.request, size)


@register.simple_tag(takes_context=True)
def logo_url(context, height, theme="light"):
    """Returns the URL for a user's avatar image for a given size. Size is specified as "sm", "md", "lg", etc. The actual implementation is determined by the MVP_AVATAR_URL_FUNCTION setting, which should point to a function that accepts a user and size and returns a URL string.

    Note: The default implementation of avatar_url returns None, which will cause the avatar component to fall back to displaying an anonymouse user svg icon.
    """
    func = import_string(MVP_LOGO_URL_FUNC)
    return func(context.request, height, theme)


@register.simple_tag(takes_context=True)
def icon_url(context, height, theme="light"):
    """Returns the URL for a user's avatar image for a given size. Size is specified as "sm", "md", "lg", etc. The actual implementation is determined by the MVP_AVATAR_URL_FUNCTION setting, which should point to a function that accepts a user and size and returns a URL string.

    Note: The default implementation of avatar_url returns None, which will cause the avatar component to fall back to displaying an anonymouse user svg icon.
    """
    func = import_string(MVP_ICON_URL_FUNC)
    return func(context.request, height, theme)


@register.simple_tag(takes_context=True)
def render_list_item(context, item, template_name):
    new = {}
    # Always provide a generic name
    new["object"] = item

    if hasattr(item, "_meta"):
        # If it's a model, provide the model-specific name
        name = item._meta.model_name
        new["model"] = item._meta  # provide the model meta class, can be useful.
    else:
        name = item.__class__.__name__.lower()

    new[name] = item

    return render_to_string(template_name, new)


@register.filter
def slot_is_empty(slot):
    if isinstance(slot, str):
        return slot.strip() == ""


@register.simple_tag
def slot_exists(*args):
    """Accepts any number of slots and returns True if any are non-empty."""
    return any(not slot_is_empty(slot) for slot in args)


@register.simple_tag(takes_context=True)
def responsive(context, root: str):
    # The idea is to take a root class name (e.g., "col") and
    # and generate responsive variants based on context variables xs, sm, md, lg, xl, xxl).
    # If a context variable is present, the value should be added to root along with the responsive
    # name (e.g., "col-md-6").

    responsive_values = {
        responsive: context.get(responsive)
        for responsive in ["xs", "sm", "md", "lg", "xl", "xxl"]
    }

    return " ".join(
        f"{root}-{key}-{value}"
        for key, value in responsive_values.items()
        if value is not None
    )


@register.tag(name="show_code")
def show_code(parser, token):
    nodelist = parser.parse(("endshow_code",))
    parser.delete_first_token()
    return ShowCodeNode(nodelist)


@register.filter
def nrange(start, end):
    """Generate a range of numbers for iteration in templates.

    Usage:
        {% for i in 0|nrange:5 %}
            {{ i }}  {# Outputs 0, 1, 2, 3, 4 #}
        {% endfor %}
    """
    return range(int(start), int(end))


class ShowCodeNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        raw = self.nodelist.render(context)

        # 1. Normalize indentation
        dedented = textwrap.dedent(raw)

        # 2. Remove leading/trailing blank lines
        cleaned = dedented.strip("\n")

        # 3. Escape for HTML
        escaped = escape(cleaned)

        compiled = compiler.process(cleaned)

        t = template.Template(compiled)
        rendered = t.render(context)
        return render_to_string(
            "cotton/documentation.html", {"code": escaped, "rendered": rendered}
        )
        return rendered
        return mark_safe(f"<pre><code>{escaped}</code></pre>")
