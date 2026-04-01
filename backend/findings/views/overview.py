from django.db.models import Count, F, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.cache import cached_view
from core.constants import CACHE_TTL_OVERVIEW, OVERVIEW_BREAKDOWN_LIMIT, OVERVIEW_RULES_LIMIT
from core.pagination import paginate_list, paginate_queryset
from projects.models import Project
from ..models import Finding, Rule
from ..serializers import OverviewFindingSerializer


def _user_project_ids(user):
    """Return project IDs the user has any membership on."""
    return Project.objects.filter(
        memberships__user=user
    ).values_list("id", flat=True).distinct()


@api_view(["GET"])
def overview_rules(request):
    """List rules across all of the authenticated user's projects.
    """
    project_ids = _user_project_ids(request.user)
    severity = request.query_params.get("severity")

    rules_qs = Rule.objects.filter(project_id__in=project_ids)
    if severity:
        rules_qs = rules_qs.filter(severity=severity)

    # Aggregated rule-level data
    rule_data = list(
        rules_qs.values("semgrep_rule_id", "severity", "message")
        .annotate(
            finding_count=Count("findings"),
            false_positive_count=Count(
                "findings", filter=Q(findings__is_false_positive=True)
            ),
            project_count=Count("project", distinct=True),
        )
        .order_by("-finding_count")[:OVERVIEW_RULES_LIMIT]
    )

    # Fetch ALL project breakdowns in a single query, then group in Python.
    all_breakdowns = (
        rules_qs.values(
            "semgrep_rule_id",
            slug=F("project__slug"),
            name=F("project__name"),
        )
        .annotate(finding_count=Count("findings"))
        .order_by("semgrep_rule_id")[:OVERVIEW_BREAKDOWN_LIMIT]
    )

    # Index breakdowns by semgrep_rule_id for lookup
    breakdown_map = {}
    for bd in all_breakdowns:
        breakdown_map.setdefault(bd["semgrep_rule_id"], []).append(
            {"slug": bd["slug"], "name": bd["name"], "finding_count": bd["finding_count"]}
        )

    result = []
    for rd in rule_data:
        result.append(
            {
                "semgrep_rule_id": rd["semgrep_rule_id"],
                "severity": rd["severity"],
                "message": rd["message"],
                "project_count": rd["project_count"],
                "finding_count": rd["finding_count"],
                "false_positive_count": rd["false_positive_count"],
                "projects": breakdown_map.get(rd["semgrep_rule_id"], []),
            }
        )

    return paginate_list(result, request)


@api_view(["GET"])
def overview_findings(request):
    """List findings across all of the authenticated user's projects, with optional filters for project, status, severity, and rule."""
    project_ids = _user_project_ids(request.user)
    findings = (
        Finding.objects.filter(project_id__in=project_ids)
        .select_related("rule", "project")
        .defer("code_snippet", "metadata")
    )

    project_slug = request.query_params.get("project")
    if project_slug:
        findings = findings.filter(project__slug=project_slug)
    finding_status = request.query_params.get("status")
    if finding_status:
        findings = findings.filter(status=finding_status)
    severity = request.query_params.get("severity")
    if severity:
        findings = findings.filter(rule__severity=severity)
    is_fp = request.query_params.get("is_false_positive")
    if is_fp is not None:
        findings = findings.filter(is_false_positive=is_fp.lower() == "true")
    rule_id = request.query_params.get("rule_id")
    if rule_id:
        findings = findings.filter(rule__semgrep_rule_id=rule_id)

    return paginate_queryset(findings, request, OverviewFindingSerializer)


@api_view(["GET"])
@cached_view("overview_summary", timeout=CACHE_TTL_OVERVIEW)
def overview_summary(request):
    """Return cross-project summary statistics"""
    project_ids = _user_project_ids(request.user)
    findings = Finding.objects.filter(project_id__in=project_ids)

    severity_dist = (
        findings.values(severity=F("rule__severity"))
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    project_activity = (
        findings.values(slug=F("project__slug"), name=F("project__name"))
        .annotate(
            total=Count("id"),
            active=Count("id", filter=Q(status__in=["new", "open", "reopened"])),
        )
        .order_by("-active")
    )

    return Response(
        {
            "total_findings": findings.count(),
            "total_active": findings.filter(status__in=["new", "open", "reopened"]).count(),
            "total_false_positives": findings.filter(is_false_positive=True).count(),
            "severity_distribution": list(severity_dist),
            "project_activity": list(project_activity),
        }
    )
