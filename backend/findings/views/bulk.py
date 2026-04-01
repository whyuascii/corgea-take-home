import uuid

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from core.audit import log_audit
from core.constants import BULK_OPERATION_LIMIT, VALID_BULK_ACTIONS
from core.throttles import BulkOperationThrottle
from projects.membership import ProjectMembership
from ..models import AuditLog, Finding, FindingHistory
from projects.permissions import get_project_for_user


@extend_schema(tags=["Findings"])
@api_view(["POST"])
@throttle_classes([BulkOperationThrottle])
def bulk_update_findings(request, project_slug):
    """Apply a bulk action (status_change or false_positive) to multiple findings at once."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.ADMIN)
    finding_ids = request.data.get("finding_ids", [])
    action = request.data.get("action")  # "status_change" | "false_positive"

    if not isinstance(finding_ids, list):
        return Response(
            {"error": "finding_ids must be a list"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not finding_ids or not action:
        return Response(
            {"error": "finding_ids (list) and action required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate each finding_id is a valid UUID
    validated_ids = []
    for id_str in finding_ids:
        try:
            validated_ids.append(uuid.UUID(str(id_str)))
        except (ValueError, AttributeError):
            return Response(
                {"error": f"Invalid UUID in finding_ids: {id_str}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    finding_ids = validated_ids

    if len(finding_ids) > BULK_OPERATION_LIMIT:
        return Response(
            {"error": f"Maximum {BULK_OPERATION_LIMIT} findings per bulk operation."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if action not in VALID_BULK_ACTIONS:
        return Response(
            {"error": f"action must be one of: {', '.join(sorted(VALID_BULK_ACTIONS))}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    updated = 0

    with transaction.atomic():
        findings = list(
            Finding.objects.select_for_update().filter(id__in=finding_ids, project=project)
        )
        if len(findings) != len(set(finding_ids)):
            return Response(
                {"error": "One or more finding_ids not found in this project."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if action == "status_change":
            new_status = request.data.get("status")
            if new_status not in [c[0] for c in Finding.Status.choices]:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            to_update = []
            history_records = []
            for f in findings:
                old = f.status
                if old != new_status:
                    f.status = new_status
                    to_update.append(f)
                    history_records.append(
                        FindingHistory(
                            finding=f,
                            old_status=old,
                            new_status=new_status,
                            changed_by=request.user,
                            notes="Bulk status change",
                        )
                    )
            if to_update:
                Finding.objects.bulk_update(to_update, ["status", "updated_at"])
                FindingHistory.objects.bulk_create(history_records)
            updated = len(to_update)

        elif action == "false_positive":
            is_fp = request.data.get("is_false_positive", True)
            if not isinstance(is_fp, bool):
                return Response(
                    {"error": "is_false_positive must be a boolean"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            reason = request.data.get("reason", "")
            if reason is not None and not isinstance(reason, str):
                return Response(
                    {"error": "reason must be a string"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            to_update = []
            history_records = []
            for f in findings:
                if f.is_false_positive != is_fp:
                    f.is_false_positive = is_fp
                    f.false_positive_reason = reason if is_fp else ""
                    to_update.append(f)
                    history_records.append(
                        FindingHistory(
                            finding=f,
                            change_type=FindingHistory.ChangeType.FALSE_POSITIVE,
                            old_status=f.status,
                            new_status=f.status,
                            changed_by=request.user,
                            notes=f"Bulk {'marked' if is_fp else 'unmarked'} as false positive"
                            + (f": {reason}" if reason else ""),
                        )
                    )
            if to_update:
                Finding.objects.bulk_update(
                    to_update, ["is_false_positive", "false_positive_reason", "updated_at"]
                )
                FindingHistory.objects.bulk_create(history_records)
            updated = len(to_update)

    if updated > 0:
        if action == "status_change":
            log_audit(
                request, AuditLog.Action.FINDING_STATUS_CHANGE, "finding", "",
                project, {"bulk": True, "count": updated, "new_status": new_status},
            )
        elif action == "false_positive":
            log_audit(
                request, AuditLog.Action.FINDING_FALSE_POSITIVE, "finding", "",
                project, {"bulk": True, "count": updated, "is_false_positive": is_fp},
            )

    return Response({"updated": updated})
