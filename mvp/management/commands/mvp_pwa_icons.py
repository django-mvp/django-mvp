"""Render the installable app's images from the project's brand mark.

The manifest and page head name four PNGs under ``brand/pwa/`` in static files.
This command draws them from ``brand/icon.svg`` (the file ``mvp.utils.icon_url``
serves), so a change to the mark is one command rather than an image editor::

    python manage.py mvp_pwa_icons

It asks nothing, so it runs in a build pipeline. Run it before ``collectstatic``.
Rendering needs the optional ``resvg-py`` package, which django-mvp does not
depend on.
"""

import base64
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand, CommandError

import mvp
from mvp.config import MVP_CONFIG
from mvp.pwa import IMAGE_DIRECTORY, IMAGES

PACKAGE_STATIC = Path(next(iter(mvp.__path__))).resolve() / "static"
MARK = "brand/icon.svg"

# Image key -> (side in pixels, share of the side the mark fills, opaque?)
# Maskable icons are cropped to a shape by the platform, so the mark stays in
# the central 80% (the W3C safe zone). iOS fills transparency with black.
SPECS = {
    "icon_192": (192, 1.0, False),
    "icon_512": (512, 1.0, False),
    "icon_maskable_512": (512, 0.8, True),
    "apple_touch_icon": (180, 0.8, True),
}


class Command(BaseCommand):
    help = "Render the installable app's images from the project's brand mark."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            help="Static directory to write brand/pwa/ into. "
            "Defaults to the first STATICFILES_DIRS entry without a prefix.",
        )

    def handle(self, *args, **options):
        if not MVP_CONFIG["pwa"]:
            raise CommandError(
                "MVP_CONFIG['pwa'] must be set with a theme_color, "
                "for example {'theme_color': '#ffffff'}."
            )
        try:
            import resvg_py
        except ImportError as error:
            raise CommandError(
                "Rendering the images needs the resvg-py package. "
                "Install it with: pip install resvg-py"
            ) from error

        mark = self.find_mark()
        destination = self.output_root(options["output_dir"]) / IMAGE_DIRECTORY
        destination.mkdir(parents=True, exist_ok=True)
        data = base64.b64encode(mark.read_bytes()).decode("ascii")
        background = MVP_CONFIG["pwa"]["theme_color"]

        for key, (side, share, opaque) in SPECS.items():
            inner = side * share
            offset = (side - inner) / 2
            wrapper = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}">'
                f'<image href="data:image/svg+xml;base64,{data}" x="{offset}" '
                f'y="{offset}" width="{inner}" height="{inner}" '
                'preserveAspectRatio="xMidYMid meet"/></svg>'
            )
            png = resvg_py.svg_to_bytes(
                svg_string=wrapper,
                width=side,
                height=side,
                background=background if opaque else None,
            )
            (destination / IMAGES[key]).write_bytes(bytes(png))
            self.stdout.write(f"Wrote {destination / IMAGES[key]}")

    def find_mark(self):
        found = finders.find(MARK)
        if not found:
            raise CommandError(f"No {MARK} found in the static files.")
        mark = Path(found).resolve()
        if mark.is_relative_to(PACKAGE_STATIC):
            self.stdout.write(
                f"Using the package's own mark ({MARK}); add {MARK} to your "
                "static files to use your own."
            )
        return mark

    @staticmethod
    def output_root(output_dir):
        if output_dir:
            return Path(output_dir)
        # A (prefix, path) entry is served under its prefix, where the
        # manifest never looks, so only an unprefixed entry will do.
        for entry in settings.STATICFILES_DIRS:
            if not isinstance(entry, (list, tuple)):
                return Path(entry)
        raise CommandError(
            "STATICFILES_DIRS has no entry without a prefix; pass --output-dir "
            "to say where to write the images."
        )
