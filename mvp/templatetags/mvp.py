"""Template tags and filters for MVP navbar widgets."""

import hashlib
import textwrap

from django import template
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_cotton.compiler_regex import CottonCompiler

register = template.Library()

compiler = CottonCompiler()


@register.filter
def generate_initials(name):
    """Generate 1-2 character initials from a name.

    Args:
        name: Full name string (e.g., "John Doe", "Madonna", "José García")

    Returns:
        String of 1-2 uppercase letters representing initials

    Examples:
        >>> generate_initials("John Doe")
        'JD'
        >>> generate_initials("Madonna")
        'MA'
        >>> generate_initials("")
        'U'
        >>> generate_initials("O'Brien-Smith")
        'OS'
    """
    if not name or not name.strip():
        return "U"  # Unknown/User fallback

    # Remove special characters and extra whitespace
    clean_name = "".join(c for c in name if c.isalnum() or c.isspace())
    parts = clean_name.strip().split()

    if not parts:
        return "U"

    if len(parts) == 1:
        # Single name: use first 2 letters
        single = parts[0].upper()
        return single[:2] if len(single) >= 2 else single[0]

    # Multiple names: first letter of first and last name
    return (parts[0][0] + parts[-1][0]).upper()


@register.filter
def avatar_color(name):
    """Generate consistent color class for avatar based on name.

    Uses hash of name to deterministically pick from Bootstrap color palette.

    Args:
        name: Name string to generate color for

    Returns:
        Bootstrap background color class (e.g., 'bg-primary', 'bg-success')
    """
    if not name:
        name = "default"

    # Hash the name to get consistent color
    hash_value = int(hashlib.md5(name.encode()).hexdigest(), 16)  # noqa: S324

    # Bootstrap color palette for avatars
    colors = [
        "primary",
        "secondary",
        "success",
        "danger",
        "warning",
        "info",
    ]

    return f"text-bg-{colors[hash_value % len(colors)]}"


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

    responsive_values = {responsive: context.get(responsive) for responsive in ["xs", "sm", "md", "lg", "xl", "xxl"]}

    return " ".join(f"{root}-{key}-{value}" for key, value in responsive_values.items() if value is not None)


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
        return render_to_string("cotton/documentation.html", {"code": escaped, "rendered": rendered})
        return rendered
        return mark_safe(f"<pre><code>{escaped}</code></pre>")
