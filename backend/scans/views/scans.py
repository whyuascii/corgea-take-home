from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.pagination import paginate_queryset
from ..models import Scan
from ..serializers import ScanSerializer
from .helpers import get_project_for_user


@api_view(["GET"])
def scan_list(request, project_slug):
    """List all scans for a project, ordered by most recent first."""
    project = get_project_for_user(request, project_slug)
    scans = Scan.objects.filter(project=project).only(
        "id", "project_id", "scanned_at", "source",
        "total_findings_count", "new_count", "resolved_count",
        "reopened_count", "commit_sha", "branch", "ci_provider",
        "created_by_id", "created_at",
    )
    return paginate_queryset(scans, request, ScanSerializer)


@api_view(["GET"])
def scan_detail(request, project_slug, scan_id):
    """Retrieve details of a single scan by ID."""
    project = get_project_for_user(request, project_slug)
    scan = get_object_or_404(Scan, id=scan_id, project=project)
    serializer = ScanSerializer(scan)
    return Response(serializer.data)


@api_view(["GET"])
def scan_latest(request, project_slug):
    """Retrieve the most recent scan for a project, or 404 if no scans exist."""
    project = get_project_for_user(request, project_slug)
    scan = Scan.objects.filter(project=project).first()
    if not scan:
        return Response({"detail": "No scans found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(ScanSerializer(scan).data)
