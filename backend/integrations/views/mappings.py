from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import IntegrationConfig, StatusMapping
from ..serializers import StatusMappingSerializer
from .helpers import get_project_for_user


@api_view(["GET", "POST"])
def mapping_list(request, project_slug, integration_id):
    """List or create status mappings between external service statuses and internal finding statuses."""
    project = get_project_for_user(request, project_slug)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)

    if request.method == "GET":
        mappings = StatusMapping.objects.filter(integration=config)
        serializer = StatusMappingSerializer(mappings, many=True)
        return Response(serializer.data)

    serializer = StatusMappingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(integration=config)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def mapping_detail(request, project_slug, integration_id, mapping_id):
    """Update or delete a specific status mapping."""
    project = get_project_for_user(request, project_slug)
    config = get_object_or_404(IntegrationConfig, id=integration_id, project=project)
    mapping = get_object_or_404(StatusMapping, id=mapping_id, integration=config)

    if request.method == "DELETE":
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = StatusMappingSerializer(mapping, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
