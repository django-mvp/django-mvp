"""Template tags and filters for MVP navbar widgets."""

import textwrap
from typing import Any

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field
from django import template
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.forms import CheckboxInput
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_cotton.compiler_regex import CottonCompiler

from .. import utils
from ..config import MVP_CONFIG
from ..layout import BREAKPOINT_WIDTHS, LayoutConfig

register = template.Library()

compiler = CottonCompiler()

# Tailwind breakpoints supported for sidebar expansion. Maps breakpoint name to
# (drawer-open variant class, min-width in px). The widths come from
# mvp.layout, which is where a breakpoint name becomes anything else — writing
# them again here is how the two drift. The class strings must stay in sync
# with the @source inline() safelist in mvp/tailwind/base.css.
SIDEBAR_BREAKPOINTS = {
    name: (f"{name}:drawer-open", width) for name, width in BREAKPOINT_WIDTHS.items()
}


@register.simple_tag
def sidebar_has_breakpoint(bp):
    """Return whether the sidebar becomes persistent at some viewport width.

    False when the breakpoint is set to "never" (or "none"), meaning the
    sidebar stays an off-canvas overlay at every width.
    """
    return LayoutConfig(bp).persistent


@register.simple_tag
def sidebar_breakpoint_class(bp):
    """Return the drawer-open variant class for a configured sidebar breakpoint.

    Returns "" for the "never"/"none" breakpoint (the sidebar never becomes
    persistent). Falls back to the ``lg`` breakpoint for unknown values.
    """
    config = LayoutConfig(bp)
    if not config.persistent:
        return ""
    return SIDEBAR_BREAKPOINTS[config.breakpoint][0]


@register.simple_tag
def breakpoint_px(bp):
    """Return the min-width in pixels for a configured sidebar breakpoint.

    Returns the ``lg`` width (1024) for the "never"/"none" breakpoint: it is
    not a recognised breakpoint name, so it takes the same fallback an
    unrecognised name does. This is a deliberate, pre-existing behaviour of
    the tag, distinct from ``LayoutConfig.breakpoint_px``, which reports
    ``None`` for "never" — the honest value the client payload needs.
    """
    return SIDEBAR_BREAKPOINTS.get(
        LayoutConfig(bp).breakpoint, SIDEBAR_BREAKPOINTS["lg"]
    )[1]


@register.simple_tag
def resolve_layout_config(bp, collapse, sticky, boost):
    """Resolve one LayoutConfig for a template's layout facts and client payload."""
    return LayoutConfig(bp, collapse, sticky, boost)


#: The alignment classes the inference emits, and the ones an author declares
#: to override it. Kept in sync with the text-{start,center,end} classes
#: safelisted in mvp/tailwind/base.css.
ALIGNMENT_CLASSES = ("text-start", "text-center", "text-end")

#: The three cell kinds django-tables2 gives every bound column.
CELL_KINDS = ("th", "td", "tf")


@register.simple_tag
def table_cell_attrs(column, table, cell="td", wrap=True):
    """Return a django-tables2 column's cell attributes, wrap and alignment filled in.

    Fills in the project's wrap default when the column names neither
    "mvp-col-wrap" nor "mvp-col-nowrap" of its own (issue #255), and the
    inferred alignment class when the column declares none of its own
    (issue #256).

    Resolution order for wrap: the column's own class (already present in
    ``column.attrs[cell]``), then ``MVP_CONFIG["table"]["wrap"]``, then the
    package default (no wrap). Pass ``wrap=False`` for a heading cell: a
    heading is a short label the author chose, and letting it wrap keeps a
    column from being widened by its own title, where cell data is
    arbitrary-length and holding it to one line is what keeps rows scannable.
    The emitted classes must stay in sync with the behaviour and
    text-{start,center,end} classes safelisted in mvp/tailwind/base.css.
    """
    declared = column.attrs
    attrs = declared[cell]
    classes = (attrs.get("class") or "").split()

    if wrap and "mvp-col-wrap" not in classes and "mvp-col-nowrap" not in classes:
        classes.append(
            "mvp-col-wrap" if MVP_CONFIG["table"]["wrap"] else "mvp-col-nowrap"
        )

    align = column_alignment_class(column, table, cell=cell, declared=declared)
    if align:
        classes.append(align)

    if classes:
        attrs["class"] = " ".join(classes)
    return attrs.as_html()


