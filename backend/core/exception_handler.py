import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler that adds request_id and hides internals."""
    response = exception_handler(exc, context)

    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request else None

    if response is not None:
        if request_id:
            response.data["request_id"] = request_id
    else:
        # Unhandled exception (5xx) — log and always return a generic message.
        # In DEBUG mode Django's default handler would expose tracebacks, so
        # we intercept here to ensure a consistent JSON response.
        logger.exception(
            "Unhandled exception [request_id=%s]: %s",
            request_id, exc,
        )
        data = {"error": "An internal error occurred."}
        if request_id:
            data["request_id"] = request_id
        response = Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
