"""
ASGI config for Nigerian University MIS.
Supports both HTTP and WebSocket via Channels.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# WebSocket routing
from config import wschannels

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(wschannels.websocket_urlpatterns)
        )
    ),
})