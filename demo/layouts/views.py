"""Demo pages for the layout code: a playground and layouts nested in components."""

from django.template.response import TemplateResponse

from daisy_cotton_layout.view import LayoutView, LayoutViewError
from mvp.views import MVPTemplateView

EXAMPLES = [
    ("lHh LpR lff", "This site's own layout"),
    ("hHh LpR fFf", "Header and footer stay"),
    ("hHh lpr fff", "Only the header stays"),
    ("hhh lpr fff", "Nothing stays"),
    ("lHr LpR lfr", "Both sidebars full height"),
    ("hHh LpR fff", "Footer across the bottom"),
]
COLLAPSES = [
    ("offcanvas", "Slides away"),
    ("icons", "Icon rail"),
    ("none", "Stays open"),
]
BREAKPOINTS = [("sm", "sm · 40rem"), ("md", "md · 48rem"), ("lg", "lg · 64rem"), ("xl", "xl · 80rem"), ("2xl", "2xl · 96rem")]
BEHAVIORS = [
    ("auto", "By breakpoint"),
    ("docked", "Always beside"),
    ("overlay", "Always a drawer"),
]
DEFAULTS = {
    "left": {"collapse": "icons", "breakpoint": "md", "behavior": "auto"},
    "right": {"collapse": "offcanvas", "breakpoint": "lg", "behavior": "auto"},
}


def pick(value, choices, default):
    """The value when it is one of the choices, else the default."""
    return value if value in {key for key, _ in choices} else default


def sidebar_options(params, side):
    """One sidebar's options from the query string."""
    defaults = DEFAULTS[side]
    return {
        "collapse": pick(params.get(f"{side}_collapse"), COLLAPSES, defaults["collapse"]),
        "breakpoint": pick(params.get(f"{side}_breakpoint"), BREAKPOINTS, defaults["breakpoint"]),
        "behavior": pick(params.get(f"{side}_behavior"), BEHAVIORS, defaults["behavior"]),
    }


def settings_snippet(code, left, right):
    """What to put in settings.py for this layout."""
    return (
        "MVP_CONFIG = {\n"
        '    "layout": {\n'
        f'        "view": "{code}",\n'
        '        "sidebar": {\n'
        f'            "collapse": "{left["collapse"]}",\n'
        f'            "breakpoint": "{left["breakpoint"]}",\n'
        f'            "behavior": "{left["behavior"]}",\n'
        "        },\n"
        '        "secondary_sidebar": {\n'
        f'            "collapse": "{right["collapse"]}",\n'
        f'            "breakpoint": "{right["breakpoint"]}",\n'
        f'            "behavior": "{right["behavior"]}",\n'
        "        },\n"
        "    },\n"
        "}"
    )


def markup_snippet(code, left, right):
    """The same layout written as components."""

    def sidebar(side, opts):
        return (
            f'  <c-layout.sidebar side="{side}" collapse="{opts["collapse"]}" '
            f'breakpoint="{opts["breakpoint"]}" behavior="{opts["behavior"]}">\n'
            "    …\n"
            "  </c-layout.sidebar>\n"
        )

    return (
        f'<c-layout view="{code}" container style="height: 32rem">\n'
        "  <c-layout.header>\n"
        '    <c-layout.toggle side="left" /> … <c-layout.toggle side="right" />\n'
        "  </c-layout.header>\n"
        + sidebar("left", left)
        + sidebar("right", right)
        + "  <c-layout.page>…</c-layout.page>\n"
        "  <c-layout.footer>…</c-layout.footer>\n"
        "</c-layout>"
    )


BREAKPOINT_WIDTHS = dict(sm="40rem", md="48rem", lg="64rem", xl="80rem", **{"2xl": "96rem"})


def describe(side, opts):
    """One sentence on how a sidebar opens and closes."""
    name = f"The {side} sidebar"
    if opts["behavior"] == "overlay":
        return f"{name} is a drawer over the page at every width."
    closes = {
        "offcanvas": "slides away when closed",
        "icons": "shrinks to an icon rail when closed",
        "none": "stays open, with no toggle",
    }[opts["collapse"]]
    if opts["behavior"] == "docked":
        return f"{name} {closes}, and stays beside the page at every width."
    width = BREAKPOINT_WIDTHS[opts["breakpoint"]]
    return f"{name} {closes}. Below {width} of layout width it is a drawer over the page."


