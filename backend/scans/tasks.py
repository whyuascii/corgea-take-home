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
    from django.core.management import call_command

    call_command("cleanup_old_scans")
