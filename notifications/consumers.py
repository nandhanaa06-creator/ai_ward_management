import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification
import logging

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if self.user.is_anonymous:
            logger.info("Rejecting anonymous websocket connection to notifications")
            await self.close(code=4401)  # 4401 Unauthorized (custom)
            return

        self.group_name = f'notifications_{self.user.id}'

        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            logger.info("WebSocket connected for user %s", self.user.id)
            unread_count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': unread_count
            }))
        except Exception as exc:
            logger.exception("Error during websocket connect for user %s: %s", self.user.id, exc)
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            try:
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
            except Exception as exc:
                logger.exception("Error during websocket disconnect for user %s: %s", getattr(self, "user", None), exc)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('action') == 'mark_read':
                await self.mark_notification_read(data.get('notification_id'))
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
        except Exception as exc:
            logger.exception("Error handling websocket message for user %s: %s", getattr(self, "user", None), exc)

    async def notification_message(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification': event['notification']
            }))
        except Exception as exc:
            logger.exception("Error sending notification to user %s: %s", getattr(self, "user", None), exc)

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=self.user)
            notification.is_read = True
            notification.save()
        except Notification.DoesNotExist:
            pass
