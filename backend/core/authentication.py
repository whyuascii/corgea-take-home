from datetime import timedelta

from django.middleware.csrf import CsrfViewMiddleware
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from core.constants import TOKEN_LIFETIME_HOURS

AUTH_COOKIE_NAME = "auth_token"


class _CSRFCheck(CsrfViewMiddleware):
    """Shim that lets us run CSRF validation outside the middleware stack."""

    def _reject(self, request, reason):
        raise AuthenticationFailed(f"CSRF Failed: {reason}")


class ExpiringTokenAuthentication(TokenAuthentication):
    """Token auth with expiry, header support, and httpOnly cookie fallback."""

    def authenticate(self, request):
        # 1. Try header auth (standard DRF TokenAuthentication)
        result = super().authenticate(request)
        if result is not None:
            user, token = result
            self._check_expiry(token)
            return (user, token)

        # 2. Fallback: read from httpOnly cookie
        token_key = request.COOKIES.get(AUTH_COOKIE_NAME)
        if not token_key:
            return None

        user, token = self.authenticate_credentials(token_key)
        self._check_expiry(token)
        self._enforce_csrf(request)
        return (user, token)

    def _check_expiry(self, token):
        age = timezone.now() - token.created
        if age > timedelta(hours=TOKEN_LIFETIME_HOURS):
            token.delete()
            raise AuthenticationFailed("Token has expired.")

    @staticmethod
    def _enforce_csrf(request):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return
        check = _CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise AuthenticationFailed(f"CSRF Failed: {reason}")
