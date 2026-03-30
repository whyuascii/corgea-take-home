from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..audit import log_audit
from ..models import AuditLog, Finding, FindingHistory
from .helpers import get_project_for_user


@api_view(["POST"])
def mark_false_positive(request, project_slug, finding_id):
    """Mark or unmark a finding as a false positive, optionally applying across all projects for the same rule."""
    project = get_project_for_user(request, project_slug)
    finding = get_object_or_404(Finding, id=finding_id, project=project)

    is_fp = request.data.get("is_false_positive", True)
    reason = request.data.get("reason", "")
    apply_to_all = request.data.get("apply_to_all_projects", False)

    affected_findings = [finding]

    if apply_to_all and is_fp:
        cross_project_findings = (
            Finding.objects.filter(
                rule__semgrep_rule_id=finding.rule.semgrep_rule_id,
                project__owner=request.user,
                is_false_positive=False,
            )
            .exclude(id=finding.id)
            .select_related("rule")
        )
        affected_findings.extend(list(cross_project_findings))

    with transaction.atomic():
        history_records = []
        for f in affected_findings:
            old_fp = f.is_false_positive
            f.is_false_positive = is_fp
            f.false_positive_reason = reason if is_fp else ""
            f.save(update_fields=["is_false_positive", "false_positive_reason", "updated_at"])

            if old_fp != is_fp:
                history_records.append(
                    FindingHistory(
                        finding=f,
                        change_type=FindingHistory.ChangeType.FALSE_POSITIVE,
                        old_status=f.status,
                        new_status=f.status,
                        changed_by=request.user,
                        notes=f"Marked as {'false positive' if is_fp else 'not false positive'}"
                        + (f": {reason}" if reason else ""),
                    )
                )
        if history_records:
            FindingHistory.objects.bulk_create(history_records)

    affected_ids = [str(f.id) for f in affected_findings]
    log_audit(
        request,
        AuditLog.Action.FINDING_FALSE_POSITIVE,
        "finding",
        finding.id,
        project,
        {"affected_count": len(affected_ids), "is_false_positive": is_fp},
    )
    return Response(
        {
            "affected_count": len(affected_ids),
            "affected_findings": affected_ids,
        }
    )
