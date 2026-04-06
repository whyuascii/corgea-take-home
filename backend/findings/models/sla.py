import uuid

from django.db import models


class SLAPolicy(models.Model):
    """Defines maximum resolution time per severity level per project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="sla_policies"
    )
    severity = models.CharField(
        max_length=20,
        choices=[("ERROR", "Error"), ("WARNING", "Warning"), ("INFO", "Info")],
    )
    max_resolution_hours = models.PositiveIntegerField(
        help_text="Maximum hours allowed to resolve findings of this severity."
    )
    notification_threshold_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Hours before deadline to send a warning notification.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "severity")]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(notification_threshold_hours__isnull=True)
                    | models.Q(notification_threshold_hours__lt=models.F("max_resolution_hours"))
                ),
                name="sla_notification_lt_deadline",
            ),
        ]
        ordering = ["severity"]

    def __str__(self):
        return f"SLA {self.project.name}: {self.severity} <= {self.max_resolution_hours}h"
