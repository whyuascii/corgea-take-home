from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.audit import log_audit
from core.pagination import paginate_queryset
from projects.membership import ProjectMembership
from scans.models import Scan
from ..models import AuditLog, Finding, FindingHistory, Rule
from ..serializers import RuleSerializer
from projects.permissions import get_project_for_user


@api_view(["GET"])
def rule_list(request, project_slug):
    """List all rules for a project, with optional filtering by status (active/ignored)."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    rules = Rule.objects.filter(project=project)
    rule_status = request.query_params.get("status")
    if rule_status:
        if rule_status not in [Rule.Status.ACTIVE, Rule.Status.IGNORED]:
            return Response(
                {"error": "Invalid status. Must be 'active' or 'ignored'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rules = rules.filter(status=rule_status)
    return paginate_queryset(rules, request, RuleSerializer)


@api_view(["PATCH"])
def rule_update(request, project_slug, rule_id):
    """Update a rule's status (active or ignored). Ignoring a rule also ignores all its findings."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.ADMIN)

    new_status = request.data.get("status")
    if new_status not in [Rule.Status.ACTIVE, Rule.Status.IGNORED]:
        return Response(
            {"error": "Status must be 'active' or 'ignored'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    affected_count = 0

    with transaction.atomic():
        # select_for_update prevents concurrent rule status changes
        try:
            rule = Rule.objects.select_for_update().get(id=rule_id, project=project)
        except Rule.DoesNotExist:
            return Response(
                {"error": "Rule not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        old_status = rule.status
        rule.status = new_status
        rule.save(update_fields=["status", "updated_at"])

        if new_status == Rule.Status.IGNORED:
            findings = list(
                Finding.objects.filter(rule=rule)
                .exclude(status=Finding.Status.IGNORED)
                .only("id", "status", "updated_at")
            )
            history_records = []
            for finding in findings:
                old = finding.status
                finding.status = Finding.Status.IGNORED
                history_records.append(
                    FindingHistory(
                        finding=finding,
                        old_status=old,
                        new_status=Finding.Status.IGNORED,
                        changed_by=request.user,
                        notes=f"Rule {rule.semgrep_rule_id} marked as ignored",
                    )
                )
            Finding.objects.bulk_update(findings, ["status", "updated_at"])
            FindingHistory.objects.bulk_create(history_records)
            affected_count = len(findings)

        elif new_status == Rule.Status.ACTIVE and old_status == Rule.Status.IGNORED:
            latest_scan = Scan.objects.filter(project=project).first()
            findings = list(
                Finding.objects.filter(rule=rule, status=Finding.Status.IGNORED)
                .only("id", "status", "last_seen_scan_id", "updated_at")
            )
            history_records = []
            for finding in findings:
                if latest_scan and finding.last_seen_scan_id == latest_scan.id:
                    finding.status = Finding.Status.OPEN
                else:
                    finding.status = Finding.Status.RESOLVED
                history_records.append(
                    FindingHistory(
                        finding=finding,
                        old_status=Finding.Status.IGNORED,
                        new_status=finding.status,
                        changed_by=request.user,
                        notes=f"Rule {rule.semgrep_rule_id} reactivated",
                    )
                )
            Finding.objects.bulk_update(findings, ["status", "updated_at"])
            FindingHistory.objects.bulk_create(history_records)
            affected_count = len(findings)

    log_audit(
        request, AuditLog.Action.RULE_STATUS_CHANGE, "rule", rule.id, project,
        {"old_status": old_status, "new_status": new_status, "affected_findings": affected_count},
    )

    return Response(RuleSerializer(rule).data)
