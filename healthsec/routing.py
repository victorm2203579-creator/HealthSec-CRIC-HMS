"""
healthsec/routing.py
====================
Django Channels WebSocket routing configuration.

Maps WebSocket URLs to consumer classes.
"""

from django.urls import path
from alerts.consumers import AlertNotificationConsumer, UserActivityConsumer

websocket_urlpatterns = [
    path("ws/alerts/", AlertNotificationConsumer.as_asgi()),
    path("ws/activity/", UserActivityConsumer.as_asgi()),
]
