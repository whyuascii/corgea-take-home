import logging

import requests
from django.db import transaction
from findings.models import Finding
from findings.models.history import FindingHistory

from .models import IntegrationConfig

logger = logging.getLogger(__name__)


def close_tickets_for_finding(finding):
    """Close tickets in all enabled integrations for a resolved finding.

    Called after scan ingestion when findings disappear (are resolved).
    Failures are logged but never raised — ticket closure must not block scans.
    """
    configs = IntegrationConfig.objects.filter(
        project=finding.project, is_enabled=True
    )

    for config in configs:
        try:
            if config.provider == IntegrationConfig.Provider.JIRA:
                _close_jira_ticket(config, finding)
            elif config.provider == IntegrationConfig.Provider.LINEAR:
                _close_linear_ticket(config, finding)
        except (requests.RequestException, ConnectionError, ValueError, KeyError, OSError, Exception):
            logger.exception(
                "Failed to close %s ticket for finding %s",
                config.provider, finding.id,
            )


def _close_jira_ticket(config, finding):
    if not finding.jira_ticket_id:
        return

    from .jira_client import transition_jira_issue_to_done

    transitioned = transition_jira_issue_to_done(config, finding.jira_ticket_id)
    if transitioned:
        FindingHistory.objects.create(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
            old_status=finding.status,
            new_status=finding.status,
            jira_ticket_url=finding.jira_ticket_url,
            notes=f"Closed Jira ticket: {finding.jira_ticket_id}",
        )


def _close_linear_ticket(config, finding):
    if not finding.linear_ticket_id:
        return

    from .linear_client import transition_linear_issue_to_done

    transitioned = transition_linear_issue_to_done(config, finding.linear_ticket_id)
    if transitioned:
        FindingHistory.objects.create(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
            old_status=finding.status,
            new_status=finding.status,
            linear_ticket_url=finding.linear_ticket_url,
            notes=f"Closed Linear ticket: {finding.linear_ticket_id}",
        )


def create_tickets_for_finding(finding):
    """Create tickets in all enabled integrations for a finding's project.

    Called after scan ingestion for new/reopened findings.
    Failures are logged but never raised — ticket creation must not block scans.
    """
    configs = IntegrationConfig.objects.filter(
        project=finding.project, is_enabled=True
    )

    for config in configs:
        try:
            if config.provider == IntegrationConfig.Provider.JIRA:
                _create_jira_ticket(config, finding)
            elif config.provider == IntegrationConfig.Provider.LINEAR:
                _create_linear_ticket(config, finding)
        except (requests.RequestException, ConnectionError, ValueError, KeyError, OSError):
            logger.exception(
                "Failed to create %s ticket for finding %s",
                config.provider, finding.id,
            )


def _create_jira_ticket(config, finding):
    from .jira_client import create_jira_issue, get_jira_issue_status

    with transaction.atomic():
        # Re-fetch with row lock to prevent duplicate ticket creation
        finding = Finding.objects.select_for_update().get(pk=finding.pk)

        # If a Jira ticket already exists, only skip if it is NOT done.
        if finding.jira_ticket_id:
            status = get_jira_issue_status(config, finding.jira_ticket_id)
            if status != "done":
                logger.debug(
                    "Skipping Jira ticket creation for finding %s — "
                    "existing ticket %s has status %r",
                    finding.id, finding.jira_ticket_id, status,
                )
                return

        issue_key, issue_url = create_jira_issue(config, finding)
        finding.jira_ticket_id = issue_key
        finding.jira_ticket_url = issue_url
        finding.save(update_fields=["jira_ticket_id", "jira_ticket_url", "updated_at"])
        logger.info("Created Jira ticket %s for finding %s", issue_key, finding.id)

    FindingHistory.objects.create(
        finding=finding,
        change_type=FindingHistory.ChangeType.TICKET_CREATED,
        old_status=finding.status,
        new_status=finding.status,
        jira_ticket_url=issue_url,
        notes=f"Created Jira ticket: {issue_key}",
    )


def _create_linear_ticket(config, finding):
    from .linear_client import create_linear_issue, get_linear_issue_status

    with transaction.atomic():
        # Re-fetch with row lock to prevent duplicate ticket creation
        finding = Finding.objects.select_for_update().get(pk=finding.pk)

        # If a Linear ticket already exists, only skip if it is NOT completed/cancelled.
        if finding.linear_ticket_id:
            status = get_linear_issue_status(config, finding.linear_ticket_id)
            if status not in ("completed", "cancelled"):
                logger.debug(
                    "Skipping Linear ticket creation for finding %s — "
                    "existing ticket %s has status %r",
                    finding.id, finding.linear_ticket_id, status,
                )
                return

        issue_id, issue_url = create_linear_issue(config, finding)
        finding.linear_ticket_id = issue_id
        finding.linear_ticket_url = issue_url
        finding.save(update_fields=["linear_ticket_id", "linear_ticket_url", "updated_at"])
        logger.info("Created Linear ticket %s for finding %s", issue_id, finding.id)

    FindingHistory.objects.create(
        finding=finding,
        change_type=FindingHistory.ChangeType.TICKET_CREATED,
        old_status=finding.status,
        new_status=finding.status,
        linear_ticket_url=issue_url,
        notes=f"Created Linear ticket: {issue_id}",
    )