@register.simple_tag
def column_alignment_class(column, table, cell="td", declared=None):
    """Return the alignment class for a column's cell, inferred from its model field.

    "text-start" for a text field, "text-end" for a numeric one (integer,
    decimal or float), "text-center" for a boolean field or for a column
    with no resolvable field that is not orderable (an action column, e.g.
    buttons — issue #256). Returns "" — no alignment imposed — when the
    table's data has no model to resolve a field from, or when a column is
    unresolvable but still orderable, since its kind cannot be determined
    (FR-017, FR-018, FR-021).

    Takes the table as well as the column because ``BoundColumn._table`` is
    private and unreachable from a template (research R2).

    An alignment class the author declared wins over the inference (FR-019),
    and every cell of the column takes the same one, so a heading always sits
    over cells aligned the way it is (FR-020). Declaring ``text-end`` on the
    ``td`` alone is the usual way it is written, and it must not leave the
    heading on the inferred alignment or, worse, on none at all. So: a cell
    that already carries the declared class gets "" back and is left alone,
    and every other cell of that column is given the same class rather than an
    inferred one.

    ``declared`` is ``column.attrs`` when the caller has already resolved it.
    That property rebuilds all three cell dicts on every access and runs any
    callable a project put in ``attrs``, so passing it keeps a render to one
    evaluation per cell rather than two.
    """
    if declared is None:
        declared = column.attrs

    own = (declared[cell].get("class") or "").split()
    if any(c in own for c in ALIGNMENT_CLASSES):
        return ""

    for other in CELL_KINDS:
        if other == cell:
            continue
        for klass in (declared[other].get("class") or "").split():
            if klass in ALIGNMENT_CLASSES:
                return klass

    model = table.data.model
    if model is None:
        return ""

    from django_tables2.utils import Accessor

    field = Accessor(column.accessor).get_field(model)
    if field is None:
        return "text-center" if not column.orderable else ""
    if isinstance(field, models.BooleanField):
        return "text-center"
    if isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
        return "text-end"
    return "text-start"


@register.simple_tag
def row_header_columns(table):
    """Return the column names a table declares as row headers.

    Declared as (issue #320)::

        class SampleTable(tables.Table):
            class Meta:
                row_headers = ("dataset", "location")

    A column named here has its body cells rendered as ``<th scope="row">``
    rather than ``<td>``. A column that identifies the row — an icon linking
    to the record, a name, a reference — is a row header, and that is the
    markup a screen reader announces the rest of the row against. It is also
    what daisyUI's ``table-pin-cols`` selects on, so a column declared here
    is one that can be kept in view while a wide table scrolls sideways.

    Declared on the table rather than on the column, because whether a column
    identifies a row is a fact about the table: the same column class is
    reused across tables where it identifies in one and not in the other.
    Naming columns on ``Meta`` is also how django-tables2 already spells
    ``fields``, ``sequence`` and ``exclude``, and it works for every column
    class without asking a project to subclass one.

    A single name may be given as a plain string, because a string is itself
    a sequence and taking one at face value would test every column against
    its characters. A name that is no column of this table raises, rather
    than being dropped the way django-tables2 drops any ``Meta`` option it
    does not recognise — a declaration that quietly does nothing is the
    failure this feature exists to remove.
    """
    declared = getattr(getattr(table, "Meta", None), "row_headers", ())
    names = (declared,) if isinstance(declared, str) else tuple(declared)

    unknown = [name for name in names if name not in table.base_columns]
    if unknown:
        named = ", ".join(repr(name) for name in unknown)
        verb = "name" if len(unknown) > 1 else "names"
        columns = ", ".join(table.base_columns)
        raise ImproperlyConfigured(
            f"{type(table).__name__} declares row_headers {named}, which "
            f"{verb} no column of the table. Its columns are: {columns}."
        )
    return names


@register.filter
def app_is_installed(app_name):
    """Return whether an app is installed, for use inside ``{% if %}``.

    Example::

        {% load mvp %}
        {% if "allauth.mfa"|app_is_installed %}
          ...
        {% endif %}

    Wraps ``mvp.utils.app_is_installed`` unchanged.
    """
    return utils.app_is_installed(app_name)


@register.simple_tag
def avatar_url(user: Any, size: str):
    """Return the URL for a user's avatar image at a given size.

    The implementation is resolved from the ``MVP_AVATAR_URL_FUNCTION``
    setting, a callable accepting a user and size and returning a URL
    string. The default implementation returns ``None``, which falls back
    to an anonymous-user SVG icon in the avatar component.

    Args:
        user: The user to resolve an avatar for.
        size: Size keyword, e.g. "sm", "md", "lg".

    Returns:
        The avatar image URL, or ``None`` if unresolved.
    """
    func = import_string(MVP_CONFIG["brand"]["avatar_resolver"])  # type: ignore[index]
    return func(user, size)


