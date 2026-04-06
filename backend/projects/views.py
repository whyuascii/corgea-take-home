from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q, Subquery
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import viewsets
from rest_framework.decorators import action, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.throttles import ApiKeyRotationThrottle
from core.audit import log_audit
from findings.models import AuditLog, Finding
from scans.models import Scan

from .membership import ProjectMembership
from .models import Project, generate_api_key
from .permissions import HasProjectRole
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticated, HasProjectRole]
    action_roles = {
        "update": ProjectMembership.Role.ADMIN,
        "partial_update": ProjectMembership.Role.ADMIN,
        "destroy": ProjectMembership.Role.OWNER,
        "rotate_api_key": ProjectMembership.Role.OWNER,
    }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()
        qs = (
            Project.objects.filter(memberships__user=self.request.user)
            .select_related("owner")
            .distinct()
        )
        # Annotate finding counts to avoid N+1 in ProjectSerializer.get_findings_summary
        if self.action == "list":
            qs = qs.annotate(
                _findings_new=Count("findings", filter=Q(findings__status="new")),
                _findings_open=Count("findings", filter=Q(findings__status="open")),
                _findings_reopened=Count("findings", filter=Q(findings__status="reopened")),
                _findings_resolved=Count("findings", filter=Q(findings__status="resolved")),
                _findings_ignored=Count("findings", filter=Q(findings__status="ignored")),
                _findings_fp=Count("findings", filter=Q(findings__is_false_positive=True)),
                _findings_total=Count("findings"),
                _findings_critical=Count(
                    "findings",
                    filter=Q(findings__rule__severity="ERROR") & ~Q(findings__status="resolved"),
                ),
                _last_scan_at=Max("scans__scanned_at"),
            )
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            ctx["membership_map"] = {
                m.project_id: m
                for m in ProjectMembership.objects.filter(user=self.request.user)
            }
        return ctx

    def perform_create(self, serializer):
        base_slug = slugify(serializer.validated_data["name"])
        slug = base_slug
        suffix = 1
        while Project.objects.filter(owner=self.request.user, slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        max_retries = 3
        for attempt in range(max_retries):
            try:
                instance = serializer.save(owner=self.request.user, slug=slug)
                break
            except IntegrityError:
                if attempt == max_retries - 1:
                    raise
                # Race condition: another request created the same slug between
                # the exists() check and the save(). Bump the suffix and retry.
                suffix += 1
                slug = f"{base_slug}-{suffix}"

        ProjectMembership.objects.get_or_create(
            project=instance, user=self.request.user,
            defaults={"role": ProjectMembership.Role.OWNER},
        )
        log_audit(self.request, AuditLog.Action.PROJECT_CREATE, "project", instance.id, instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(
            self.request, AuditLog.Action.PROJECT_UPDATE, "project",
            instance.id, instance,
        )

    def perform_destroy(self, instance):
        log_audit(self.request, AuditLog.Action.PROJECT_DELETE, "project", instance.id, instance)
        instance.delete()

    @action(detail=True, methods=["post"])
    @throttle_classes([ApiKeyRotationThrottle])
    def rotate_api_key(self, request, slug=None):
        """Rotate API key with grace period for old key."""
        with transaction.atomic():
            project = (
                Project.objects.select_for_update()
                .get(pk=self.get_object().pk)
            )
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

