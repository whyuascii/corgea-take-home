import logging
from smtplib import SMTPException

from django.utils import timezone

logger = logging.getLogger(__name__)


def check_sla_breaches():
    """Periodic task: mark findings that have exceeded their SLA deadline."""
    from django.core.cache import cache
    from django.db import transaction

    from core.constants import SLA_BATCH_SIZE
    from findings.models import Finding

    # Distributed lock to prevent overlapping executions across workers
    if not cache.add("sla_breach_check_lock", "1", timeout=300):
        logger.debug("check_sla_breaches: skipping — another worker holds the lock")
        return

    now = timezone.now()
    all_breached_ids = []

    try:
        while True:
            batch_ids = list(
                Finding.objects.filter(
                    sla_deadline__lte=now,
                    sla_breached=False,
                )
                .exclude(status__in=[Finding.Status.RESOLVED, Finding.Status.IGNORED])
                .values_list("id", flat=True)[:SLA_BATCH_SIZE]
            )
            if not batch_ids:
                break
            with transaction.atomic():
                Finding.objects.filter(id__in=batch_ids).update(sla_breached=True)
            all_breached_ids.extend(batch_ids)

        if all_breached_ids:
            logger.info("check_sla_breaches: marked %d findings as breached", len(all_breached_ids))

        # Send breach notifications per project
        if all_breached_ids:
            breached_findings = (
                Finding.objects.filter(id__in=all_breached_ids)
                .select_related("project", "project__owner", "rule")
            )
            projects = {}
            for finding in breached_findings:
                projects.setdefault(finding.project_id, []).append(finding)

            from core.emails import send_sla_breach_email

            for project_id, findings in projects.items():
                project = findings[0].project
                try:
                    send_sla_breach_email(project, findings)
                except (SMTPException, ConnectionError, OSError):
                    logger.exception("Failed to send SLA breach email for project %s", project_id)
    finally:
        cache.delete("sla_breach_check_lock")
