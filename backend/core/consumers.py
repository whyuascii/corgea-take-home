import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from projects.membership import ProjectMembership


class ScanProgressConsumer(AsyncWebsocketConsumer):
    """Broadcasts scan progress updates to all clients watching a project."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        self.project_slug = self.scope["url_route"]["kwargs"]["project_slug"]

        has_access = await database_sync_to_async(
            ProjectMembership.objects.filter(
                user=user, project__slug=self.project_slug
            ).exists
        )()

        if not has_access:
            await self.close()
            return

        self.group_name = f"project_{self.project_slug}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def scan_progress(self, event):
        """Handle scan.progress type messages."""
        await self.send(text_data=json.dumps(event["data"]))

    async def scan_complete(self, event):
        """Handle scan.complete type messages."""
        await self.send(text_data=json.dumps(event["data"]))


class DashboardConsumer(AsyncWebsocketConsumer):
    """Broadcasts cross-project notifications to authenticated user groups."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        self.group_name = f"user_{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dashboard_update(self, event):
        """Handle dashboard.update type messages."""
        await self.send(text_data=json.dumps(event["data"]))
