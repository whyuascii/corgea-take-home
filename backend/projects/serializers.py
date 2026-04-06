from django.db.models import Count, Q
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field
from findings.models import Finding
from scans.models import Scan

from .membership import ProjectMembership
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    findings_summary = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    api_key_hint = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "owner", "name", "slug", "description",
            "repository_url", "api_key_hint", "findings_summary",
            "user_role", "created_at", "updated_at", "last_used_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "last_used_at"]

    def _get_membership(self, obj):
        """Return membership from prefetched map if available, else query."""
        membership_map = self.context.get("membership_map")
        if membership_map is not None:
            return membership_map.get(obj.pk)
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return ProjectMembership.objects.filter(
            project=obj, user=request.user
        ).first()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_api_key_hint(self, obj):
        """Return a masked preview of the API key for privileged users only."""
        membership = self._get_membership(obj)
        is_privileged = membership and membership.role in (
            ProjectMembership.Role.OWNER, ProjectMembership.Role.ADMIN
        )
        if not is_privileged:
            return None
        key = obj.api_key
        if key and len(key) > 8:
            return f"{key[:4]}...{key[-4:]}"
        return "****"

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_user_role(self, obj):
        membership = self._get_membership(obj)
        return membership.role if membership else None

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_findings_summary(self, obj):
        membership = self._get_membership(obj)
        if not membership:
            return None

        # Use prefetched annotations if the queryset provided them (list view),
        # otherwise fall back to per-object aggregate (detail view).
        if hasattr(obj, "_findings_new"):
            return {
                "new": obj._findings_new,
                "open": obj._findings_open,
                "reopened": obj._findings_reopened,
                "resolved": obj._findings_resolved,
                "ignored": obj._findings_ignored,
                "false_positive": obj._findings_fp,
                "total": obj._findings_total,
                "critical": obj._findings_critical,
                "last_scan_at": obj._last_scan_at.isoformat() if obj._last_scan_at else None,
            }

        agg = Finding.objects.filter(project=obj).aggregate(
            new=Count("id", filter=Q(status="new")),
            open=Count("id", filter=Q(status="open")),
            reopened=Count("id", filter=Q(status="reopened")),
            resolved=Count("id", filter=Q(status="resolved")),
            ignored=Count("id", filter=Q(status="ignored")),
            false_positive=Count("id", filter=Q(is_false_positive=True)),
            total=Count("id"),
            critical=Count(
                "id",
                filter=Q(rule__severity="ERROR") & ~Q(status="resolved"),
            ),
        )

        latest_scan = Scan.objects.filter(project=obj).only("scanned_at").first()

        return {
            **agg,
            "last_scan_at": latest_scan.scanned_at.isoformat() if latest_scan else None,
        }
