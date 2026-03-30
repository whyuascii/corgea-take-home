import hashlib
import hmac
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from findings.models import Finding, FindingHistory

from ..models import IntegrationConfig, StatusMapping

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def jira_webhook(request, webhook_secret):
    """Receive Jira webhook events and sync finding statuses based on configured status mappings."""
    try:
        config = IntegrationConfig.objects.get(
            webhook_secret=webhook_secret,
            provider=IntegrationConfig.Provider.JIRA,
        )
    except IntegrationConfig.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    event = request.data
    issue = event.get("issue", {})
    issue_key = issue.get("key", "")
    status_name = issue.get("fields", {}).get("status", {}).get("name", "")

    if not issue_key or not status_name:
        return Response({"ok": True})

    _sync_status(config, "jira_ticket_id", issue_key, status_name)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([AllowAny])
def linear_webhook(request, webhook_secret):
    """Receive Linear webhook events and sync finding statuses based on configured status mappings."""
    try:
        config = IntegrationConfig.objects.get(
            webhook_secret=webhook_secret,
            provider=IntegrationConfig.Provider.LINEAR,
        )
    except IntegrationConfig.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Verify Linear signature using the webhook secret
    signature = request.headers.get("Linear-Signature", "")
    if signature:
        body = request.body
        expected = hmac.new(
            config.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return Response(status=status.HTTP_403_FORBIDDEN)

    data = request.data
    action = data.get("action", "")
    if action != "update":
        return Response({"ok": True})

    issue_data = data.get("data", {})
    issue_id = issue_data.get("id", "")
    state = issue_data.get("state", {})
    status_name = state.get("name", "") if isinstance(state, dict) else ""

    if not issue_id or not status_name:
        return Response({"ok": True})

    _sync_status(config, "linear_ticket_id", issue_id, status_name)
    return Response({"ok": True})


def _sync_status(config, ticket_field, ticket_value, external_status):
    """Look up status mapping and update the finding if a mapping exists."""
    try:
        mapping = StatusMapping.objects.get(
            integration=config, external_status=external_status
        )
    except StatusMapping.DoesNotExist:
        logger.debug(
            "No status mapping for '%s' on %s integration %s",
            external_status, config.provider, config.id,
        )
        return

    findings = Finding.objects.filter(**{ticket_field: ticket_value})
    for finding in findings:
        if finding.status == mapping.internal_status:
            continue

        old_status = finding.status
        finding.status = mapping.internal_status
        finding.save(update_fields=["status", "updated_at"])
        FindingHistory.objects.create(
            finding=finding,
            old_status=old_status,
            new_status=mapping.internal_status,
            notes=f"Status synced from {config.provider} ({external_status})",
        )
        logger.info(
            "Synced finding %s: %s -> %s (from %s %s=%s)",
            finding.id, old_status, mapping.internal_status,
            config.provider, external_status, ticket_value,
        )
