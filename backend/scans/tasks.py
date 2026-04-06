import logging
from datetime import timedelta

from django.utils import timezone

from core.constants import DATA_RETENTION_DAYS
from core.emails import send_scan_complete_email
from scans.ingestion import ingest_scan
from scans.models import Scan

logger = logging.getLogger(__name__)


def ingest_scan_async(scan_id):
    """Background task: parse and ingest a scan report (django-q2 one-off task)."""
    try:
        scan = Scan.objects.select_related("project").get(id=scan_id)
    except Scan.DoesNotExist:
        logger.warning("ingest_scan_async: scan %s not found", scan_id)
        return

    # Idempotency guard: skip if this scan was already ingested (e.g., task
    # was enqueued and also ran synchronously due to a transient error, or
    # the broker retried delivery).  Check new_count + resolved_count too,
    # because a valid scan can have total_findings_count == 0 if all results
    # were skipped or the report was empty.
    if scan.total_findings_count > 0 or scan.new_count > 0 or scan.resolved_count > 0:
        logger.info("ingest_scan_async: scan %s already ingested, skipping", scan_id)
        return

    ingest_scan(scan)


def send_scan_notifications(scan_id):
    """Send scan-complete email notification to the project owner (django-q2 task)."""
    try:
        scan = Scan.objects.select_related("project", "project__owner").get(id=scan_id)
    except Scan.DoesNotExist:
        logger.warning("send_scan_notifications: scan %s not found", scan_id)
        return

    send_scan_complete_email(scan)


def cleanup_old_scans():
    """Periodic task: nullify raw_report on old scans per retention policy."""
    cutoff = timezone.now() - timedelta(days=DATA_RETENTION_DAYS)
    updated = (
        Scan.objects
        .filter(created_at__lt=cutoff, archived_at__isnull=True)
        .exclude(raw_report={})
        .update(raw_report={}, archived_at=timezone.now())
    )
    if updated:
        logger.info("Cleaned up %d old scan(s) past %d-day retention", updated, DATA_RETENTION_DAYS)
