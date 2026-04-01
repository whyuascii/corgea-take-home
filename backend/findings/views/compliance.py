"""SLA tracking and compliance reporting views."""

from datetime import timedelta

from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.pagination import paginate_queryset
from findings.models import Finding, FindingHistory, SLAPolicy
from findings.serializers import FindingSerializer, SLAPolicySerializer
from projects.membership import ProjectMembership
from core.constants import DB_ITERATOR_CHUNK_SIZE, TOP_OWASP_LIMIT
from projects.permissions import get_project_for_user


@api_view(["GET"])
def compliance_dashboard(request, project_slug):
    """Return MTTR by severity, SLA compliance %, age distribution."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)

    # MTTR by severity — DB-level aggregation instead of Python iteration.
    # Computes avg(resolve_timestamp - finding_created_at) per severity.
    resolved_history = FindingHistory.objects.filter(
        finding__project=project,
        new_status=Finding.Status.RESOLVED,
    )
    mttr_aggregation = (
        resolved_history
        .values(severity=F("finding__rule__severity"))
        .annotate(
            avg_resolution_seconds=Avg(
                F("created_at") - F("finding__created_at")
            )
        )
    )
    mttr_by_severity = {}
    for row in mttr_aggregation:
        avg_dur = row["avg_resolution_seconds"]
        if avg_dur is not None:
            hours = avg_dur.total_seconds() / 3600
            mttr_by_severity[row["severity"]] = round(hours, 1)
    for severity in ["ERROR", "WARNING", "INFO"]:
        mttr_by_severity.setdefault(severity, None)

    # SLA compliance percentage
    findings_with_sla = Finding.objects.filter(project=project, sla_deadline__isnull=False)
    total_with_sla = findings_with_sla.count()
    breached_count = findings_with_sla.filter(sla_breached=True).count()
    compliance_pct = (
        round(((total_with_sla - breached_count) / total_with_sla * 100), 1)
        if total_with_sla > 0 else 100.0
    )

    # Age distribution — bucket active findings by age
    now = timezone.now()
    active = Finding.objects.filter(
        project=project,
        status__in=[Finding.Status.NEW, Finding.Status.OPEN, Finding.Status.REOPENED],
    )
    age_buckets = {
        "0-7d": active.filter(created_at__gte=now - timedelta(days=7)).count(),
        "7-30d": active.filter(
            created_at__lt=now - timedelta(days=7),
            created_at__gte=now - timedelta(days=30),
        ).count(),
        "30-90d": active.filter(
            created_at__lt=now - timedelta(days=30),
            created_at__gte=now - timedelta(days=90),
        ).count(),
        "90d+": active.filter(created_at__lt=now - timedelta(days=90)).count(),
    }

    # OWASP category breakdown from metadata — cap iteration to prevent
    # unbounded memory usage on projects with many active findings.
    owasp_counts = {}
    for finding in active.only("metadata").iterator(chunk_size=DB_ITERATOR_CHUNK_SIZE):
        owasp = finding.metadata.get("owasp", []) if isinstance(finding.metadata, dict) else []
        for cat in (owasp[:20] if isinstance(owasp, list) else []):
            owasp_counts[cat] = owasp_counts.get(cat, 0) + 1

    return Response({
        "mttr_by_severity": mttr_by_severity,
        "sla_compliance_pct": compliance_pct,
        "total_with_sla": total_with_sla,
        "breached_count": breached_count,
        "age_distribution": age_buckets,
        "owasp_categories": dict(sorted(owasp_counts.items(), key=lambda x: -x[1])[:TOP_OWASP_LIMIT]),
    })


@api_view(["GET"])
def sla_breaches(request, project_slug):
    """List findings that have breached their SLA deadline."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)

    breached = (
        Finding.objects.filter(project=project, sla_breached=True)
        .exclude(status__in=[Finding.Status.RESOLVED, Finding.Status.IGNORED])
        .select_related("rule")
        .order_by("-sla_deadline")
    )

    return paginate_queryset(breached, request, FindingSerializer)


@api_view(["GET", "POST"])
def sla_policies(request, project_slug):
    """List or create SLA policies for a project."""
    if request.method == "GET":
        project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER)
    else:
        project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.ADMIN)

    if request.method == "GET":
        policies = SLAPolicy.objects.filter(project=project)
        return Response(SLAPolicySerializer(policies, many=True).data)

    serializer = SLAPolicySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # Prevent duplicate policies for the same severity within a project
    severity = serializer.validated_data.get("severity")
    if SLAPolicy.objects.filter(project=project, severity=severity).exists():
        return Response(
            {"error": f"An SLA policy for severity '{severity}' already exists in this project."},
            status=status.HTTP_409_CONFLICT,
        )
    serializer.save(project=project)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def sla_policy_detail(request, project_slug, policy_id):
    """Update or delete an SLA policy."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.ADMIN)

    try:
        policy = SLAPolicy.objects.get(id=policy_id, project=project)
    except SLAPolicy.DoesNotExist:
        return Response({"error": "SLA policy not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        policy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SLAPolicySerializer(policy, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
