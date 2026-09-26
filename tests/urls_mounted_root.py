"""The fixture app mounted at the site root, without ``main`` (spec edge case).

Placed after the host's own routes, so the host's pages still resolve first.
"""

from demo.urls import urlpatterns as demo_patterns
from mvp.mounted import mount
from tests.testapp_mounted.mounted import testapp_mounted

urlpatterns = [
    *demo_patterns,
    mount("", testapp_mounted),
]
