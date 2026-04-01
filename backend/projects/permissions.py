from django.http import Http404
from rest_framework.permissions import BasePermission

from .membership import ProjectMembership
from .models import Project


def get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.VIEWER):
    """Return the project if the requesting user has at least *min_role*."""
    try:
        project = Project.objects.filter(
            memberships__user=request.user,
            slug=project_slug,
        ).distinct().get()
    except (Project.DoesNotExist, Project.MultipleObjectsReturned):
        raise Http404

    membership = ProjectMembership.objects.filter(
        project=project, user=request.user
    ).first()

    if membership is None:
        raise Http404

    if not ProjectMembership.has_role(membership.role, min_role):
        raise Http404

    return project


class HasProjectRole(BasePermission):
    """DRF permission for ViewSet-based views that operate on a Project."""

    def has_object_permission(self, request, view, obj):
        min_role = getattr(view, "min_role", ProjectMembership.Role.VIEWER)
        membership = ProjectMembership.objects.filter(
            project=obj, user=request.user
        ).first()

        if membership is None:
            return False

        return ProjectMembership.has_role(membership.role, min_role)
