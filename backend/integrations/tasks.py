import logging

logger = logging.getLogger(__name__)


def close_tickets_async(finding_id):
    """Close Jira/Linear tickets for a resolved finding (django-q2 task)."""
    from findings.models import Finding

    try:
        finding = Finding.objects.select_related("project", "rule").get(id=finding_id)
    except Finding.DoesNotExist:
        logger.warning("close_tickets_async: finding %s not found", finding_id)
        return

    from integrations.ticket_service import close_tickets_for_finding

    close_tickets_for_finding(finding)


def create_tickets_async(finding_id):
    """Create Jira/Linear tickets for a single finding (django-q2 task)."""
    from findings.models import Finding

    try:
        finding = Finding.objects.select_related("project", "rule").get(id=finding_id)
    except Finding.DoesNotExist:
        logger.warning("create_tickets_async: finding %s not found", finding_id)
        return

    from integrations.ticket_service import create_tickets_for_finding

    create_tickets_for_finding(finding)
