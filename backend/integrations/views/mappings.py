from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.audit import log_audit
from findings.models import AuditLog
from projects.membership import ProjectMembership
from ..models import IntegrationConfig, StatusMapping
from ..serializers import StatusMappingSerializer
from projects.permissions import get_project_for_user
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Integrations"], responses=StatusMappingSerializer)
@api_view(["GET", "POST"])
def mapping_list(request, project_slug, integration_id):
    """List or create status mappings between external service statuses and internal finding statuses."""
    min_role = ProjectMembership.Role.ADMIN if request.method == "POST" else ProjectMembership.Role.VIEWER
    project = get_project_for_user(request, project_slug, min_role=min_role)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)

    if request.method == "GET":
        mappings = StatusMapping.objects.filter(integration=config)
        serializer = StatusMappingSerializer(mappings, many=True)
        return Response(serializer.data)

    serializer = StatusMappingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    mapping = serializer.save(integration=config)
    log_audit(
        request, AuditLog.Action.INTEGRATION_CHANGE, "mapping", mapping.id,
        project, {"action": "mapping_created"},
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Integrations"], responses=StatusMappingSerializer)
@api_view(["PATCH", "DELETE"])
def mapping_detail(request, project_slug, integration_id, mapping_id):
    """Update or delete a specific status mapping."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.ADMIN)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)
    mapping = get_object_or_404(StatusMapping, id=mapping_id, integration=config)

    if request.method == "DELETE":
        log_audit(
            request, AuditLog.Action.INTEGRATION_CHANGE, "mapping", mapping.id,
            project, {"action": "mapping_deleted"},
        )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = StatusMappingSerializer(mapping, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    log_audit(
        request, AuditLog.Action.INTEGRATION_CHANGE, "mapping", mapping.id,
        project, {"action": "mapping_updated"},
    )
    return Response(serializer.data)
