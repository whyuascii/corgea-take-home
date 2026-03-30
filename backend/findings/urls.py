from django.urls import path
from . import views

urlpatterns = [
    # Rules
    path("rules/", views.rule_list, name="rule-list"),
    path("rules/<uuid:rule_id>/", views.rule_update, name="rule-update"),

    # Findings
    path("", views.finding_list, name="finding-list"),
    path("<uuid:finding_id>/", views.finding_detail, name="finding-detail"),
    path("<uuid:finding_id>/history/", views.finding_history, name="finding-history"),
    path("<uuid:finding_id>/false-positive/", views.mark_false_positive, name="finding-false-positive"),
    path("<uuid:finding_id>/comments/", views.finding_comments, name="finding-comments"),
    path("<uuid:finding_id>/comments/<uuid:comment_id>/", views.finding_comment_delete, name="finding-comment-delete"),

    # Bulk operations
    path("bulk/", views.bulk_update_findings, name="finding-bulk-update"),

    # Analytics & export
    path("summary/", views.project_summary, name="project-summary"),
    path("trends/", views.finding_trends, name="finding-trends"),
    path("export/", views.finding_export, name="finding-export"),
    path("search/", views.finding_search, name="finding-search"),

    # Audit
    path("audit-log/", views.audit_log_list, name="audit-log"),
]
