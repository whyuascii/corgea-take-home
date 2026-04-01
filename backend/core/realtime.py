import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def broadcast_scan_progress(project_slug, data):
    """Send scan progress update to all clients watching a project."""

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"project_{project_slug}",
            {"type": "scan.progress", "data": data},
        )
    except (OSError, ConnectionError, RuntimeError, AttributeError):
        logger.debug("Could not broadcast scan progress for %s", project_slug)


def broadcast_scan_complete(project_slug, scan_id, summary):
    """Send scan completion notification to all clients watching a project."""
    
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"project_{project_slug}",
            {
                "type": "scan.complete",
                "data": {
                    "event": "scan_complete",
                    "scan_id": str(scan_id),
                    "summary": summary,
                },
            },
        )
    except (OSError, ConnectionError, RuntimeError, AttributeError):
        logger.debug("Could not broadcast scan complete for %s", project_slug)


def broadcast_dashboard_update(user_id, data):
    """Send a dashboard notification to a specific user."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {"type": "dashboard.update", "data": data},
        )
    except (OSError, ConnectionError, RuntimeError, AttributeError):
        logger.debug("Could not broadcast dashboard update for user %s", user_id)
