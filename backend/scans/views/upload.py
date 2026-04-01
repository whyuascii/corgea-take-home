from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from core.throttles import ScanUploadThrottle
from core.audit import log_audit
from findings.models import AuditLog
from projects.membership import ProjectMembership
from scans.parsers import detect_format
from ..models import Scan
from ..serializers import ScanSerializer, ScanUploadSerializer
from ..ingestion import ingest_scan
from projects.permissions import get_project_for_user


@api_view(["POST"])
@throttle_classes([ScanUploadThrottle])
def scan_upload(request, project_slug):
    """Upload a scan report file (Semgrep JSON or SARIF) and ingest its findings."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.MEMBER)
    serializer = ScanUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    report_data = serializer.validated_data["file"]

    scanner_type = detect_format(report_data)

    scan = Scan.objects.create(
        project=project,
        source=Scan.Source.UPLOAD,
        scanner_type=scanner_type,
        raw_report=report_data,
        created_by=request.user,
    )
    summary = ingest_scan(scan)
    log_audit(request, AuditLog.Action.SCAN_UPLOAD, "scan", scan.id, project)
    return Response(
        {"scan": ScanSerializer(scan).data, "summary": summary},
        status=status.HTTP_201_CREATED,
    )
