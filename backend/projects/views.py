from django.utils.text import slugify
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Project, generate_api_key
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        slug = slugify(serializer.validated_data["name"])
        instance = serializer.save(owner=self.request.user, slug=slug)
        from findings.audit import log_audit
        from findings.models import AuditLog
        log_audit(self.request, AuditLog.Action.PROJECT_CREATE, "project", instance.id, instance)

    @action(detail=True, methods=["post"])
    def regenerate_api_key(self, request, slug=None):
        project = self.get_object()
        project.api_key = generate_api_key()
        project.save(update_fields=["api_key"])
        from findings.audit import log_audit
        from findings.models import AuditLog
        log_audit(request, AuditLog.Action.API_KEY_REGENERATE, "project", project.id, project)
        return Response({"api_key": project.api_key})
