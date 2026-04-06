import logging
from datetime import timedelta

from django.utils import timezone

from accounts.models import LoginAttempt
from core.constants import LOGIN_ATTEMPT_RETENTION_HOURS

logger = logging.getLogger(__name__)


def cleanup_login_attempts():
    """Periodic task: delete login attempts older than configured retention period."""
    cutoff = timezone.now() - timedelta(hours=LOGIN_ATTEMPT_RETENTION_HOURS)
    deleted, _ = LoginAttempt.objects.filter(created_at__lt=cutoff).delete()
    if deleted:
        logger.info("cleanup_login_attempts: deleted %d old login attempts", deleted)
