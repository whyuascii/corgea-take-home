import json
from rest_framework import serializers
from .models import Scan


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = [
            "id", "project", "scanned_at", "source",
            "total_findings_count", "new_count", "resolved_count",
            "reopened_count", "commit_sha", "branch", "ci_provider",
            "created_by", "created_at",
        ]
        read_only_fields = fields


class ScanUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if value.size > 50 * 1024 * 1024:  # 50MB
            raise serializers.ValidationError("File too large. Maximum size is 50MB.")
        try:
            content = value.read().decode("utf-8")
            data = json.loads(content)
        except UnicodeDecodeError:
            raise serializers.ValidationError(
                "File is not valid UTF-8 text. Please upload a JSON file."
            )
        except json.JSONDecodeError as e:
            raise serializers.ValidationError(
                f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}."
            )
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                "Invalid Semgrep report: expected a JSON object, got "
                f"{type(data).__name__}."
            )
        if "results" not in data:
            raise serializers.ValidationError(
                "Invalid Semgrep report: missing 'results' key. "
                "Ensure you ran semgrep with the --json flag."
            )
        if not isinstance(data["results"], list):
            raise serializers.ValidationError(
                "Invalid Semgrep report: 'results' must be a list."
            )
        return data


class ScanPushSerializer(serializers.Serializer):
    results = serializers.ListField(required=True)
    errors = serializers.ListField(required=False, default=[])
    version = serializers.CharField(required=False, default="")
    commit_sha = serializers.CharField(required=False, default="")
    branch = serializers.CharField(required=False, default="")
    ci_provider = serializers.CharField(required=False, default="")

    def validate_results(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("'results' must be a list.")
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    f"Result at index {i} must be an object, got {type(item).__name__}."
                )
        return value
