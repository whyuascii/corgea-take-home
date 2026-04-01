from django.db import DatabaseError, connection
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from findings import views as findings_views
from integrations import views as webhook_views


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint that verifies database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except DatabaseError:
        db_status = "unavailable"

    healthy = db_status == "ok"
    return Response(
        {"status": "ok" if healthy else "degraded", "database": db_status},
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/auth/", include("accounts.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/overview/summary/", findings_views.overview_summary, name="overview-summary"),
    path("api/overview/rules/", findings_views.overview_rules, name="overview-rules"),
    path("api/overview/findings/", findings_views.overview_findings, name="overview-findings"),
    path(
        "api/webhooks/jira/<str:webhook_secret>/",
        webhook_views.jira_webhook,
        name="jira-webhook",
    ),
    path(
        "api/webhooks/linear/<str:webhook_secret>/",
        webhook_views.linear_webhook,
        name="linear-webhook",
    ),
]
