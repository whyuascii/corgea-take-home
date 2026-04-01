from django.db.models import Count, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.cache import cached_view
from core.constants import CACHE_TTL_PROJECT, RECENT_SCANS_LIMIT, TOP_RULES_LIMIT
from projects.membership import ProjectMembership
from scans.models import Scan
from ..models import Finding, Rule
from projects.permissions import get_project_for_user


@api_view(["GET"])
@cached_view("project_summary", timeout=CACHE_TTL_PROJECT)
def project_summary(request, project_slug):
    """Return aggregate project statistics"""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)

    # Consolidate status counts into a single query using conditional aggregation
    findings_qs = Finding.objects.filter(project=project)
    agg = findings_qs.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status="new")),
        open=Count("id", filter=Q(status="open")),
        reopened=Count("id", filter=Q(status="reopened")),
        resolved=Count("id", filter=Q(status="resolved")),
        ignored=Count("id", filter=Q(status="ignored")),
        false_positive=Count("id", filter=Q(is_false_positive=True)),
        sev_error=Count("id", filter=Q(rule__severity="ERROR") & ~Q(status="resolved")),
        sev_warning=Count("id", filter=Q(rule__severity="WARNING") & ~Q(status="resolved")),
        sev_info=Count("id", filter=Q(rule__severity="INFO") & ~Q(status="resolved")),
    )

    status_counts = {
        "new": agg["new"],
        "open": agg["open"],
        "reopened": agg["reopened"],
        "resolved": agg["resolved"],
        "ignored": agg["ignored"],
        "false_positive": agg["false_positive"],
    }

    top_rules = (
        Rule.objects.filter(project=project, status=Rule.Status.ACTIVE)
        .annotate(
            active_findings=Count(
                "findings",
                filter=Q(findings__status__in=["new", "open", "reopened"]),
            )
        )
        .filter(active_findings__gt=0)
        .order_by("-active_findings")[:TOP_RULES_LIMIT]
    )

    recent_scans = Scan.objects.filter(project=project).only(
        "id", "scanned_at", "new_count", "resolved_count",
        "reopened_count", "total_findings_count",
    )[:RECENT_SCANS_LIMIT]

    return Response(
        {
            "status_counts": status_counts,
            "severity_counts": {
                "error": agg["sev_error"],
                "warning": agg["sev_warning"],
                "info": agg["sev_info"],
            },
            "total_findings": agg["total"],
            "total_active": agg["new"] + agg["open"] + agg["reopened"],
            "top_rules": [
                {
                    "id": str(r.id),
                    "rule_id": r.semgrep_rule_id,
                    "severity": r.severity,
                    "active_findings": r.active_findings,
                }
                for r in top_rules
            ],
            "recent_scans": [
                {
                    "id": str(s.id),
                    "scanned_at": s.scanned_at,
                    "new_count": s.new_count,
                    "resolved_count": s.resolved_count,
                    "reopened_count": s.reopened_count,
                    "total_findings_count": s.total_findings_count,
                }
                for s in recent_scans
            ],
        }
    )
