import uuid
from django.core.validators import MaxLengthValidator
from django.db import models

from core.constants import MAX_REASON_LENGTH

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
    line_start = models.PositiveIntegerField(default=0)
    line_end = models.PositiveIntegerField(default=0)
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
    false_positive_reason = models.TextField(blank=True, default="", validators=[MaxLengthValidator(MAX_REASON_LENGTH)])
    jira_ticket_id = models.CharField(max_length=100, blank=True, default="")
    jira_ticket_url = models.URLField(blank=True, default="")
    linear_ticket_id = models.CharField(max_length=100, blank=True, default="")
    linear_ticket_url = models.URLField(blank=True, default="")
    severity_override = models.CharField(max_length=20, blank=True, default="")
    pr_url = models.URLField(blank=True, default="")
    sla_deadline = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "rule", "file_path", "line_start", "line_end")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(line_end__gte=models.F("line_start")),
                name="finding_line_end_gte_start",
            ),
        ]
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
            # Overview/ordering: paginated lists across projects sort by created_at
            models.Index(
                fields=["project", "-created_at"],
                name="finding_proj_created_idx",
            ),
            # Cross-project FP propagation in ingestion: rule FK + false_positive flag
            models.Index(
                fields=["rule", "is_false_positive"],
                name="finding_rule_fp_idx",
            ),
            models.Index(
                fields=["project", "sla_breached", "status"],
                name="finding_sla_breach_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rule.semgrep_rule_id} @ {self.file_path}:{self.line_start}"