@register.simple_tag(takes_context=True)
def logo_url(context: template.Context, height: int, theme: str = "light"):
    """Return the URL for the brand logo image at a given height and theme.

    The resolver callable is read from the ``MVP_LOGO_RESOLVER`` setting,
    accepting ``(request, height, theme)`` and returning a URL string or
    ``None``. Defaults to ``mvp.utils.logo_url`` (light-theme fallback for
    all themes — no dark logo asset is bundled).

    Args:
        context: The template context, used to read the request.
        height: Requested logo height.
        theme: "light" or "dark".

    Returns:
        The logo image URL, or "" if unresolved or the resolver errors.

    Raises:
        ImproperlyConfigured: ``MVP_LOGO_RESOLVER`` names a non-existent
            import path.
    """
    try:
        func = import_string(MVP_CONFIG["brand"]["logo_resolver"])  # type: ignore[index]
    except ImportError as exc:
        raise ImproperlyConfigured(
            f"MVP_CONFIG['brand']['logo_resolver'] '{MVP_CONFIG['brand']['logo_resolver']}' could not be imported: {exc}"  # type: ignore[index]
        ) from exc
    try:
        result = func(context.get("request"), height, theme)
    except Exception:
        return ""
    return result if result is not None else ""


@register.simple_tag(takes_context=True)
def icon_url(context: template.Context, height: int, theme: str = "light"):
    """Return the URL for the brand icon image at a given height and theme.

    The resolver callable is read from the ``MVP_ICON_RESOLVER`` setting,
    accepting ``(request, height, theme)`` and returning a URL string or
    ``None``. Defaults to ``mvp.utils.icon_url`` (light/dark routing via
    icon_light.svg / icon_dark.svg; falls back to icon.svg for unknown
    themes).

    Args:
        context: The template context, used to read the request.
        height: Requested icon height.
        theme: "light" or "dark".

    Returns:
        The icon image URL, or "" if unresolved or the resolver errors.

    Raises:
        ImproperlyConfigured: ``MVP_ICON_RESOLVER`` names a non-existent
            import path.
    """
    try:
        func = import_string(MVP_CONFIG["brand"]["icon_resolver"])  # type: ignore[index]
    except ImportError as exc:
        raise ImproperlyConfigured(
            f"MVP_CONFIG['brand']['icon_resolver'] '{MVP_CONFIG['brand']['icon_resolver']}' could not be imported: {exc}"  # type: ignore[index]
        ) from exc
    try:
        result = func(context.get("request"), height, theme)
    except Exception:
        return ""
    return result if result is not None else ""


@register.simple_tag(takes_context=True)
def render_list_item(context: template.Context, item: Any, template_name: str):
    """Render one list item template, with ``item`` bound as "object" and by model name.

    Args:
        context: The template context (unused, required by ``takes_context``).
        item: The object to render.
        template_name: The template to render.

    Returns:
        The rendered template as a string.
    """
    new = {}
    new["object"] = item

    if hasattr(item, "_meta"):
        name = item._meta.model_name
        new["model"] = item._meta
    else:
        name = item.__class__.__name__.lower()

    new[name] = item

    return render_to_string(template_name, new)


@register.filter
def slot_is_empty(slot: Any):
    """Return whether a Cotton slot has no content.

    Args:
        slot: The slot value.

    Returns:
        ``True`` if ``slot`` is a blank string, ``False`` if non-blank, or
        ``None`` for a non-string slot.
    """
    if isinstance(slot, str):
        return slot.strip() == ""


@register.simple_tag
def slot_exists(*args):
    """Accepts any number of slots and returns True if any are non-empty."""
    return any(not slot_is_empty(slot) for slot in args)


@register.tag(name="show_code")
def show_code(parser: template.base.Parser, token: template.base.Token):
    """Parse a ``{% show_code %}...{% endshow_code %}`` block into a ``ShowCodeNode``.

    Args:
        parser: The template parser.
        token: The tag's token.

    Returns:
        The node that renders the block's source, preview and HTML.
    """
    nodelist = parser.parse(("endshow_code",))
    parser.delete_first_token()
    return ShowCodeNode(nodelist)


@register.filter
def nrange(start: Any, end: Any):
    """Return a range of numbers for iteration in templates.

    Example::

        {% for i in 0|nrange:5 %}
            {{ i }}  {# Outputs 0, 1, 2, 3, 4 #}
        {% endfor %}

    Args:
        start: The range's start value.
        end: The range's exclusive end value.

    Returns:
        A ``range`` from ``start`` to ``end``.
    """
    return range(int(start), int(end))


