from core.ip_utils import get_client_ip
from findings.models import AuditLog


def log_audit(request, action, target_type, target_id="", project=None, metadata=None):
    """Helper to create audit log entries."""
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        project=project,
        metadata=metadata or {},
        ip_address=get_client_ip(request),
    )
