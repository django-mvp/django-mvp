"""The demo's URLs, so a shell page renders, with ``mvp.urls`` mounted at ``account/``.

``urlpatterns_without_mvp_urls`` is the same set without that include, for the
case where a project turns the feature on and forgets to mount it.
"""

from demo import urls as demo_urls

urlpatterns = demo_urls.urlpatterns

urlpatterns_without_mvp_urls = [
    pattern
    for pattern in demo_urls.urlpatterns
    if getattr(getattr(pattern, "urlconf_name", None), "__name__", None) != "mvp.urls"
]
