import uuid
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models

from core.constants import MAX_NOTES_LENGTH

from .finding import Finding


class FindingHistory(models.Model):
    class ChangeType(models.TextChoices):
        STATUS_CHANGE = "status_change"
        FALSE_POSITIVE = "false_positive"
        TICKET_CREATED = "ticket_created"
        TICKET_CLOSED = "ticket_closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    finding = models.ForeignKey(
        Finding, on_delete=models.CASCADE, related_name="history"
    )
    scan = models.ForeignKey(
        "scans.Scan", on_delete=models.SET_NULL, null=True, blank=True
    )
    change_type = models.CharField(
        max_length=20, choices=ChangeType.choices, default=ChangeType.STATUS_CHANGE
    )
    old_status = models.CharField(max_length=20, blank=True, default="")
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    jira_ticket_url = models.URLField(blank=True, default="")
    linear_ticket_url = models.URLField(blank=True, default="")
    pr_url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True, default="", validators=[MaxLengthValidator(MAX_NOTES_LENGTH)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["finding", "-created_at"],
                name="fh_finding_created_idx",
            ),
            # finding_trends() aggregates resolved history by date
            models.Index(
                fields=["new_status", "created_at"],
                name="fh_status_created_idx",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.finding} : {self.old_status} -> {self.new_status}"
