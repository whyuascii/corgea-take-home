from rest_framework.decorators import api_view

from core.pagination import paginate_queryset
from ..models import AuditLog
from ..serializers import AuditLogSerializer
from .helpers import get_project_for_user


@api_view(["GET"])
def audit_log_list(request, project_slug):
    """List audit log entries for a project, including scan uploads, status changes, and API key events."""
    project = get_project_for_user(request, project_slug)
    logs = AuditLog.objects.filter(project=project).select_related("user")
    return paginate_queryset(logs, request, AuditLogSerializer)
