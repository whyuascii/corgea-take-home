from rest_framework import serializers

from .models import IntegrationConfig, StatusMapping


class StatusMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusMapping
        fields = ["id", "external_status", "internal_status"]
        read_only_fields = ["id"]


class IntegrationConfigSerializer(serializers.ModelSerializer):
    status_mappings = StatusMappingSerializer(many=True, read_only=True)
    jira_api_token_set = serializers.SerializerMethodField()
    linear_api_key_set = serializers.SerializerMethodField()

    class Meta:
        model = IntegrationConfig
        fields = [
            "id", "provider", "is_enabled",
            "jira_instance_url", "jira_project_key", "jira_api_token",
            "jira_user_email", "jira_api_token_set",
            "linear_api_key", "linear_team_id", "linear_api_key_set",
            "webhook_secret",
            "status_mappings",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "webhook_secret", "created_at", "updated_at"]
        extra_kwargs = {
            "jira_api_token": {"write_only": True, "required": False},
            "linear_api_key": {"write_only": True, "required": False},
        }

    def get_jira_api_token_set(self, obj):
        return bool(obj.jira_api_token)

    def get_linear_api_key_set(self, obj):
        return bool(obj.linear_api_key)

    def update(self, instance, validated_data):
        # Don't clear tokens if not provided in PATCH
        if "jira_api_token" in validated_data and not validated_data["jira_api_token"]:
            validated_data.pop("jira_api_token")
        if "linear_api_key" in validated_data and not validated_data["linear_api_key"]:
            validated_data.pop("linear_api_key")
        return super().update(instance, validated_data)
