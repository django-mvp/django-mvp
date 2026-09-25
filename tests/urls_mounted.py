"""A host URLconf that mounts the fixture app at ``mounted/``."""

from demo.urls import urlpatterns as demo_patterns
from mvp.mounted import mount
from tests.testapp_mounted.mounted import testapp_mounted

urlpatterns = [
    *demo_patterns,
    mount("mounted/", testapp_mounted),
]
