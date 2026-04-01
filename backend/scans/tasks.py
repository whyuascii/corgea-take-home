import logging

logger = logging.getLogger(__name__)


def ingest_scan_async(scan_id):
    """Background task: parse and ingest a scan report (django-q2 one-off task)."""
    from scans.ingestion import ingest_scan
    from scans.models import Scan

    try:
        scan = Scan.objects.select_related("project").get(id=scan_id)
    except Scan.DoesNotExist:
        logger.warning("ingest_scan_async: scan %s not found", scan_id)
        return

    ingest_scan(scan)


def send_scan_notifications(scan_id):
    """Send scan-complete email notification to the project owner (django-q2 task)."""
    from scans.models import Scan

    try:
        scan = Scan.objects.select_related("project", "project__owner").get(id=scan_id)
    except Scan.DoesNotExist:
        logger.warning("send_scan_notifications: scan %s not found", scan_id)
        return

    from core.emails import send_scan_complete_email

    send_scan_complete_email(scan)


def cleanup_old_scans():
    """Periodic task: nullify raw_report on old scans per retention policy."""
    from datetime import timedelta

    from django.utils import timezone

    from core.constants import DATA_RETENTION_DAYS
    from scans.models import Scan

    cutoff = timezone.now() - timedelta(days=DATA_RETENTION_DAYS)
    updated = (
        Scan.objects
        .filter(created_at__lt=cutoff, archived_at__isnull=True)
        .exclude(raw_report={})
        .update(raw_report={}, archived_at=timezone.now())
    )
    if updated:
        logger.info("Cleaned up %d old scan(s) past %d-day retention", updated, DATA_RETENTION_DAYS)
