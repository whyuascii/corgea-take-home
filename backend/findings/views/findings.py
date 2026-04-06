import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.constants import MAX_NOTES_LENGTH, VALID_SEVERITIES
from core.pagination import paginate_queryset
from projects.membership import ProjectMembership
from core.audit import log_audit
from ..models import AuditLog, Finding, FindingHistory
from ..serializers import (
    FindingDetailSerializer,
    FindingHistorySerializer,
    FindingSerializer,
)
from projects.permissions import get_project_for_user
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Findings"], operation_id="findings_list", responses=FindingSerializer)
@api_view(["GET"])
def finding_list(request, project_slug):
    """List findings for a project, with optional filters for status, severity, rule, scan, and false positive state."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    findings = (
        Finding.objects.filter(project=project)
        .select_related("rule")
        .defer("code_snippet", "metadata")
    )

    finding_status = request.query_params.get("status")
    if finding_status:
        if finding_status not in Finding.Status.values:
            return Response(
                {"error": f"Invalid status. Must be one of: {', '.join(Finding.Status.values)}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        findings = findings.filter(status=finding_status)
    severity = request.query_params.get("severity")
    if severity:
        severity = severity.upper()
        if severity not in VALID_SEVERITIES:
            return Response(
                {"error": f"Invalid severity. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        findings = findings.filter(rule__severity=severity)
    rule_id = request.query_params.get("rule")
    if rule_id:
        try:
            uuid.UUID(rule_id)
        except (ValueError, AttributeError):
            return Response(
                {"error": "Invalid rule ID. Must be a valid UUID."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
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
        try:
            uuid.UUID(scan_id)
        except (ValueError, AttributeError):
            return Response(
                {"error": "Invalid scan ID. Must be a valid UUID."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        findings = findings.filter(last_seen_scan_id=scan_id)

    return paginate_queryset(findings, request, FindingSerializer)


@extend_schema(tags=["Findings"], responses=FindingDetailSerializer)
@api_view(["GET", "PATCH"])
def finding_detail(request, project_slug, finding_id):
    """Retrieve or update a single finding. PATCH accepts status and ticket URL fields."""
    min_role = ProjectMembership.Role.ADMIN if request.method == "PATCH" else ProjectMembership.Role.VIEWER
    project = get_project_for_user(request, project_slug, min_role=min_role)
    finding = get_object_or_404(
        Finding.objects.select_related("rule").prefetch_related(
            "history", "comments", "comments__user"
        ),
        id=finding_id,
        project=project,
    )

    if request.method == "PATCH":
        # Validate input types before processing
        if "status" in request.data and not isinstance(request.data["status"], str):
            return Response(
                {"error": "status must be a string"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if "notes" in request.data and not isinstance(request.data["notes"], str):
            return Response(
                {"error": "notes must be a string"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Re-fetch with select_for_update to prevent concurrent status conflicts
            finding = Finding.objects.select_for_update().select_related("rule").get(
                id=finding_id, project=project
            )
            old_status = finding.status
            old_severity_override = finding.severity_override
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
                    notes=str(request.data.get("notes", ""))[:MAX_NOTES_LENGTH],
                )
                log_audit(
                    request,
                    AuditLog.Action.FINDING_STATUS_CHANGE,
                    "finding",
                    finding.id,
                    project,
                    {"old_status": old_status, "new_status": finding.status},
                )

            if "severity_override" in request.data and finding.severity_override != old_severity_override:
                log_audit(
                    request,
                    AuditLog.Action.FINDING_SEVERITY_OVERRIDE,
                    "finding",
                    finding.id,
                    project,
                    {
                        "old_severity_override": old_severity_override or None,
                        "new_severity_override": finding.severity_override or None,
                    },
                )
            finding.refresh_from_db()

    serializer = FindingDetailSerializer(finding)
    return Response(serializer.data)


@extend_schema(tags=["Findings"], responses=FindingHistorySerializer)
@api_view(["GET"])
def finding_history(request, project_slug, finding_id):
    """Return the status-change history for a single finding, ordered by most recent first."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    finding = get_object_or_404(Finding, id=finding_id, project=project)
    history = FindingHistory.objects.filter(finding=finding).select_related("changed_by")
    return paginate_queryset(history, request, FindingHistorySerializer, page_size=50)
