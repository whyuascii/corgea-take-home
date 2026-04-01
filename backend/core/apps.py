import logging

from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        try:
            from core.schedules import register_schedules

            register_schedules()
        except (OperationalError, ProgrammingError):
            logger.debug("Skipping schedule registration — DB tables not ready")
        except Exception:
            logger.exception("Failed to register periodic schedules")
