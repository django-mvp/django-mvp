"""Read the calls a directory of templates makes to daisy-cotton's components.

A call is read from the template as django-cotton compiles it, so a tag that spans
lines, or holds ``>`` or ``%}`` inside an attribute value, is read the way Cotton
reads it. Text inside ``{# #}`` and ``{% comment %}`` never reaches the compiled
output as a tag.
"""

import re
from pathlib import Path

from django.apps import apps
from django.template.base import Lexer, TokenType
from django_cotton.compiler_regex import CottonCompiler
from django_cotton.tag_parser import parse_component_tag


class DaisyCottonCalls:
    """Find the calls a directory of templates makes to daisy-cotton's components.

    A component name is daisy-cotton's when daisy-cotton ships a template for it
    and this package ships none. The name becomes a path the way Cotton makes it:
    dots to slashes, hyphens to underscores, then the ``index.html`` fallback. The
    class holds no list of component names.

    Attributes:
        compiler: The django-cotton compiler templates are read through.
        own_components: The directory of this package's component templates.
        daisy_components: The directory of daisy-cotton's component templates.
        verbatim_markers: The tags that wrap a shown example, opening and closing.
    """

    verbatim_markers = re.compile(r"{%\s*(?:end)?cotton:verbatim\s*%}")

    def __init__(self):
        """Locate the two directories of component templates."""
        self.compiler = CottonCompiler()
        self.own_components = self.components_in("mvp")
        self.daisy_components = self.components_in("daisy_cotton")

    def components_in(self, app_label):
        """Return the directory of component templates an installed app ships.

        Args:
            app_label: The app's label.

        Returns:
            The app's ``templates/cotton`` directory.
        """
        return Path(apps.get_app_config(app_label).path) / "templates" / "cotton"

    def ships(self, directory, name):
        """Tell whether a directory of component templates has one for a name.

        Args:
            directory: The directory holding component templates.
            name: The component name as written in the tag, without ``c-``.

        Returns:
            True when ``<path>.html`` or ``<path>/index.html`` exists there.
        """
        path = name.replace(".", "/").replace("-", "_")
        return (directory / f"{path}.html").is_file() or (
            directory / path / "index.html"
        ).is_file()

    def is_daisy_cotton(self, name):
        """Tell whether a component name is daisy-cotton's.

        Args:
            name: The component name as written in the tag, without ``c-``.

        Returns:
            True when daisy-cotton ships the component and this package does not.
        """
        return self.ships(self.daisy_components, name) and not self.ships(
            self.own_components, name
        )

    def calls(self, directory):
        """Yield every component call in the templates under a directory.

        Args:
            directory: The directory, read recursively for ``*.html`` files.

        Yields:
            A tuple of the template's path, the component name, the names of the
            attributes the call passes, and whether the call carries ``only``.
        """
        for path in sorted(Path(directory).rglob("*.html")):
            yield from self.read(path, path.read_text(encoding="utf-8"))

    def calls_with_examples(self, directory):
        """Yield every component call, including those shown as examples.

        A page that shows markup to a reader wraps it in ``cotton:verbatim`` so
        Cotton leaves the tags alone. Those tags are calls a reader will copy,
        so they are read here as if the wrapper were not there.

        Args:
            directory: The directory, read recursively for ``*.html`` files.

        Yields:
            The same tuple as ``calls``.
        """
        for path in sorted(Path(directory).rglob("*.html")):
            source = self.verbatim_markers.sub("", path.read_text(encoding="utf-8"))
            yield from self.read(path, source)

    def read(self, path, source):
        """Yield every component call in one template's source.

        Args:
            path: The template's path, repeated in each tuple.
            source: The template's source text.

        Yields:
            The same tuple as ``calls``.
        """
        compiled = self.compiler.process(source)
        for token in Lexer(compiled).tokenize():
            if token.token_type != TokenType.BLOCK:
                continue
            if not token.contents.startswith("cotton "):
                continue
            tag = parse_component_tag(token.contents)
            yield path, tag.name, tuple(tag.attrs), tag.only

    def unisolated(self, directory):
        """Yield every call to a daisy-cotton component that lacks ``only``.

        Args:
            directory: The directory, read recursively for ``*.html`` files.

        Yields:
            The same tuple as ``calls``, for each offending call.
        """
        for path, name, attrs, only in self.calls(directory):
            if self.is_daisy_cotton(name) and not only:
                yield path, name, attrs, only
