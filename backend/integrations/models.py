import secrets
import uuid

from django.db import models

from core.fields import EncryptedTextField


def generate_webhook_secret():
    return secrets.token_urlsafe(32)


class IntegrationConfig(models.Model):
    class Provider(models.TextChoices):
        JIRA = "jira"
        LINEAR = "linear"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="integrations"
    )
    provider = models.CharField(max_length=20, choices=Provider.choices)
    is_enabled = models.BooleanField(default=False)

    # Jira fields
    jira_instance_url = models.URLField(blank=True, default="")
    jira_project_key = models.CharField(max_length=50, blank=True, default="")
    jira_api_token = EncryptedTextField(blank=True, default="")
    jira_user_email = models.EmailField(blank=True, default="")

    # Linear fields
    linear_api_key = EncryptedTextField(blank=True, default="")
    linear_team_id = models.CharField(max_length=100, blank=True, default="")

    webhook_secret = models.CharField(
        max_length=64, default=generate_webhook_secret, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "provider")]
        ordering = ["provider"]

    def __str__(self):
        return f"{self.project.name} - {self.provider}"


class StatusMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(
        IntegrationConfig, on_delete=models.CASCADE, related_name="status_mappings"
    )
    external_status = models.CharField(max_length=100)
    internal_status = models.CharField(
        max_length=20,
        choices=[
            ("new", "New"),
            ("open", "Open"),
            ("resolved", "Resolved"),
            ("reopened", "Reopened"),
            ("ignored", "Ignored"),
        ],
    )

    class Meta:
        unique_together = [("integration", "external_status")]
        ordering = ["external_status"]

    def __str__(self):
        return f"{self.external_status} -> {self.internal_status}"
