"""The layout resolver.

``LayoutConfig`` is the single place a sidebar breakpoint name becomes
anything else: a normalised name, a pixel width, or a persistence flag.
"""

#: Supported sidebar breakpoints, mapped to their Tailwind min-width in px.
BREAKPOINT_WIDTHS = {
    "sm": 640,
    "md": 768,
    "lg": 1024,
    "xl": 1280,
    "2xl": 1536,
}

#: Values (case-insensitive) that disable the persistent sidebar entirely:
#: the sidebar stays an off-canvas overlay at every viewport width.
DISABLED_BREAKPOINTS = {"never", "none"}


class LayoutConfig:
    """The shell's resolved layout facts for one render.

    Built from the breakpoint, collapse, sticky and boost values a page has
    already resolved (a component attribute override, or the project's
    ``MVP_CONFIG`` default). Normalisation lives here and nowhere else:
    ``never``/``none`` in any case means the sidebar is never persistent,
    and an unrecognised breakpoint name falls back to ``lg``.
    """

    def __init__(self, bp, collapse=None, sticky=None, boost=None):
        self._raw_breakpoint = bp
        self.collapse = collapse
        self.sticky = sticky
        self.boost = boost

    @property
    def _disabled(self):
        return (
            isinstance(self._raw_breakpoint, str)
            and self._raw_breakpoint.lower() in DISABLED_BREAKPOINTS
        )

    @property
    def breakpoint(self):
        """The normalised breakpoint name: sm, md, lg, xl, 2xl, or never."""
        if self._disabled:
            return "never"
        if self._raw_breakpoint in BREAKPOINT_WIDTHS:
            return self._raw_breakpoint
        return "lg"

    @property
    def persistent(self):
        """Whether the sidebar ever becomes persistent at some width."""
        return not self._disabled

    @property
    def breakpoint_px(self):
        """The breakpoint's width in pixels, or None when never persistent."""
        if self._disabled:
            return None
        return BREAKPOINT_WIDTHS[self.breakpoint]

    def as_dict(self):
        """The payload handed to the client via ``json_script``."""
        return {
            "breakpoint": self.breakpoint,
            "persistent": self.persistent,
            "breakpoint_px": self.breakpoint_px,
            "collapse": self.collapse,
            "sticky": self.sticky,
            "boost": self.boost,
        }
