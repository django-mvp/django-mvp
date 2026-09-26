"""The same fixture app mounted under a different prefix (US-1 scenario 7)."""

from demo.urls import urlpatterns as demo_patterns
from mvp.mounted import mount
from tests.testapp_mounted.mounted import testapp_mounted

urlpatterns = [
    *demo_patterns,
    mount("elsewhere/nested/", testapp_mounted),
]
