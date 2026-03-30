from rest_framework import serializers
from .models import AuditLog, Finding, FindingComment, FindingHistory, Rule


class RuleSerializer(serializers.ModelSerializer):
    active_finding_count = serializers.SerializerMethodField()
    total_finding_count = serializers.SerializerMethodField()

    class Meta:
        model = Rule
        fields = [
            "id", "semgrep_rule_id", "severity", "message",
            "category", "status", "active_finding_count",
            "total_finding_count", "created_at",
        ]
        read_only_fields = ["id", "semgrep_rule_id", "severity", "message", "created_at"]

    def get_active_finding_count(self, obj):
        """Count of findings that are not ignored and not marked as false positive."""
        return obj.findings.exclude(
            status=Finding.Status.IGNORED
        ).exclude(
            is_false_positive=True
        ).count()

    def get_total_finding_count(self, obj):
        """Count of all findings for this rule, regardless of status."""
        return obj.findings.count()


class FindingHistorySerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(
        source="changed_by.username", read_only=True, default=None
    )

    class Meta:
        model = FindingHistory
        fields = [
            "id", "change_type", "old_status", "new_status",
            "changed_by_username", "scan", "jira_ticket_url",
            "linear_ticket_url", "pr_url", "notes", "created_at",
        ]


class FindingSerializer(serializers.ModelSerializer):
    rule_id_display = serializers.CharField(source="rule.semgrep_rule_id", read_only=True)
    rule_message = serializers.CharField(source="rule.message", read_only=True)
    severity = serializers.CharField(source="rule.severity", read_only=True)
    effective_severity = serializers.SerializerMethodField()

    class Meta:
        model = Finding
        fields = [
            "id", "rule", "rule_id_display", "rule_message", "severity", "severity_override",
            "effective_severity",
            "file_path", "line_start", "line_end", "code_snippet", "metadata",
            "status", "is_false_positive", "false_positive_reason",
            "first_seen_scan", "last_seen_scan",
            "jira_ticket_id", "jira_ticket_url",
            "linear_ticket_id", "linear_ticket_url",
            "pr_url",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "rule", "file_path", "line_start", "line_end", "metadata",
            "is_false_positive", "false_positive_reason",
            "first_seen_scan", "last_seen_scan", "created_at", "updated_at",
        ]

    def get_effective_severity(self, obj):
        return obj.severity_override or obj.rule.severity


class FindingCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = FindingComment
        fields = ["id", "username", "text", "created_at", "updated_at"]
        read_only_fields = ["id", "username", "created_at", "updated_at"]


class FindingDetailSerializer(FindingSerializer):
    history = FindingHistorySerializer(many=True, read_only=True)
    comments = FindingCommentSerializer(many=True, read_only=True)

    class Meta(FindingSerializer.Meta):
        fields = FindingSerializer.Meta.fields + ["history", "comments"]


class OverviewFindingSerializer(FindingSerializer):
    project_slug = serializers.CharField(source="project.slug", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta(FindingSerializer.Meta):
        fields = FindingSerializer.Meta.fields + ["project_slug", "project_name"]


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "target_type",
            "target_id",
            "user",
            "metadata",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
