import uuid
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models

from core.constants import MAX_COMMENT_LENGTH

from .finding import Finding


class FindingComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    text = models.TextField(validators=[MaxLengthValidator(MAX_COMMENT_LENGTH)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on {self.finding_id} by {self.user}"
