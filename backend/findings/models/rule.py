import uuid
from django.db import models


class Rule(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active"
        IGNORED = "ignored"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="rules"
    )
    semgrep_rule_id = models.CharField(max_length=500)
    severity = models.CharField(max_length=20)
    message = models.TextField(blank=True, default="")
    category = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "semgrep_rule_id")]
        indexes = [
            models.Index(
                fields=["project", "status"],
                name="rule_proj_status_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.semgrep_rule_id
