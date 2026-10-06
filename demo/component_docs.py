"""Registry of documented core components.

A single source of truth shared by the documentation views (``views.py``), the
URL configuration (``urls.py``), and the sidebar navigation (``menus.py``). Each
entry drives one documentation page at ``components/<slug>/``.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentDoc:
    """Metadata for a single component documentation page."""

    slug: str
    label: str
    icon: str
    description: str


# Core, developer-facing components — the building blocks for page content.
# Deliberately excludes layout primitives (container/grid/group/section) and app
# chrome (navbar/sidebar/dock/breadcrumbs/menus), which pages provide already.
COMPONENTS = [
    ComponentDoc(
        "text", "Text", "newspaper", "Paragraph text with tone and emphasis modifiers."
    ),
    ComponentDoc(
        "button",
        "Button",
        "check2-square",
        "From daisy-cotton. Actions and links with variants, sizes, and icons.",
    ),
    ComponentDoc(
        "link",
        "Link",
        "link",
        "From daisy-cotton. A styled inline text link, for prose rather than actions.",
    ),
    ComponentDoc(
        "badge", "Badge", "bell", "From daisy-cotton. Compact labels and counts."
    ),
    ComponentDoc(
        "alert",
        "Alert",
        "info-circle",
        "From daisy-cotton. Inline contextual messages.",
    ),
    ComponentDoc("card", "Card", "grid", "A padded surface for grouping content."),
    ComponentDoc(
        "divider",
        "Divider",
        "dash",
        "From daisy-cotton. Separate content, horizontally or vertically.",
    ),
    ComponentDoc("icon", "Icon", "star", "Render any registered icon by name."),
    ComponentDoc(
        "avatar",
        "Avatar",
        "person-circle",
        "User pictures and status dots from this package, and the avatar group "
        "from daisy-cotton.",
    ),
    ComponentDoc(
        "data-field",
        "Data Field",
        "list-ul",
        "A labelled read-only value for detail pages.",
    ),
    ComponentDoc(
        "formset",
        "Formset",
        "list-ul",
        "A whole Django formset: management form, one row per form, and add/remove controls.",
    ),
    ComponentDoc(
        "dropdown", "Dropdown", "list", "A trigger that reveals a floating panel."
    ),
    ComponentDoc("modal", "Modal", "layout", "A dialog overlay opened via JavaScript."),
    ComponentDoc(
        "mockup",
        "Mockup",
        "laptop",
        "From daisy-cotton. Device and browser frames for screenshots.",
    ),
    ComponentDoc(
        "placeholder",
        "Placeholder",
        "grid",
        "Empty-state stand-ins for pending content.",
    ),
]

COMPONENTS_BY_SLUG = {c.slug: c for c in COMPONENTS}
