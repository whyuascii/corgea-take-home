import uuid
from django.conf import settings
from django.db import models


class Scan(models.Model):
    class Source(models.TextChoices):
        UPLOAD = "upload"
        API = "api"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="scans"
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, choices=Source.choices)
    scanner_type = models.CharField(
        max_length=20,
        choices=[("semgrep", "Semgrep"), ("sarif", "SARIF"), ("generic", "Generic")],
        default="semgrep",
    )
    total_findings_count = models.IntegerField(default=0)
    new_count = models.IntegerField(default=0)
    resolved_count = models.IntegerField(default=0)
    reopened_count = models.IntegerField(default=0)
    commit_sha = models.CharField(max_length=40, blank=True, default="")
    branch = models.CharField(max_length=255, blank=True, default="")
    ci_provider = models.CharField(max_length=50, blank=True, default="")
    raw_report = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["project", "-created_at"],
                name="scan_proj_created_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Scan {self.id} ({self.project.name})"
