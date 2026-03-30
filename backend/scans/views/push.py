from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from projects.models import Project
from ..models import Scan
from ..serializers import ScanSerializer, ScanPushSerializer
from ..ingestion import ingest_scan


@api_view(["POST"])
@permission_classes([AllowAny])
def scan_push(request, project_slug):
    """Push Semgrep scan results from CI/CD. Authenticates via Api-Key header; rate-limited to 100 pushes/hour."""
    # Body size validation
    content_length = request.META.get('CONTENT_LENGTH')
    if content_length and int(content_length) > 50 * 1024 * 1024:
        return Response(
            {"error": "Request too large. Maximum size is 50MB."},
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Api-Key "):
        return Response(
            {"error": "Api-Key header required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    api_key = auth_header[len("Api-Key "):]
    try:
        project = Project.objects.get(slug=project_slug, api_key=api_key)
    except Project.DoesNotExist:
        return Response(
            {"error": "Invalid API key or project"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Rate limiting: max 100 pushes per hour per project.
    # NOTE: This uses Django's locmem cache which is per-process and will NOT
    # work correctly across multiple gunicorn/uvicorn workers.  In production,
    # configure a shared cache backend such as Redis
    # (django.core.cache.backends.redis.RedisCache) for accurate cross-process
    # rate limiting.
    from django.core.cache import cache

    rate_key = f"scan_push_{project.id}"
    push_count = cache.get(rate_key, 0)
    if push_count >= 100:
        return Response(
            {"error": "Rate limit exceeded. Maximum 100 pushes per hour."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    cache.set(rate_key, push_count + 1, timeout=3600)

    project.last_used_at = timezone.now()
    project.save(update_fields=["last_used_at"])

    serializer = ScanPushSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    scan = Scan.objects.create(
        project=project,
        source=Scan.Source.API,
        raw_report={
            "results": serializer.validated_data["results"],
            "errors": serializer.validated_data.get("errors", []),
        },
        commit_sha=serializer.validated_data.get("commit_sha", ""),
        branch=serializer.validated_data.get("branch", ""),
        ci_provider=serializer.validated_data.get("ci_provider", ""),
    )
    summary = ingest_scan(scan)
    from findings.audit import log_audit
    from findings.models import AuditLog

    log_audit(request, AuditLog.Action.SCAN_PUSH, "scan", scan.id, project)
    return Response(
        {"scan": ScanSerializer(scan).data, "summary": summary},
        status=status.HTTP_201_CREATED,
    )
