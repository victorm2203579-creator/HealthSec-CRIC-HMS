"""
alerts/consumers.py
===================
Django Channels WebSocket consumers for real-time alert notifications.

Broadcasts critical alerts to all connected admin/analyst users.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class AlertNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time alert notifications."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope["user"]
        self.room_group_name = "alerts_broadcast"

        # Only allow authenticated admins/analysts
        if not self.user.is_authenticated:
            await self.close()
            return

        if not await self.user_has_alert_permission():
            await self.close()
            return

        # Add user to broadcast group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        logger.info(f"User {self.user.username} connected to alerts")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"User {self.user.username} disconnected from alerts")

    async def receive(self, text_data):
        """
        Handle incoming WebSocket message.

        Expects JSON:
        {
            "type": "ping" | "acknowledge_alert",
            "alert_id": "uuid" (for acknowledge)
        }
        """
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))

            elif message_type == "acknowledge_alert":
                alert_id = data.get("alert_id")
                await self.acknowledge_alert(alert_id)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {self.user.username}")
        except Exception as e:
            logger.error(f"Error in consumer: {e}")

    async def alert_notification(self, event):
        """
        Handle alert notification event from channel layer.

        Called when group_send is triggered with type='alert_notification'.
        """
        alert_data = event["alert_data"]

        # Send alert to WebSocket
        await self.send(text_data=json.dumps({
            "type": "alert_notification",
            "alert": alert_data,
        }))

    @database_sync_to_async
    def user_has_alert_permission(self):
        """Check if user can receive alert notifications."""
        self.user.refresh_from_db()
        return self.user.is_admin or self.user.is_analyst

    @database_sync_to_async
    def acknowledge_alert(self, alert_id):
        """Mark alert as acknowledged by user."""
        from .models import Alert

        try:
            alert = Alert.objects.get(id=alert_id)
            alert.is_read = True
            alert.save(update_fields=['is_read'])
            logger.info(f"{self.user.username} acknowledged alert {alert_id}")
        except Alert.DoesNotExist:
            logger.warning(f"Alert {alert_id} not found")


class UserActivityConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for user activity monitoring."""

    async def connect(self):
        """Handle user activity connection."""
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # User activity room per user
        self.activity_group = f"user_activity_{self.user.id}"
        await self.channel_layer.group_add(self.activity_group, self.channel_name)
        await self.accept()

        logger.info(f"Activity stream connected for {self.user.username}")

    async def disconnect(self, close_code):
        """Handle disconnection."""
        await self.channel_layer.group_discard(self.activity_group, self.channel_name)

    async def activity_update(self, event):
        """Handle activity update notification."""
        activity_data = event["activity_data"]

        await self.send(text_data=json.dumps({
            "type": "activity_update",
            "activity": activity_data,
        }))


async def broadcast_critical_alert(alert_instance):
    """
    Broadcast a critical alert to all connected admins/analysts.

    Called from alert creation signal.
    """
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()

    # Format alert data
    alert_data = {
        "id": str(alert_instance.id),
        "title": alert_instance.title,
        "description": alert_instance.description,
        "severity": alert_instance.severity,
        "alert_type": alert_instance.alert_type,
        "created_at": alert_instance.created_at.isoformat() if alert_instance.created_at else None,
    }

    # Broadcast to alerts group
    await channel_layer.group_send(
        "alerts_broadcast",
        {
            "type": "alert_notification",
            "alert_data": alert_data,
        }
    )

    logger.info(f"Broadcasting alert {alert_instance.id} to connected clients")
