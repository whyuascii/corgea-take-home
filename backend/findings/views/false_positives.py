from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from core.constants import MAX_REASON_LENGTH
from projects.membership import ProjectMembership
from core.audit import log_audit
from ..models import AuditLog, Finding, FindingHistory
from projects.permissions import get_project_for_user


@extend_schema(tags=["Findings"])
@api_view(["POST"])
def mark_false_positive(request, project_slug, finding_id):
    """Mark or unmark a finding as a false positive, optionally applying across all projects for the same rule."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.MEMBER)
    finding = get_object_or_404(Finding, id=finding_id, project=project)

    is_fp = request.data.get("is_false_positive", True)

    reason = request.data.get("reason", "")
    if not isinstance(reason, str):
        return Response(
            {"error": "reason must be a string"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    reason = reason.strip()[:MAX_REASON_LENGTH]

    apply_all = request.data.get("apply_to_all_projects", False)
    if isinstance(apply_all, str):
        apply_all = apply_all.lower() in ("true", "1", "yes")
    elif not isinstance(apply_all, bool):
        apply_all = False
    apply_to_all = apply_all

    with transaction.atomic():
        # Lock the primary finding row first.
        finding = Finding.objects.select_for_update().get(pk=finding.pk)
        affected_findings = [finding]

        if apply_to_all and is_fp:
            # Get all projects the user has at least MEMBER access to.
            user_project_ids = ProjectMembership.objects.filter(
                user=request.user,
                role__in=[
                    ProjectMembership.Role.MEMBER,
                    ProjectMembership.Role.ADMIN,
                    ProjectMembership.Role.OWNER,
                ],
            ).values_list("project_id", flat=True)

            # select_for_update prevents concurrent FP marking from racing
            # on the same finding rows across projects.
            cross_project_findings = (
                Finding.objects.select_for_update()
                .filter(
                    rule__semgrep_rule_id=finding.rule.semgrep_rule_id,
                    project_id__in=user_project_ids,
                    is_false_positive=False,
                )
                .exclude(id=finding.id)
                .select_related("rule")
            )
            affected_findings.extend(list(cross_project_findings))

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
