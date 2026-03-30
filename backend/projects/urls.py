from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("", views.ProjectViewSet, basename="project")

urlpatterns = [
    path("<slug:project_slug>/scans/", include("scans.urls")),
    path("<slug:project_slug>/findings/", include("findings.urls")),
    path("<slug:project_slug>/integrations/", include("integrations.urls")),
    path("", include(router.urls)),
]
