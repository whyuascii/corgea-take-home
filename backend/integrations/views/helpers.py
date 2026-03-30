from django.shortcuts import get_object_or_404

from projects.models import Project


def get_project_for_user(request, project_slug):
    return get_object_or_404(Project, slug=project_slug, owner=request.user)
