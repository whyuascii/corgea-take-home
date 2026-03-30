from .models import AuditLog


def log_audit(request, action, target_type, target_id="", project=None, metadata=None):
    """Helper to create audit log entries."""
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
    if not ip:
        ip = request.META.get("REMOTE_ADDR")

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        project=project,
        metadata=metadata or {},
        ip_address=ip,
    )
