from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from core.throttles import IntegrationTestThrottle
from core.audit import log_audit
from findings.models import AuditLog
from projects.membership import ProjectMembership
from ..models import IntegrationConfig
from ..serializers import IntegrationConfigSerializer
from projects.permissions import get_project_for_user


@api_view(["GET", "POST"])
def integration_list(request, project_slug):
    """List all integrations for a project, or create a new integration configuration."""
    min_role = ProjectMembership.Role.ADMIN if request.method == "POST" else ProjectMembership.Role.VIEWER
    project = get_project_for_user(request, project_slug, min_role=min_role)

    if request.method == "GET":
        configs = IntegrationConfig.objects.filter(project=project)
        serializer = IntegrationConfigSerializer(configs, many=True)
        return Response(serializer.data)

    serializer = IntegrationConfigSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save(project=project)
    log_audit(
        request, AuditLog.Action.INTEGRATION_CHANGE, "integration", instance.id, project,
        metadata={"action": "created", "provider": instance.provider},
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
def integration_detail(request, project_slug, integration_id):
    """Retrieve, update, or delete a specific integration configuration."""
    min_role = ProjectMembership.Role.ADMIN if request.method in ("PATCH", "DELETE") else ProjectMembership.Role.VIEWER
    project = get_project_for_user(request, project_slug, min_role=min_role)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)

    if request.method == "GET":
        serializer = IntegrationConfigSerializer(config)
        return Response(serializer.data)

    if request.method == "DELETE":
        log_audit(
            request, AuditLog.Action.INTEGRATION_CHANGE, "integration", config.id, project,
            metadata={"action": "deleted", "provider": config.provider},
        )
        config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = IntegrationConfigSerializer(config, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    log_audit(
        request, AuditLog.Action.INTEGRATION_CHANGE, "integration", config.id, project,
        metadata={"action": "updated", "provider": config.provider},
    )
    return Response(serializer.data)


@api_view(["POST"])
@throttle_classes([IntegrationTestThrottle])
def integration_test(request, project_slug, integration_id):
    """Test connectivity to the configured external service (Jira or Linear)."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.ADMIN)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)

    if config.provider == IntegrationConfig.Provider.JIRA:
        from ..jira_client import test_jira_connection
        result = test_jira_connection(config)
    elif config.provider == IntegrationConfig.Provider.LINEAR:
        from ..linear_client import test_linear_connection
        result = test_linear_connection(config)
    else:
        result = {"ok": False, "error": "Unknown provider"}

    return Response(result)
