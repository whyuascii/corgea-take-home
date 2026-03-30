from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Finding, FindingHistory
from .helpers import get_project_for_user


@api_view(["POST"])
def bulk_update_findings(request, project_slug):
    """Apply a bulk action (status_change or false_positive) to multiple findings at once."""
    project = get_project_for_user(request, project_slug)
    finding_ids = request.data.get("finding_ids", [])
    action = request.data.get("action")  # "status_change", "false_positive", "ignore"

    if not finding_ids or not action:
        return Response(
            {"error": "finding_ids and action required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    findings = list(Finding.objects.filter(id__in=finding_ids, project=project))
    updated = 0

    with transaction.atomic():
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
            reason = request.data.get("reason", "")

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

    return Response({"updated": updated})
