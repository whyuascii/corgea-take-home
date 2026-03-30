from rest_framework import serializers
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    findings_summary = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "owner", "name", "slug", "description",
            "repository_url", "api_key", "findings_summary",
            "created_at", "updated_at", "last_used_at",
        ]
        read_only_fields = ["id", "slug", "api_key", "created_at", "updated_at", "last_used_at"]

    def get_findings_summary(self, obj):
        from findings.models import Finding
        from scans.models import Scan

        qs = Finding.objects.filter(project=obj)
        latest_scan = Scan.objects.filter(project=obj).first()

        return {
            "new": qs.filter(status="new").count(),
            "open": qs.filter(status="open").count(),
            "reopened": qs.filter(status="reopened").count(),
            "resolved": qs.filter(status="resolved").count(),
            "ignored": qs.filter(status="ignored").count(),
            "false_positive": qs.filter(is_false_positive=True).count(),
            "total": qs.count(),
            "critical": qs.filter(rule__severity="ERROR").exclude(status="resolved").count(),
            "last_scan_at": latest_scan.scanned_at.isoformat() if latest_scan else None,
        }
