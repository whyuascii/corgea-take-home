import json
import os

from rest_framework import serializers

from core.constants import (
    ALLOWED_CONTENT_TYPES, ALLOWED_EXTENSIONS, JSON_MAX_NESTING_DEPTH,
    MAX_SCAN_RESULTS, MAX_UPLOAD_BYTES,
)
from .models import Scan


def _check_json_depth(raw: str):
    """Reject JSON payloads nested deeper than JSON_MAX_NESTING_DEPTH."""
    depth = 0
    in_string = False
    escape = False
    for ch in raw:
        if escape:
            escape = False
            continue
        if ch == "\\":
            if in_string:
                escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            depth += 1
            if depth > JSON_MAX_NESTING_DEPTH:
                raise serializers.ValidationError(
                    f"JSON nesting exceeds maximum depth of {JSON_MAX_NESTING_DEPTH}."
                )
        elif ch in ("}", "]"):
            depth -= 1


class ScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scan
        fields = [
            "id", "project", "scanned_at", "source", "scanner_type",
            "total_findings_count", "new_count", "resolved_count",
            "reopened_count", "commit_sha", "branch", "ci_provider",
            "created_by", "created_at", "archived_at",
        ]
        read_only_fields = fields


class ScanUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        ext = os.path.splitext(value.name or "")[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
            )

        content_type = (value.content_type or "").split(";")[0].strip().lower()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                f"Unsupported content type '{content_type}'. Upload a JSON file."
            )

        if value.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("File too large. Maximum size is 50MB.")

        try:
            raw_bytes = value.read()

            if b"\x00" in raw_bytes:
                raise serializers.ValidationError(
                    "File contains null bytes and is not valid JSON."
                )

            stripped = raw_bytes.lstrip()
            if stripped and stripped[0:1] not in (b"{", b"["):
                raise serializers.ValidationError(
                    "File does not appear to be JSON. Expected '{' or '[' at start."
                )

            content = raw_bytes.decode("utf-8")
            _check_json_depth(content)
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
                "Invalid scan report: expected a JSON object, got "
                f"{type(data).__name__}."
            )

        has_results = "results" in data and isinstance(data.get("results"), list)
        has_runs = "runs" in data and isinstance(data.get("runs"), list)
        if not has_results and not has_runs:
            raise serializers.ValidationError(
                "Invalid scan report: expected 'results' (Semgrep) or 'runs' (SARIF) key. "
                "Ensure your scanner output is in a supported format."
            )
        return data


class ScanPushSerializer(serializers.Serializer):
    results = serializers.ListField(required=True, max_length=MAX_SCAN_RESULTS)
    errors = serializers.ListField(required=False, default=[])
    version = serializers.CharField(required=False, default="", max_length=50)
    commit_sha = serializers.CharField(required=False, default="", max_length=64)
    branch = serializers.CharField(required=False, default="", max_length=256)
    ci_provider = serializers.CharField(required=False, default="", max_length=100)

    def validate_results(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("'results' must be a list.")
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    f"Result at index {i} must be an object, got {type(item).__name__}."
                )
        return value
