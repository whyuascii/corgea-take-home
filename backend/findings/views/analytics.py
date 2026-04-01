import defusedcsv
from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from core.constants import DB_ITERATOR_CHUNK_SIZE, DEFAULT_TREND_DAYS, MAX_EXPORT_ROWS, MAX_TREND_DAYS, SEARCH_QUERY_MAX_LEN, SEARCH_QUERY_MIN_LEN
from core.pagination import paginate_queryset
from core.throttles import ExportThrottle
from projects.membership import ProjectMembership
from ..models import Finding, FindingHistory
from ..serializers import FindingSerializer
from projects.permissions import get_project_for_user


@api_view(["GET"])
def finding_trends(request, project_slug):
    """Return daily new and resolved finding counts over a configurable time window (default 30 days)."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    try:
        days = int(request.query_params.get("days", DEFAULT_TREND_DAYS))
    except (ValueError, TypeError):
        return Response(
            {"error": "days must be an integer"}, status=status.HTTP_400_BAD_REQUEST
        )
    days = max(1, min(days, MAX_TREND_DAYS))  # Clamp to [1, MAX_TREND_DAYS]
    start_date = timezone.now() - timedelta(days=days)

    # Daily new findings (by created_at)
    new_by_day = (
        Finding.objects.filter(project=project, created_at__gte=start_date)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Daily resolved findings (by history entries)
    resolved_by_day = (
        FindingHistory.objects.filter(
            finding__project=project,
            new_status="resolved",
            created_at__gte=start_date,
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Build a complete date range
    date_map_new = {str(r["date"]): r["count"] for r in new_by_day}
    date_map_resolved = {str(r["date"]): r["count"] for r in resolved_by_day}

    result = []
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        date_str = str(date)
        result.append(
            {
                "date": date_str,
                "new": date_map_new.get(date_str, 0),
                "resolved": date_map_resolved.get(date_str, 0),
            }
        )

    return Response(result)


@api_view(["GET"])
@throttle_classes([ExportThrottle])
def finding_export(request, project_slug):
    """Export findings as a CSV file, with optional status and severity filters."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    findings = Finding.objects.filter(project=project).select_related("rule")

    # Apply same filters as finding_list
    finding_status = request.query_params.get("status")
    if finding_status:
        findings = findings.filter(status=finding_status)
    severity = request.query_params.get("severity")
    if severity:
        findings = findings.filter(rule__severity=severity)

    # Cap to MAX_EXPORT_ROWS to avoid memory exhaustion on very large projects.
    findings = findings[:MAX_EXPORT_ROWS]

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="findings-{project.slug}.csv"'

    writer = defusedcsv.writer(response)
    writer.writerow(
        [
            "Rule ID",
            "Severity",
            "File",
            "Line Start",
            "Line End",
            "Status",
            "False Positive",
            "FP Reason",
            "First Seen",
            "Last Updated",
        ]
    )

    for f in findings.iterator(chunk_size=DB_ITERATOR_CHUNK_SIZE):
        writer.writerow(
            [
                f.rule.semgrep_rule_id,
                f.rule.severity,
                f.file_path,
                f.line_start,
                f.line_end,
                f.status,
                f.is_false_positive,
                f.false_positive_reason,
                f.created_at.isoformat(),
                f.updated_at.isoformat(),
            ]
        )

    return response


@api_view(["GET"])
def finding_search(request, project_slug):
    """Search findings by file path, rule ID, or code snippet. Requires a query of at least 2 characters."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    q = request.query_params.get("q", "").strip()
    if not q or len(q) < SEARCH_QUERY_MIN_LEN:
        return Response({"count": 0, "next": None, "previous": None, "results": []})
    if len(q) > SEARCH_QUERY_MAX_LEN:
        return Response(
            {"error": f"Search query too long (max {SEARCH_QUERY_MAX_LEN} characters)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    findings = (
        Finding.objects.filter(project=project)
        .filter(
            Q(file_path__icontains=q)
            | Q(rule__semgrep_rule_id__icontains=q)
            | Q(code_snippet__icontains=q)
        )
        .select_related("rule")
    )

    return paginate_queryset(findings, request, FindingSerializer)
