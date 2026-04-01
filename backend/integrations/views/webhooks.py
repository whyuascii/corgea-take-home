import hashlib
import hmac
import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.throttles import WebhookThrottle
from drf_spectacular.utils import extend_schema

from findings.models import Finding, FindingHistory

from ..models import IntegrationConfig, StatusMapping

logger = logging.getLogger(__name__)


def _verify_hmac(secret, body, provided_signature):
    """Constant-time HMAC-SHA256 verification."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided_signature)


@extend_schema(tags=["Integrations"])
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([WebhookThrottle])
def jira_webhook(request, webhook_secret):
    """Receive Jira webhook events and sync finding statuses based on configured status mappings."""
    try:
        config = IntegrationConfig.objects.get(
            webhook_secret=webhook_secret,
            provider=IntegrationConfig.Provider.JIRA,
        )
    except IntegrationConfig.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Verify HMAC signature — reject unsigned or forged payloads.
    signature = request.headers.get("X-Hub-Signature", "")
    if not signature or not _verify_hmac(config.webhook_secret, request.body, signature):
        return Response(status=status.HTTP_403_FORBIDDEN)

    event = request.data
    issue = event.get("issue", {})
    issue_key = issue.get("key", "")
    status_name = issue.get("fields", {}).get("status", {}).get("name", "")

    if not isinstance(issue_key, str) or len(issue_key) > 200:
        return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(status_name, str) or len(status_name) > 200:
        return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

    if not issue_key or not status_name:
        return Response({"ok": True})

    _sync_status(config, "jira_ticket_id", issue_key, status_name)
    return Response({"ok": True})


@extend_schema(tags=["Integrations"])
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([WebhookThrottle])
def linear_webhook(request, webhook_secret):
    """Receive Linear webhook events and sync finding statuses based on configured status mappings."""
    try:
        config = IntegrationConfig.objects.get(
            webhook_secret=webhook_secret,
            provider=IntegrationConfig.Provider.LINEAR,
        )
    except IntegrationConfig.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Verify Linear signature — reject unsigned or forged payloads.
    signature = request.headers.get("Linear-Signature", "")
    if not signature or not _verify_hmac(config.webhook_secret, request.body, signature):
        return Response(status=status.HTTP_403_FORBIDDEN)

    data = request.data
    action = data.get("action", "")
    if action != "update":
        return Response({"ok": True})

    issue_data = data.get("data", {})
    issue_id = issue_data.get("id", "")
    state = issue_data.get("state", {})
    status_name = state.get("name", "") if isinstance(state, dict) else ""

    if not isinstance(issue_id, str) or len(issue_id) > 200:
        return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(status_name, str) or len(status_name) > 200:
        return Response({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)

    if not issue_id or not status_name:
        return Response({"ok": True})

    _sync_status(config, "linear_ticket_id", issue_id, status_name)
    return Response({"ok": True})


def _sync_status(config, ticket_field, ticket_value, external_status):
    """Look up status mapping and update the finding if a mapping exists.

    Uses select_for_update to prevent two concurrent webhook deliveries
    from racing on the same finding row.
    """
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

    with transaction.atomic():
        findings = (
            Finding.objects.select_for_update()
            .filter(**{ticket_field: ticket_value})
        )
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
