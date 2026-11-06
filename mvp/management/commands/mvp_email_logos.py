"""Render the project's brand logo to the PNG files an email shows.

Mail clients don't draw SVG, so the email shows ``brand/email/logo.png`` and,
for the dark scheme, ``brand/email/logo_dark.png`` in static files. This command
draws them from ``brand/logo.svg`` and ``brand/logo_dark.svg``, so a change to
the logo is one command::

    python manage.py mvp_email_logos

It asks nothing, so it runs in a build pipeline. Run it before ``collectstatic``.
Rendering needs the optional ``resvg-py`` package, which django-mvp does not
depend on.
"""

from pathlib import Path

from django.contrib.staticfiles import finders
from django.core.management.base import BaseCommand, CommandError

from mvp.email.brand import LOGO, LOGO_DARK, LOGO_SOURCE, PACKAGE_STATIC
from mvp.management.commands.mvp_pwa_icons import Command as PwaIconsCommand

SOURCE_DARK = "brand/logo_dark.svg"
HEIGHT = 64


class Command(BaseCommand):
    """Write the email's PNG logos, drawn from the project's brand logos."""

    help = "Render the email's PNG logos from the project's brand logos."

    def add_arguments(self, parser):
        """Add ``--output-dir``."""
        parser.add_argument(
            "--output-dir",
            help="Static directory to write brand/email/ into. "
            "Defaults to the first STATICFILES_DIRS entry without a prefix.",
        )

    def handle(self, *args, **options):
        """Render the logo, and the dark logo when there is one, as PNGs 64 pixels high."""
        try:
            import resvg_py
        except ImportError as error:
            raise CommandError(
                "Rendering the images needs the resvg-py package. Install it with: pip install resvg-py"
            ) from error

        root = PwaIconsCommand.output_root(options["output_dir"])
        sources = [(self.find_source(LOGO_SOURCE), LOGO)]
        if dark := self.find_source(SOURCE_DARK, required=False):
            sources.append((dark, LOGO_DARK))

        for source, target in sources:
            try:
                png = resvg_py.svg_to_bytes(svg_path=str(source), height=HEIGHT)
            except ValueError as error:
                raise CommandError(
                    f"{source} could not be rendered: {error}"
                ) from error
            destination = root / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(bytes(png))
            self.stdout.write(f"Wrote {destination}")

    def find_source(self, name: str, *, required: bool = True) -> Path | None:
        """Return the path of a logo the static files serve.

        Says so when the logo found is the package's own rather than the
        project's.

        Args:
            name: The logo's path in static files.
            required: Whether a logo that is not found stops the command.

        Returns:
            The resolved path, or ``None`` when the logo is not found and not required.

        Raises:
            CommandError: The logo is required and is not in the static files.
        """
        found = finders.find(name)
        if not found:
            if required:
                raise CommandError(f"No {name} found in the static files.")
            return None
        logo = Path(found).resolve()
        if logo.is_relative_to(PACKAGE_STATIC):
            self.stdout.write(
                f"Using the package's own logo ({name}); add {name} to your static files to use your own."
            )
        return logo
