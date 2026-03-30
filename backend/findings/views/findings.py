from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.pagination import paginate_queryset
from ..audit import log_audit
from ..models import AuditLog, Finding, FindingHistory
from ..serializers import (
    FindingDetailSerializer,
    FindingHistorySerializer,
    FindingSerializer,
)
from .helpers import get_project_for_user


@api_view(["GET"])
def finding_list(request, project_slug):
    """List findings for a project, with optional filters for status, severity, rule, scan, and false positive state."""
    project = get_project_for_user(request, project_slug)
    findings = (
        Finding.objects.filter(project=project)
        .select_related("rule")
        .defer("code_snippet", "metadata")
    )

    finding_status = request.query_params.get("status")
    if finding_status:
        findings = findings.filter(status=finding_status)
    severity = request.query_params.get("severity")
    if severity:
        findings = findings.filter(rule__severity=severity)
    rule_id = request.query_params.get("rule")
    if rule_id:
        findings = findings.filter(rule_id=rule_id)
    is_fp = request.query_params.get("is_false_positive")
    show_all = request.query_params.get("show_all")
    if is_fp is not None:
        findings = findings.filter(is_false_positive=is_fp.lower() == "true")
    elif not show_all:
        # Default: hide false positives unless explicitly requested
        findings = findings.exclude(is_false_positive=True)
    scan_id = request.query_params.get("scan")
    if scan_id:
        findings = findings.filter(last_seen_scan_id=scan_id)

    return paginate_queryset(findings, request, FindingSerializer)


@api_view(["GET", "PATCH"])
def finding_detail(request, project_slug, finding_id):
    """Retrieve or update a single finding. PATCH accepts status and ticket URL fields."""
    project = get_project_for_user(request, project_slug)
    finding = get_object_or_404(
        Finding.objects.select_related("rule").prefetch_related(
            "history", "comments", "comments__user"
        ),
        id=finding_id,
        project=project,
    )

    if request.method == "PATCH":
        old_status = finding.status
        serializer = FindingSerializer(finding, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if "status" in request.data and request.data["status"] != old_status:
            FindingHistory.objects.create(
                finding=finding,
                old_status=old_status,
                new_status=finding.status,
                changed_by=request.user,
                jira_ticket_url=finding.jira_ticket_url,
                linear_ticket_url=finding.linear_ticket_url,
                pr_url=finding.pr_url,
                notes=request.data.get("notes", ""),
            )
            log_audit(
                request,
                AuditLog.Action.FINDING_STATUS_CHANGE,
                "finding",
                finding.id,
                project,
                {"old_status": old_status, "new_status": finding.status},
            )
        finding.refresh_from_db()

    serializer = FindingDetailSerializer(finding)
    return Response(serializer.data)


@api_view(["GET"])
def finding_history(request, project_slug, finding_id):
    """Return the status-change history for a single finding, ordered by most recent first."""
    project = get_project_for_user(request, project_slug)
    finding = get_object_or_404(Finding, id=finding_id, project=project)
    history = FindingHistory.objects.filter(finding=finding).select_related("changed_by")
    return paginate_queryset(history, request, FindingHistorySerializer, page_size=50)
