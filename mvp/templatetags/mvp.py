"""Template tags and filters for MVP navbar widgets."""

import textwrap

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
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

# Breakpoint values (case-insensitive) that disable the persistent sidebar
# entirely: the sidebar is an off-canvas overlay at every viewport width.
NO_BREAKPOINT_VALUES = {"never", "none"}


def _breakpoint_disabled(bp):
    return isinstance(bp, str) and bp.lower() in NO_BREAKPOINT_VALUES


@register.simple_tag
def sidebar_has_breakpoint(bp):
    """Return whether the sidebar becomes persistent at some viewport width.

    False when the breakpoint is set to "never" (or "none"), meaning the
    sidebar stays an off-canvas overlay at every width.
    """
    return not _breakpoint_disabled(bp)


@register.simple_tag
def sidebar_breakpoint_class(bp):
    """Return the drawer-open variant class for a configured sidebar breakpoint.

    Returns "" for the "never"/"none" breakpoint (the sidebar never becomes
    persistent). Falls back to the ``lg`` breakpoint for unknown values.
    """
    if _breakpoint_disabled(bp):
        return ""
    return SIDEBAR_BREAKPOINTS.get(bp, SIDEBAR_BREAKPOINTS["lg"])[0]


@register.simple_tag
def breakpoint_px(bp):
    """Return the min-width in pixels for a configured sidebar breakpoint."""
    return SIDEBAR_BREAKPOINTS.get(bp, SIDEBAR_BREAKPOINTS["lg"])[1]


@register.simple_tag
def sidebar_navbar_toggle_class(bp, collapse):
    """Return visibility classes for the navbar's sidebar-toggle button.

    Below the sidebar breakpoint the toggle is always shown (the sidebar is an
    off-canvas overlay there). At or above it, the sidebar header carries its
    own toggle, so the navbar one is hidden: always in ``icons`` mode (the
    collapsed rail still shows a toggle on hover), and only while the drawer
    is open in ``offcanvas`` mode (a fully hidden sidebar has no toggle left).

    With the "never"/"none" breakpoint the sidebar is an overlay everywhere,
    so the navbar toggle is always shown (the open overlay covers the navbar).

    The emitted classes must stay in sync with the @source inline() safelist
    in mvp/tailwind/base.css.
    """
    if _breakpoint_disabled(bp):
        return ""
    prefix = bp if bp in SIDEBAR_BREAKPOINTS else "lg"
    if collapse == "icons":
        return f"{prefix}:hidden"
    return f"{prefix}:is-drawer-open:hidden"


@register.simple_tag
def table_cell_attrs(column, cell="td"):
    """Return a django-tables2 column's rendered cell attributes, with the
    project's wrap default filled in when the column names neither
    "mvp-col-wrap" nor "mvp-col-nowrap" of its own (issue #255).

    Resolution order: the column's own class (already present in
    ``column.attrs[cell]``), then ``MVP_CONFIG["table"]["wrap"]``, then the
    package default (no wrap). The emitted class must stay in sync with the
    behaviour classes safelisted in mvp/tailwind/base.css.
    """
    attrs = column.attrs[cell]
    classes = (attrs.get("class") or "").split()
    if "mvp-col-wrap" not in classes and "mvp-col-nowrap" not in classes:
        classes.append(
            "mvp-col-wrap" if MVP_CONFIG["table"]["wrap"] else "mvp-col-nowrap"
        )
        attrs["class"] = " ".join(classes)
    return attrs.as_html()


