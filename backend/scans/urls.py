from django.urls import path
from . import views

urlpatterns = [
    path("", views.scan_list, name="scan-list"),
    path("upload/", views.scan_upload, name="scan-upload"),
    path("push/", views.scan_push, name="scan-push"),
    path("ci-snippets/", views.ci_snippets, name="ci-snippets"),
    path("latest/", views.scan_latest, name="scan-latest"),
    path("<uuid:scan_id>/", views.scan_detail, name="scan-detail"),
]
