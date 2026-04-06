import logging

from findings.models import Finding
from integrations.ticket_service import close_tickets_for_finding, create_tickets_for_finding

logger = logging.getLogger(__name__)


def close_tickets_async(finding_id):
    """Close Jira/Linear tickets for a resolved finding (django-q2 task)."""
    try:
        finding = Finding.objects.select_related("project", "rule").get(id=finding_id)
    except Finding.DoesNotExist:
        logger.warning("close_tickets_async: finding %s not found", finding_id)
        return

    close_tickets_for_finding(finding)


def create_tickets_async(finding_id):
    """Create Jira/Linear tickets for a single finding (django-q2 task)."""
    try:
        finding = Finding.objects.select_related("project", "rule").get(id=finding_id)
    except Finding.DoesNotExist:
        logger.warning("create_tickets_async: finding %s not found", finding_id)
        return

    create_tickets_for_finding(finding)
