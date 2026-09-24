"""The demo's URLs, so a shell page renders, with ``mvp.pwa.urls`` at the root.

``urlpatterns_without_pwa`` is the same set without the include, for the case
where a project turns the feature on and forgets to mount it. Whatever the demo
itself mounts is filtered out first, so neither case depends on the demo.
"""

from django.urls import include, path

from demo import urls as demo_urls

urlpatterns_without_pwa = [
    pattern
    for pattern in demo_urls.urlpatterns
    if getattr(pattern, "urlconf_name", None) != "mvp.pwa.urls"
]

urlpatterns = [path("", include("mvp.pwa.urls")), *urlpatterns_without_pwa]
