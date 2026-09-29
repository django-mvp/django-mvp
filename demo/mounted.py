"""The Sphinx user guide, mounted at ``docs/`` in ``demo/urls.py``."""

from pathlib import Path

from mvp.integrations.sphinx_view.mounted import DocumentationApp

#: Build it with ``sphinx-build -b json demo/sphinx_docs demo/sphinx_docs/_build/json``.
docs = DocumentationApp(
    json_build_dir=Path(__file__).parent / "sphinx_docs" / "_build" / "json",
    icon="support",
)
