from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import IntegrationConfig
from ..serializers import IntegrationConfigSerializer
from .helpers import get_project_for_user


@api_view(["GET", "POST"])
def integration_list(request, project_slug):
    """List all integrations for a project, or create a new integration configuration."""
    project = get_project_for_user(request, project_slug)

    if request.method == "GET":
        configs = IntegrationConfig.objects.filter(project=project)
        serializer = IntegrationConfigSerializer(configs, many=True)
        return Response(serializer.data)

    serializer = IntegrationConfigSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(project=project)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
def integration_detail(request, project_slug, integration_id):
    """Retrieve, update, or delete a specific integration configuration."""
    project = get_project_for_user(request, project_slug)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)

    if request.method == "GET":
        serializer = IntegrationConfigSerializer(config)
        return Response(serializer.data)

    if request.method == "DELETE":
        config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = IntegrationConfigSerializer(config, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
def integration_test(request, project_slug, integration_id):
    """Test connectivity to the configured external service (Jira or Linear)."""
    project = get_project_for_user(request, project_slug)
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
