import secrets
import uuid

from django.conf import settings
from django.db import models


def generate_api_key():
    return secrets.token_urlsafe(48)


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True, default="")
    repository_url = models.URLField(blank=True, default="")
    api_key = models.CharField(max_length=64, default=generate_api_key, unique=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("owner", "slug")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
