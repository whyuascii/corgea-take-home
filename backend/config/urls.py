from django.contrib import admin
from django.urls import include, path

from findings import views as findings_views
from integrations import views as webhook_views

urlpatterns = [
    # Auth
    path("api/auth/", include("accounts.urls")),

    # Projects (includes nested scans, findings, integrations)
    path("api/projects/", include("projects.urls")),

    # Cross-project overview (not project-scoped)
    path("api/overview/summary/", findings_views.overview_summary, name="overview-summary"),
    path("api/overview/rules/", findings_views.overview_rules, name="overview-rules"),
    path("api/overview/findings/", findings_views.overview_findings, name="overview-findings"),

    # Webhooks
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

    # Admin
    path("admin/", admin.site.urls),
]
