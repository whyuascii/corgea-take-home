from django.urls import path

from . import views

# These are nested under /api/projects/<slug>/integrations/
urlpatterns = [
    path("", views.integration_list, name="integration-list"),
    path("<uuid:integration_id>/", views.integration_detail, name="integration-detail"),
    path("<uuid:integration_id>/test/", views.integration_test, name="integration-test"),
    path(
        "<uuid:integration_id>/mappings/",
        views.mapping_list,
        name="mapping-list",
    ),
    path(
        "<uuid:integration_id>/mappings/<uuid:mapping_id>/",
        views.mapping_detail,
        name="mapping-detail",
    ),
]
