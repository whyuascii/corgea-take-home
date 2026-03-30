import uuid
from django.db import models

from .rule import Rule


class Finding(models.Model):
    class Status(models.TextChoices):
        NEW = "new"
        OPEN = "open"
        RESOLVED = "resolved"
        REOPENED = "reopened"
        IGNORED = "ignored"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="findings"
    )
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name="findings")
    file_path = models.CharField(max_length=1000)
    line_start = models.IntegerField()
    line_end = models.IntegerField()
    code_snippet = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW
    )
    first_seen_scan = models.ForeignKey(
        "scans.Scan", on_delete=models.SET_NULL, null=True, related_name="new_findings"
    )
    last_seen_scan = models.ForeignKey(
        "scans.Scan", on_delete=models.SET_NULL, null=True, related_name="seen_findings",
    )
    is_false_positive = models.BooleanField(default=False)
    false_positive_reason = models.TextField(blank=True, default="")
    jira_ticket_id = models.CharField(max_length=100, blank=True, default="")
    jira_ticket_url = models.URLField(blank=True, default="")
    linear_ticket_id = models.CharField(max_length=100, blank=True, default="")
    linear_ticket_url = models.URLField(blank=True, default="")
    severity_override = models.CharField(max_length=20, blank=True, default="")
    pr_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "rule", "file_path", "line_start", "line_end")]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "rule"]),
            models.Index(fields=["jira_ticket_id"]),
            models.Index(fields=["linear_ticket_id"]),
            models.Index(fields=["is_false_positive"]),
            # Compound index for the common filter pattern in finding_list
            models.Index(
                fields=["project", "status", "is_false_positive"],
                name="finding_proj_status_fp_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rule.semgrep_rule_id} @ {self.file_path}:{self.line_start}"
