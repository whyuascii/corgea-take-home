from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from core.audit import log_audit
from core.pagination import paginate_queryset
from projects.membership import ProjectMembership
from ..models import AuditLog, Finding, FindingComment
from ..serializers import FindingCommentSerializer
from projects.permissions import get_project_for_user


@extend_schema(tags=["Findings"], responses=FindingCommentSerializer)
@api_view(["GET", "POST"])
def finding_comments(request, project_slug, finding_id):
    """List or create comments on a finding. POST requires a 'text' field."""
    min_role = ProjectMembership.Role.MEMBER if request.method == "POST" else ProjectMembership.Role.VIEWER
    project = get_project_for_user(request, project_slug, min_role=min_role)
    finding = get_object_or_404(Finding, id=finding_id, project=project)

    if request.method == "POST":
        serializer = FindingCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(finding=finding, user=request.user)
        log_audit(
            request, AuditLog.Action.COMMENT_CREATED, "comment", comment.id,
            project, {"finding_id": str(finding_id)},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    comments = FindingComment.objects.filter(finding=finding).select_related("user")
    return paginate_queryset(comments, request, FindingCommentSerializer, page_size=50)


@extend_schema(tags=["Findings"])
@api_view(["DELETE"])
def finding_comment_delete(request, project_slug, finding_id, comment_id):
    """Delete a comment. Only the comment author may delete their own comments."""
    project = get_project_for_user(request, project_slug, min_role=ProjectMembership.Role.MEMBER)
    comment = get_object_or_404(
        FindingComment,
        id=comment_id,
        finding__id=finding_id,
        finding__project=project,
    )
    if comment.user != request.user:
        return Response(
            {"error": "Can only delete your own comments"},
            status=status.HTTP_403_FORBIDDEN,
        )
    log_audit(
        request, AuditLog.Action.COMMENT_DELETED, "comment", comment.id,
        project, {"finding_id": str(finding_id), "comment_id": str(comment_id)},
    )
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
