import uuid
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        # Auth events — critical for SOC 2 / compliance auditing.
        LOGIN = "login"
        LOGIN_FAILED = "login_failed"
        REGISTER = "register"
        LOGOUT = "logout"
        PROFILE_UPDATE = "profile_update"
        # Resource events
        PROJECT_CREATE = "project_create"
        PROJECT_UPDATE = "project_update"
        PROJECT_DELETE = "project_delete"
        SCAN_UPLOAD = "scan_upload"
        SCAN_PUSH = "scan_push"
        FINDING_STATUS_CHANGE = "finding_status_change"
        FINDING_FALSE_POSITIVE = "finding_false_positive"
        RULE_STATUS_CHANGE = "rule_status_change"
        COMMENT_CREATED = "comment_created"
        COMMENT_DELETED = "comment_deleted"
        INTEGRATION_CHANGE = "integration_change"
        API_KEY_REGENERATE = "api_key_regenerate"
        # Membership events
        MEMBER_ADDED = "member_added"
        MEMBER_REMOVED = "member_removed"
        MEMBER_ROLE_CHANGED = "member_role_changed"
        # Password reset events
        PASSWORD_RESET_REQUEST = "password_reset_request"
        PASSWORD_RESET_COMPLETE = "password_reset_complete"
        PASSWORD_CHANGE = "password_change"

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
