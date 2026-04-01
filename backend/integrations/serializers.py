from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from .models import IntegrationConfig, StatusMapping
from .validators import validate_external_url


class StatusMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusMapping
        fields = ["id", "external_status", "internal_status"]
        read_only_fields = ["id"]


class IntegrationConfigSerializer(serializers.ModelSerializer):
    status_mappings = StatusMappingSerializer(many=True, read_only=True)
    jira_api_token_set = serializers.SerializerMethodField()
    linear_api_key_set = serializers.SerializerMethodField()
    webhook_url = serializers.SerializerMethodField()

    class Meta:
        model = IntegrationConfig
        fields = [
            "id", "provider", "is_enabled",
            "jira_instance_url", "jira_project_key", "jira_api_token",
            "jira_user_email", "jira_api_token_set",
            "linear_api_key", "linear_team_id", "linear_api_key_set",
            # webhook_secret intentionally excluded — it is only exposed
            # once at creation time in the view, not on every GET.
            "webhook_url",
            "status_mappings",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "jira_api_token": {"write_only": True, "required": False},
            "linear_api_key": {"write_only": True, "required": False},
        }

    def get_jira_api_token_set(self, obj):
        return bool(obj.jira_api_token)

    def get_linear_api_key_set(self, obj):
        return bool(obj.linear_api_key)

    def get_webhook_url(self, obj):
        """Return the webhook path with a masked secret for display only."""
        if obj.webhook_secret:
            masked = obj.webhook_secret[:4] + "****"
            return f"/api/webhooks/{obj.provider}/{masked}/"
        return ""

    def validate_jira_instance_url(self, value):
        """Validate URL format and prevent SSRF by blocking private/internal URLs."""
        if value:
            validator = URLValidator(schemes=['https', 'http'])
            try:
                validator(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Invalid URL format for Jira base URL")
            validate_external_url(value)
            # Strip trailing slash for consistency
            value = value.rstrip('/')
        return value

    def validate_linear_team_id(self, value):
        """Validate that the Linear team ID contains only alphanumeric characters, hyphens, and underscores."""
        if value and not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError("Linear team ID must be alphanumeric")
        return value

    def update(self, instance, validated_data):
        # Don't clear tokens if not provided in PATCH
        if "jira_api_token" in validated_data and not validated_data["jira_api_token"]:
            validated_data.pop("jira_api_token")
        if "linear_api_key" in validated_data and not validated_data["linear_api_key"]:
            validated_data.pop("linear_api_key")
        return super().update(instance, validated_data)
