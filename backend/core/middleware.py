import re
import uuid


_VALID_REQUEST_ID = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")

# User-Agent patterns for known AI/scraper bots we want to block.
_BOT_PATTERNS = re.compile(
    r"(GPTBot|CCBot|anthropic-ai|ClaudeBot|Google-Extended|FacebookBot|Bytespider|PetalBot)",
    re.IGNORECASE,
)


class RequestIDMiddleware:
    """Assign a unique X-Request-ID to every response for tracing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_id = request.META.get("HTTP_X_REQUEST_ID", "")
        if client_id and _VALID_REQUEST_ID.match(client_id):
            request_id = client_id
        else:
            request_id = str(uuid.uuid4())
        request.request_id = request_id
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class BotProtectionMiddleware:
    """Block known AI/scraper bots before any processing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ua = request.META.get("HTTP_USER_AGENT", "")
        if _BOT_PATTERNS.search(ua):
            from django.http import HttpResponse
            return HttpResponse("Forbidden", status=403, content_type="text/plain")
        return self.get_response(request)


class ContentTypeValidationMiddleware:
    """Reject non-JSON/multipart Content-Type on mutating API requests."""

    MUTATING_METHODS = frozenset(("POST", "PUT", "PATCH"))
    ALLOWED_TYPES = ("application/json", "multipart/form-data")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method in self.MUTATING_METHODS
            and request.path.startswith("/api/")
            and request.content_type
            and not any(
                request.content_type.startswith(t) for t in self.ALLOWED_TYPES
            )
        ):
            from django.http import JsonResponse
            return JsonResponse(
                {"error": "Unsupported Content-Type. Use application/json or multipart/form-data."},
                status=415,
            )
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Stamp security headers on every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        return response
