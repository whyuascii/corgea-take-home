from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import member_views, views

router = DefaultRouter()
router.register("", views.ProjectViewSet, basename="project")

urlpatterns = [
    path("<slug:project_slug>/scans/", include("scans.urls")),
    path("<slug:project_slug>/findings/", include("findings.urls")),
    path("<slug:project_slug>/integrations/", include("integrations.urls")),
    path("<slug:slug>/members/", member_views.member_list, name="project-members"),
    path(
        "<slug:slug>/members/<uuid:membership_id>/",
        member_views.member_detail,
        name="project-member-detail",
    ),
    path("", include(router.urls)),
]
