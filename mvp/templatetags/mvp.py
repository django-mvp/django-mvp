"""Template tags and filters for MVP navbar widgets."""

import textwrap

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.module_loading import import_string
from django_cotton.compiler_regex import CottonCompiler

from ..config import MVP_CONFIG

register = template.Library()

compiler = CottonCompiler()

# Tailwind breakpoints supported for sidebar expansion. Maps breakpoint name to
# (drawer-open variant class, min-width in px). The class strings must stay in
# sync with the @source inline() safelist in assets/tailwind.css.
SIDEBAR_BREAKPOINTS = {
    "sm": ("sm:drawer-open", 640),
    "md": ("md:drawer-open", 768),
    "lg": ("lg:drawer-open", 1024),
    "xl": ("xl:drawer-open", 1280),
    "2xl": ("2xl:drawer-open", 1536),
}


@register.simple_tag
def sidebar_breakpoint_class(bp):
    """Return the drawer-open variant class for a configured sidebar breakpoint.

    Falls back to the ``lg`` breakpoint for unknown values.
    """
    return SIDEBAR_BREAKPOINTS.get(bp, SIDEBAR_BREAKPOINTS["lg"])[0]


@register.simple_tag
def breakpoint_px(bp):
    """Return the min-width in pixels for a configured sidebar breakpoint."""
    return SIDEBAR_BREAKPOINTS.get(bp, SIDEBAR_BREAKPOINTS["lg"])[1]


@register.simple_tag
def avatar_url(user, size):
    """Returns the URL for a user's avatar image for a given size. Size is specified as "sm", "md", "lg", etc. The actual implementation is determined by the MVP_AVATAR_URL_FUNCTION setting, which should point to a function that accepts a user and size and returns a URL string.

    Note: The default implementation of avatar_url returns None, which will cause the avatar component to fall back to displaying an anonymouse user svg icon.
    """
    func = import_string(MVP_CONFIG["brand"]["avatar_resolver"])
    return func(user, size)


@register.simple_tag(takes_context=True)
def logo_url(context, height, theme="light"):
    """Returns the URL for the brand logo image for a given height and theme.

    The resolver callable is determined by the MVP_LOGO_RESOLVER setting, which
    should point to a function that accepts (request, height, theme) and returns
    a URL string or None. Defaults to mvp.utils.logo_url (light-theme fallback
    for all themes — no dark logo asset is bundled).

    Raises ImproperlyConfigured if MVP_LOGO_RESOLVER is set to a non-existent
    import path. Returns "" silently if the resolver raises a runtime exception.
    """
    try:
        func = import_string(MVP_CONFIG["brand"]["logo_resolver"])
    except ImportError as exc:
        raise ImproperlyConfigured(
            f"MVP_CONFIG['brand']['logo_resolver'] '{MVP_CONFIG['brand']['logo_resolver']}' could not be imported: {exc}"
        ) from exc
    try:
        result = func(context.get("request"), height, theme)
    except Exception:
        return ""
    return result if result is not None else ""


@register.simple_tag(takes_context=True)
def icon_url(context, height, theme="light"):
    """Returns the URL for the brand icon image for a given height and theme.

    The resolver callable is determined by the MVP_ICON_RESOLVER setting, which
    should point to a function that accepts (request, height, theme) and returns
    a URL string or None. Defaults to mvp.utils.icon_url (light/dark routing via
    icon_light.svg / icon_dark.svg; falls back to icon.svg for unknown themes).

    Raises ImproperlyConfigured if MVP_ICON_RESOLVER is set to a non-existent
    import path. Returns "" silently if the resolver raises a runtime exception.
    """
    try:
        func = import_string(MVP_CONFIG["brand"]["icon_resolver"])
    except ImportError as exc:
        raise ImproperlyConfigured(
            f"MVP_CONFIG['brand']['icon_resolver'] '{MVP_CONFIG['brand']['icon_resolver']}' could not be imported: {exc}"
        ) from exc
    try:
        result = func(context.get("request"), height, theme)
    except Exception:
        return ""
    return result if result is not None else ""


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


@register.simple_tag(takes_context=True)
def resolve_attr(context, options, default=""):
    """In django-cotton, we often want to modify the behavior or look of a component by specifying boolean attrs on the component. If there are multiple options, the canonical way is to declare size="xs", size="sm", size="md", etc."""
    # attrs are all the attributes passed directly to a component
    attrs = context.get("attrs", {})
    if not attrs:
        return options.get("default")

    for option in options:
        # if the option is present in attrs and has a truthy value, return it. This allows for affirmative and negative booleans.
        if attrs.get(option):
            return attrs[option]

    return options.get("default")


@register.simple_tag
def responsive(var, klass):
    """Returns a base class if the var is True, and a responsive class variant if the var is a string.

    E.g., responsive(True, "divider-horizontal") -> "divider-horizontal"
          responsive("md", "divider-horizontal") -> "md:divider-horizontal"

    """
    if var is True:
        return klass
    elif isinstance(var, str):
        return f"{var}:{klass}"

    return ""  # Return empty string if var is falsy or not a string/boolean


@register.simple_tag
def variation(var, klass, allowed):
    """Returns a base class if the var is True, and a responsive class variant if the var is a string.

    E.g., responsive(True, "divider-horizontal") -> "divider-horizontal"
          responsive("md", "divider-horizontal") -> "md:divider-horizontal"

    """
    if isinstance(allowed, str):
        allowed = allowed.split(",")

    if var in allowed:
        return f"{klass}-{var}"

    return ""


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
