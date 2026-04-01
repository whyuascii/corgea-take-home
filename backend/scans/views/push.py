import hmac
import logging

from django.core.cache import cache
from django.db import DatabaseError
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.constants import (
    MAX_UPLOAD_BYTES, SCAN_PUSH_RATE_LIMIT, SCAN_PUSH_RATE_WINDOW,
    VALID_SCANNER_TYPES,
)
from core.audit import log_audit
from findings.models import AuditLog
from projects.models import Project
from ..models import Scan
from ..serializers import ScanPushSerializer, ScanSerializer

logger = logging.getLogger(__name__)

try:
    from django_q.tasks import async_task

    _HAS_DJANGO_Q = True
except ImportError:
    _HAS_DJANGO_Q = False


def _check_content_length(request):
    """Return an error Response if Content-Length is invalid or too large, else None."""
    try:
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
    except (ValueError, TypeError):
        return Response(
            {"error": "Invalid Content-Length header."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if content_length > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return Response(
            {"error": f"Request too large. Maximum size is {max_mb}MB."},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
    return None


def _authenticate_api_key(request, project_slug):
    """Validate the Api-Key header and resolve the project.

    Returns (project, using_old_key) on success, or (Response, None) on failure.
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Api-Key "):
        return Response(
            {"error": "Api-Key header required"},
            status=status.HTTP_401_UNAUTHORIZED,
        ), None

    api_key = auth_header[len("Api-Key "):]

    # Multiple owners can have projects with the same slug; iterate to
    # find the one whose key matches (constant-time comparison).
    for candidate in Project.objects.filter(slug=project_slug):
        if hmac.compare_digest(candidate.api_key, api_key):
            return candidate, False
        if candidate.is_old_key_valid() and hmac.compare_digest(
            candidate.old_api_key, api_key
        ):
            return candidate, True

    return Response(
        {"error": "Invalid API key or project"},
        status=status.HTTP_401_UNAUTHORIZED,
    ), None


def _check_rate_limit(project):
    """Return an error Response if the project has exceeded push rate limits, else None."""
    rate_key = f"scan_push_{project.id}"
    cache.add(rate_key, 0, timeout=SCAN_PUSH_RATE_WINDOW)
    push_count = cache.incr(rate_key)

    if push_count > SCAN_PUSH_RATE_LIMIT:
        return Response(
            {"error": f"Rate limit exceeded. Maximum {SCAN_PUSH_RATE_LIMIT} pushes per hour."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return None


def _ingest_scan(scan):
    """Dispatch ingestion async if possible, otherwise run synchronously.

    Returns (response_data, response_code).
    """
    if _HAS_DJANGO_Q:
        try:
            async_task("scans.tasks.ingest_scan_async", str(scan.id))
            return (
                {"scan": ScanSerializer(scan).data, "status": "processing"},
                status.HTTP_202_ACCEPTED,
            )
        except (DatabaseError, ConnectionError, OSError):
            logger.debug("Failed to enqueue async ingestion for scan %s", scan.id)

    from ..ingestion import ingest_scan

    summary = ingest_scan(scan)
    scan.refresh_from_db()
    return (
        {"scan": ScanSerializer(scan).data, "summary": summary},
        status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def scan_push(request, project_slug):
    """Push scan results from CI/CD."""
    error = _check_content_length(request)
    if error:
        return error

    result, using_old_key = _authenticate_api_key(request, project_slug)
    if isinstance(result, Response):
        return result
    project = result

    error = _check_rate_limit(project)
    if error:
        return error

    serializer = ScanPushSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    Project.objects.filter(id=project.id).update(last_used_at=timezone.now())

    scanner_type = request.query_params.get("scanner", "semgrep")
    if scanner_type not in VALID_SCANNER_TYPES:
        scanner_type = "semgrep"

    scan = Scan.objects.create(
        project=project,
        source=Scan.Source.API,
        scanner_type=scanner_type,
        raw_report={
            "results": serializer.validated_data["results"],
            "errors": serializer.validated_data.get("errors", []),
        },
        commit_sha=serializer.validated_data.get("commit_sha", ""),
        branch=serializer.validated_data.get("branch", ""),
        ci_provider=serializer.validated_data.get("ci_provider", ""),
    )

    response_data, response_code = _ingest_scan(scan)
    log_audit(request, AuditLog.Action.SCAN_PUSH, "scan", scan.id, project)

    response = Response(response_data, status=response_code)
    if using_old_key:
        response["X-VulnTracker-Key-Deprecation"] = (
            f"This API key is deprecated and will expire at {project.old_key_expires_at.isoformat()}. "
            "Please update to the new key."
        )
    return response
