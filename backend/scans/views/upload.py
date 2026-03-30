from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Scan
from ..serializers import ScanSerializer, ScanUploadSerializer
from ..ingestion import ingest_scan
from .helpers import get_project_for_user


@api_view(["POST"])
def scan_upload(request, project_slug):
    """Upload a Semgrep JSON report file to create a new scan and ingest its findings."""
    project = get_project_for_user(request, project_slug)
    serializer = ScanUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    report_data = serializer.validated_data["file"]
    scan = Scan.objects.create(
        project=project,
        source=Scan.Source.UPLOAD,
        raw_report=report_data,
        created_by=request.user,
    )
    summary = ingest_scan(scan)
    from findings.audit import log_audit
    from findings.models import AuditLog
    log_audit(request, AuditLog.Action.SCAN_UPLOAD, "scan", scan.id, project)
    return Response(
        {"scan": ScanSerializer(scan).data, "summary": summary},
        status=status.HTTP_201_CREATED,
    )