def preview_context(params):
    """Everything the preview needs, including the refusal for a wrong code."""
    code = params.get("view", EXAMPLES[0][0])
    left = sidebar_options(params, "left")
    right = sidebar_options(params, "right")
    try:
        view = LayoutView.parse(code)
        error = ""
    except LayoutViewError as exc:
        view = None
        error = str(exc)
    return {
        "code": code,
        "view": view,
        "error": error,
        "left": left,
        "right": right,
        "settings_snippet": settings_snippet(view.code, left, right) if view else "",
        "markup_snippet": markup_snippet(view.code, left, right) if view else "",
        "sides": [("left", left), ("right", right)],
        "left_description": describe("left", left),
        "right_description": describe("right", right),
        "examples": EXAMPLES,
        "collapses": COLLAPSES,
        "breakpoints": BREAKPOINTS,
        "behaviors": BEHAVIORS,
        "paragraphs": range(14),
        "nav": [
            ("house", "Home"),
            ("inbox", "Inbox"),
            ("file-text", "Documents"),
            ("chat", "Discussions"),
            ("star", "Starred"),
            ("gear", "Settings"),
        ],
    }


class LayoutCodeView(MVPTemplateView):
    """The playground: type a code, set the sidebars, see the layout."""

    template_name = "layouts/playground.html"
    page_title = "Layout code"

    def get_breadcrumbs(self):
        return [{"text": "Layout"}, {"text": self.page_title}]

    def get(self, request, *args, **kwargs):
        if request.headers.get("HX-Request"):
            context = preview_context(request.GET)
            context["oob"] = True
            return TemplateResponse(request, "layouts/_preview.html", context)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(preview_context(self.request.GET))
        return context


class NestedLayoutsView(MVPTemplateView):
    """Layouts inside a card, a modal and each other."""

    template_name = "layouts/nested.html"
    page_title = "Nested layouts"

    def get_breadcrumbs(self):
        return [{"text": "Layout"}, {"text": self.page_title}]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "folders": [
                    ("inbox", "Inbox", 12),
                    ("star", "Starred", 3),
                    ("send", "Sent", 0),
                    ("file-earmark", "Drafts", 2),
                    ("archive", "Archive", 0),
                    ("trash", "Bin", 0),
                ],
                "mail": [
                    ("Ana Ruiz", "Field season schedule", "The boats are booked for the second week of June, weather permitting.", "09:14", True),
                    ("Kofi Mensah", "Re: core samples", "I've logged the last six cores. Two need re-labelling before they go to the lab.", "08:52", True),
                    ("Lena Vogt", "Budget for the spring workshop", "Attached is the draft. The catering line is still an estimate.", "Yesterday", False),
                    ("Sam Patel", "Instrument calibration", "The thermistor string reads 0.2 °C high at depth. Logged in the notes.", "Yesterday", False),
                    ("Mia Chen", "Paper draft, section 3", "I rewrote the methods to match the new sampling grid.", "Mon", False),
                    ("Jonas Berg", "Shared drive tidy-up", "Old exports moved to the archive folder, nothing deleted.", "Mon", False),
                    ("Ana Ruiz", "Permits", "The coastal permit came through. Copy is in the shared drive.", "Sun", False),
                    ("Priya Nair", "Seminar on Thursday", "Room changed to 2.14, same time.", "Sat", False),
                    ("Tom Ellis", "Data release", "The DOI is minted. Release notes need one more read.", "Fri", False),
                    ("Kofi Mensah", "Lab booking", "We have the cold room from Tuesday to Friday.", "Fri", False),
                ],
                "settings_sections": [
                    ("person", "Profile"),
                    ("bell", "Notifications"),
                    ("shield-lock", "Privacy"),
                    ("palette", "Appearance"),
                    ("key", "Access keys"),
                ],
                "projects": [
                    ("folder", "Coastal survey"),
                    ("folder", "Spring workshop"),
                    ("folder", "Data release 2026"),
                ],
                "documents": ["Overview", "Methods", "Sampling grid", "Results", "Open questions"],
                "comments": [
                    ("Mia Chen", "Should the grid spacing go in a table?"),
                    ("Kofi Mensah", "Core 14 is missing from the list."),
                    ("Lena Vogt", "Cite the 2024 calibration report here."),
                ],
                "products": [
                    ("Sediment corer", "Field", "€1,240"),
                    ("Thermistor string", "Sensors", "€860"),
                    ("Sample bags, 500", "Consumables", "€48"),
                    ("Handheld GPS", "Field", "€310"),
                    ("Conductivity probe", "Sensors", "€540"),
                    ("Cool box, 40 l", "Field", "€95"),
                ],
                "paragraphs": range(6),
            }
        )
        return context
