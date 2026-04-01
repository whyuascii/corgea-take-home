from core.ip_utils import get_client_ip
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle

class LoginThrottle(SimpleRateThrottle):
    """Throttle login attempts by IP + username."""

    scope = "login"

    def get_cache_key(self, request, view):
        ip = get_client_ip(request) or "unknown"
        username = request.data.get("username", "").strip().lower()
        ident = f"{ip}:{username}" if username else ip
        return self.cache_format % {"scope": self.scope, "ident": ident}


class RegistrationThrottle(AnonRateThrottle):
    scope = "registration"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"

class ScanUploadThrottle(UserRateThrottle):
    """Scan uploads trigger full ingestion — limit per user."""

    scope = "scan_upload"


class BulkOperationThrottle(UserRateThrottle):
    """Bulk updates touch up to 1000 rows — limit per user."""

    scope = "bulk_operation"


class ExportThrottle(UserRateThrottle):
    """CSV exports stream the full dataset — limit per user."""

    scope = "export"

class ApiKeyRotationThrottle(UserRateThrottle):
    """API key rotation is security-critical — very strict limit."""

    scope = "api_key_rotation"


class IntegrationTestThrottle(UserRateThrottle):
    """Integration tests make outbound API calls to Jira/Linear."""

    scope = "integration_test"


class WebhookThrottle(AnonRateThrottle):
    """Webhooks are public endpoints — throttle by IP to prevent abuse."""

    scope = "webhook"
