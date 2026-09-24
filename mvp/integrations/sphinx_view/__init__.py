"""django-sphinx-view integration: Sphinx documentation served inside the app shell.

Usage::

    from mvp.integrations.sphinx_view.views import MVPDocumentationView

    urlpatterns = [
        path(
            "docs<path:path>",
            MVPDocumentationView.as_view(json_build_dir=BASE_DIR / "docs/_build/json"),
            name="docs",
        ),
    ]
"""
