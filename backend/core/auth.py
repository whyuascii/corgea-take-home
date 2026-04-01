import http.cookies
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

from core.authentication import AUTH_COOKIE_NAME
from core.constants import TOKEN_LIFETIME_HOURS


class TokenAuthMiddleware(BaseMiddleware):
    """Authenticate WebSocket connections via httpOnly cookie."""

    async def __call__(self, scope, receive, send):
        token_key = self._get_token_from_cookie(scope)

        if token_key:
            scope["user"] = await self._get_user(token_key)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @staticmethod
    def _get_token_from_cookie(scope):
        """Extract auth_token from the Cookie header."""
        for name, value in scope.get("headers", []):
            if name == b"cookie":
                cookie = http.cookies.SimpleCookie()
                cookie.load(value.decode("latin-1"))
                morsel = cookie.get(AUTH_COOKIE_NAME)
                if morsel:
                    return morsel.value
        return None

    @database_sync_to_async
    def _get_user(self, token_key):
        from django.utils import timezone
        from rest_framework.authtoken.models import Token

        try:
            token = Token.objects.select_related("user").get(key=token_key)
        except Token.DoesNotExist:
            return AnonymousUser()

        age = timezone.now() - token.created
        if age > timedelta(hours=TOKEN_LIFETIME_HOURS):
            token.delete()
            return AnonymousUser()

        return token.user
