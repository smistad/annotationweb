from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .consumers import ExportProgressConsumer


websocket_urlpatterns = [
    re_path(r'^ws/export_progress/$', ExportProgressConsumer)
]

application = ProtocolTypeRouter({
    "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns)))
})
