import uuid

from django.conf import settings
from django.db import models


class ProjectMembership(models.Model):
    """Links a user to a project with a specific role."""

    class Role(models.TextChoices):
        VIEWER = "viewer"
        MEMBER = "member"
        ADMIN = "admin"
        OWNER = "owner"

    ROLE_HIERARCHY = {
        Role.VIEWER: 0,
        Role.MEMBER: 1,
        Role.ADMIN: 2,
        Role.OWNER: 3,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("project", "user")]
        ordering = ["role", "created_at"]

    def __str__(self):
        return f"{self.user} → {self.project} ({self.role})"

    @classmethod
    def has_role(cls, role, min_role):
        """Return True if *role* meets or exceeds *min_role* in the hierarchy."""
        return cls.ROLE_HIERARCHY.get(role, -1) >= cls.ROLE_HIERARCHY.get(min_role, 99)