@register.simple_tag
def column_alignment_class(column, table):
    """Return the alignment class inferred from a column's model field kind:
    "text-start" for a text field, "text-end" for a numeric one (integer,
    decimal or float), "text-center" for a boolean field or for a column
    with no resolvable field that is not orderable (an action column, e.g.
    buttons — issue #256). Returns "" — no alignment imposed — when the
    table's data has no model to resolve a field from, or when a column is
    unresolvable but still orderable, since its kind cannot be determined
    (FR-017, FR-018, FR-021).

    Takes the table as well as the column because ``BoundColumn._table`` is
    private and unreachable from a template (research R2). Returns "" and
    leaves the column untouched when its already-computed classes already
    carry one of the three alignment classes, so an explicit class in the
    column's own attrs wins (FR-019) and the tag stays idempotent. The
    emitted class must stay in sync with the text-{start,center,end}
    classes already safelisted in mvp/tailwind/base.css.
    """
    model = table.data.model
    if model is None:
        return ""

    from django_tables2.utils import Accessor

    field = Accessor(column.accessor).get_field(model)
    if field is None:
        klass = "text-center" if not column.orderable else ""
    elif isinstance(field, models.BooleanField):
        klass = "text-center"
    elif isinstance(
        field, (models.IntegerField, models.DecimalField, models.FloatField)
    ):
        klass = "text-end"
    else:
        klass = "text-start"

    if not klass:
        return ""

    existing = " ".join(
        column.attrs[cell].get("class") or "" for cell in ("td", "th")
    ).split()
    if any(c in existing for c in ("text-start", "text-center", "text-end")):
        return ""

    return klass


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
    elif isinstance(var, str) and var:
        return f"{var}:{klass}"

    return ""  # Return empty string if var is falsy (incl. "") or not a string/boolean


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
    """Render a live component example three ways for documentation pages.

    The captured block is expected to contain *literal* Cotton markup — wrap it in
    ``{% cotton:verbatim %}`` on the page so django-cotton does not compile it away
    before it reaches this tag. The node then produces:

    - ``code``: the escaped Cotton source (the "Cotton" tab)
    - ``rendered``: the live, compiled component (the preview)
    - ``html``: the escaped, prettified HTML the component renders to (the "HTML" tab)

    These are handed to ``cotton/documentation.html`` for display.
    """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        raw = self.nodelist.render(context)

        # Normalize indentation and trim surrounding blank lines so the snippet
        # reads cleanly regardless of how it was indented on the page.
        cleaned = textwrap.dedent(raw).strip("\n")

        # The Cotton source, escaped for display in the "Cotton" tab.
        code = escape(cleaned)

        # Compile the Cotton source and render it for the live preview.
        rendered_raw = template.Template(compiler.process(cleaned)).render(context)

        # Prettify the resulting HTML for the "HTML" tab when BeautifulSoup is
        # available; fall back to the raw output otherwise.
        try:
            from bs4 import BeautifulSoup

            html_pretty = BeautifulSoup(rendered_raw, "html.parser").prettify()
        except ImportError:
            html_pretty = rendered_raw.strip()

        return render_to_string(
            "cotton/documentation.html",
            {
                "code": code,
                "rendered": mark_safe(rendered_raw),
                "html": escape(html_pretty),
            },
        )


@register.filter
def formset_row_label(form):
    """Return a human label for one formset row.

    A row usually edits a related object, and the page is much easier to read
    when it says which one. A saved row shows the object's own string; an
    unsaved row has nothing meaningful to show, since ``str()`` on an
    unsaved model gives ``Thing object (None)``, so it is named by its model
    instead.

    Returns an empty string for a plain (non-model) form, which has no
    instance to name.
    """
    instance = getattr(form, "instance", None)
    if instance is None or not hasattr(instance, "_meta"):
        return ""
    if instance.pk:
        return str(instance)
    return _("New %(model)s") % {"model": instance._meta.verbose_name}


@register.filter
def formset_label(formset):
    """Return the default heading for a set: its model's plural name.

    Used when the developer sets no title of their own. A plain (non-model)
    formset has no model to name and gets no default.
    """
    model = getattr(formset, "model", None)
    if model is None:
        return ""
    return model._meta.verbose_name_plural.title()


@register.filter
def any_multipart(formsets):
    """Return True when any set in the list needs multipart encoding.

    The form component decides the page's encoding from the parent form and
    every set together, and emits one attribute however many of them need it.
    Testing each set inside the tag instead would write the attribute once per
    multipart set, which browsers accept and the markup contract does not.
    """
    return any(formset.is_multipart() for formset in formsets or [])
