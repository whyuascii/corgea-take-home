from datetime import timedelta

from django.utils import timezone
from django.utils.text import slugify
from rest_framework import viewsets
from rest_framework.decorators import action, throttle_classes
from rest_framework.response import Response

from core.throttles import ApiKeyRotationThrottle
from core.audit import log_audit
from findings.models import AuditLog

from .membership import ProjectMembership
from .models import Project, generate_api_key
from .permissions import get_project_for_user
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    lookup_field = "slug"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        return Project.objects.filter(
            memberships__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        slug = slugify(serializer.validated_data["name"])
        instance = serializer.save(owner=self.request.user, slug=slug)

        ProjectMembership.objects.get_or_create(
            project=instance, user=self.request.user,
            defaults={"role": ProjectMembership.Role.OWNER},
        )
        log_audit(self.request, AuditLog.Action.PROJECT_CREATE, "project", instance.id, instance)

    def perform_update(self, serializer):
        get_project_for_user(
            self.request, serializer.instance.slug,
            min_role=ProjectMembership.Role.ADMIN,
        )
        instance = serializer.save()
        log_audit(
            self.request, AuditLog.Action.PROJECT_UPDATE, "project",
            instance.id, instance,
        )

    def perform_destroy(self, instance):

        get_project_for_user(self.request, instance.slug, min_role=ProjectMembership.Role.OWNER)
        log_audit(self.request, AuditLog.Action.PROJECT_DELETE, "project", instance.id, instance)
        instance.delete()

    @action(detail=True, methods=["post"])
    @throttle_classes([ApiKeyRotationThrottle])
    def rotate_api_key(self, request, slug=None):
        """Rotate API key with grace period for old key."""
        project = get_project_for_user(request, slug, min_role=ProjectMembership.Role.OWNER)

        project.old_api_key = project.api_key
        project.old_key_expires_at = timezone.now() + timedelta(hours=project.api_key_grace_period_hours)
        project.api_key = generate_api_key()
        project.save(update_fields=["api_key", "old_api_key", "old_key_expires_at"])
        log_audit(request, AuditLog.Action.API_KEY_REGENERATE, "project", project.id, project)
        response = Response({
            "api_key": project.api_key,
            "old_key_expires_at": project.old_key_expires_at.isoformat(),
            "grace_period_hours": project.api_key_grace_period_hours,
        })
        response["Cache-Control"] = "no-store"
        return response

