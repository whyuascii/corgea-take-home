from django.shortcuts import get_object_or_404

from projects.models import Project


def get_project_for_user(request, project_slug):
    """Return the project matching *project_slug* owned by the requesting user.

    Uses ``get_object_or_404`` so that a missing / inaccessible project returns
    a clean HTTP 404 instead of an unhandled 500.
    """
    return get_object_or_404(Project, slug=project_slug, owner=request.user)