@register.simple_tag(takes_context=True)
def resolve_attr(context: template.Context, options: dict, default: str = ""):
    """Return the first component attr present in ``options`` that has a truthy value.

    Lets a Cotton component vary its look by which boolean attr the caller
    set, e.g. ``size="xs"``, ``size="sm"``, ``size="md"``.

    Args:
        context: The template context, read for the component's ``attrs``.
        options: Mapping of option names to their values, including
            "default" for the fallback.
        default: Unused; present for tag-call compatibility.

    Returns:
        The value of the first matching option, or ``options["default"]``.
    """
    attrs = context.get("attrs", {})
    if not attrs:
        return options.get("default")

    for option in options:
        if attrs.get(option):
            return attrs[option]

    return options.get("default")


@register.simple_tag
def responsive(var: bool | str, klass: str):
    """Return ``klass`` unprefixed for ``True``, breakpoint-prefixed for a string.

    Example::

        responsive(True, "divider-horizontal") -> "divider-horizontal"
        responsive("md", "divider-horizontal") -> "md:divider-horizontal"

    Args:
        var: ``True``, a breakpoint name, or a falsy value.
        klass: The base class to emit.

    Returns:
        ``klass``, ``"{var}:{klass}"``, or "" if ``var`` is falsy.
    """
    if var is True:
        return klass
    elif isinstance(var, str) and var:
        return f"{var}:{klass}"

    return ""


@register.simple_tag
def variation(var: Any, klass: str, allowed: str | list):
    """Return ``klass`` suffixed with ``var`` when ``var`` is one of the allowed values.

    Example::

        variation("lg", "btn", "sm,md,lg") -> "btn-lg"

    Args:
        var: The variant value to test.
        klass: The base class to suffix.
        allowed: Allowed values, as a list or a comma-separated string.

    Returns:
        ``"{klass}-{var}"`` if ``var`` is allowed, otherwise "".
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

    These are handed to ``cotton/mvp/documentation.html`` for display.
    """

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        """Render the captured block's source, live preview and prettified HTML."""
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
            "cotton/mvp/documentation.html",
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
def formset_columns(formset):
    """Return the fields a tabular set shows as columns, in render order.

    Read from ``empty_form`` rather than a bound form, because it is the one
    form a set always has: an unbound set with no extras has no rows to read
    the columns off, and under ``can_delete_extra=False`` the fields differ
    between initial and extra rows. ``DELETE`` is excluded for the same reason
    a row does not render it as a field — it drives the remove control, which
    gets a column of its own.
    """
    empty_form = getattr(formset, "empty_form", None)
    if empty_form is None:
        return []
    return [field for field in empty_form.visible_fields() if field.name != "DELETE"]


@register.filter
def formset_grid_style(formset):
    """Return the ``grid-template-columns`` a tabular set's rows share.

    One equal-width track per column plus a narrow trailing one for the remove
    control, as an inline style rather than a utility class because the column
    count is only known at render time and Tailwind emits classes it can find
    as literal text at build time.

    Every row is its own grid rather than the set being one grid with rows
    spanning it: ``minmax(0, 1fr)`` tracks resolve identically across sibling
    grids of the same width, so the columns line up either way, and a row that
    keeps its own box can carry its own hairline, hover state and error line.
    """
    columns = formset_columns(formset)
    if not columns:
        return ""
    tracks = f"repeat({len(columns)}, minmax(0, 1fr))"
    if getattr(formset, "can_delete", False):
        tracks = f"{tracks} auto"
    return f"grid-template-columns: {tracks};"


@register.filter
def as_crispy_cell(field):
    """Render one field for a tabular row: the same control, label demoted.

    Goes through crispy's own filter rather than a copy of its template, so a
    cell's control stays identical to the same field on a single form. One
    presentation argument differs:

    ``sm:sr-only`` keeps the label in the document at every width — it is what
    names the input to a screen reader, and a column header does not, because
    nothing associates the two. It only stops being drawn once the layout is
    wide enough for the header row to carry the name for sighted readers.

    A checkbox keeps its label drawn at every width: the template pack draws
    the checkbox inside its label, so hiding one hides the other.
    """
    if isinstance(field.field.widget, CheckboxInput):
        return as_crispy_field(field)
    return as_crispy_field(field, label_class="sm:sr-only")


@register.filter
def any_multipart(formsets):
    """Return True when any set in the list needs multipart encoding.

    The form component decides the page's encoding from the parent form and
    every set together, and emits one attribute however many of them need it.
    Testing each set inside the tag instead would write the attribute once per
    multipart set, which browsers accept and the markup contract does not.
    """
    return any(formset.is_multipart() for formset in formsets or [])
