"""
healthsec/asgi.py
=================
ASGI (Asynchronous Server Gateway Interface) config for the HealthSec project.

Configured for WebSocket support via Django Channels with Daphne server:
    daphne -b 0.0.0.0 -p 8000 healthsec.asgi:application
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthsec.settings')

django_asgi_app = get_asgi_application()

# Import routing after Django setup
from healthsec.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
