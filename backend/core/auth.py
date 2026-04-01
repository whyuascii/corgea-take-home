from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


class TokenAuthMiddleware(BaseMiddleware):
    """Authenticate WebSocket connections using DRF Token from query params."""

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope.get("query_string", b"").decode())
        token_key = query_string.get("token", [None])[0]
        if token_key:
            scope["user"] = await self._get_user(token_key)
        else:
            scope["user"] = AnonymousUser()

        scope["query_string"] = b""
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _get_user(self, token_key):
        from rest_framework.authtoken.models import Token

        try:
            return Token.objects.select_related("user").get(key=token_key).user
        except Token.DoesNotExist:
            return AnonymousUser()
