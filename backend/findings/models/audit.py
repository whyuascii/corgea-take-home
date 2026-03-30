import uuid
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        PROJECT_CREATE = "project_create"
        PROJECT_DELETE = "project_delete"
        SCAN_UPLOAD = "scan_upload"
        SCAN_PUSH = "scan_push"
        FINDING_STATUS_CHANGE = "finding_status_change"
        FINDING_FALSE_POSITIVE = "finding_false_positive"
        RULE_STATUS_CHANGE = "rule_status_change"
        INTEGRATION_CHANGE = "integration_change"
        API_KEY_REGENERATE = "api_key_regenerate"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=50, choices=Action.choices)
    target_type = models.CharField(max_length=50)
    target_id = models.CharField(max_length=100, blank=True, default="")
    project = models.ForeignKey(
        "projects.Project", on_delete=models.SET_NULL, null=True, blank=True
    )
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"
