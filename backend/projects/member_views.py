from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from core.audit import log_audit
from findings.models import AuditLog

from .member_serializers import ProjectMembershipSerializer
from .membership import ProjectMembership
from .permissions import get_project_for_user

User = get_user_model()


@extend_schema(tags=["Projects"], responses=ProjectMembershipSerializer)
@api_view(["GET", "POST"])
def member_list(request, slug):
    """List project members or add a new member (owner-only for POST)."""
    if request.method == "POST":
        project = get_project_for_user(
            request, slug, min_role=ProjectMembership.Role.OWNER
        )
    else:
        project = get_project_for_user(
            request, slug, min_role=ProjectMembership.Role.VIEWER
        )

    if request.method == "GET":
        memberships = ProjectMembership.objects.filter(project=project).select_related("user")
        serializer = ProjectMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    serializer = ProjectMembershipSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_id = serializer.validated_data.get("user_id")
    if not user_id:
        return Response(
            {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return Response(
            {"error": "Invalid user_id."}, status=status.HTTP_400_BAD_REQUEST
        )

    role = serializer.validated_data.get("role", ProjectMembership.Role.MEMBER)
    if role == ProjectMembership.Role.OWNER:
        return Response(
            {"error": "Cannot add another owner. Transfer ownership instead."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        membership, created = ProjectMembership.objects.get_or_create(
            project=project, user=user,
            defaults={"role": role},
        )
    except IntegrityError:
        return Response(
            {"error": "User is already a member of this project."},
            status=status.HTTP_409_CONFLICT,
        )
    if not created:
        return Response(
            {"error": "User is already a member of this project."},
            status=status.HTTP_409_CONFLICT,
        )
    log_audit(
        request, AuditLog.Action.MEMBER_ADDED, "membership", membership.id, project,
        {"member_username": user.username, "role": role},
    )
    return Response(
        ProjectMembershipSerializer(membership).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(tags=["Projects"], responses=ProjectMembershipSerializer)
@api_view(["PATCH", "DELETE"])
def member_detail(request, slug, membership_id):
    """Update a member's role or remove a member (owner-only)."""
    project = get_project_for_user(
        request, slug, min_role=ProjectMembership.Role.OWNER
    )
    membership = get_object_or_404(
        ProjectMembership, id=membership_id, project=project
    )

    if request.method == "DELETE":
        if membership.role == ProjectMembership.Role.OWNER:
            return Response(
                {"error": "Cannot remove the project owner."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log_audit(
            request, AuditLog.Action.MEMBER_REMOVED, "membership", membership.id, project,
            {"member_username": membership.user.username},
        )
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    new_role = request.data.get("role")
    if new_role not in [r[0] for r in ProjectMembership.Role.choices]:
        return Response(
            {"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST
        )
    if new_role == ProjectMembership.Role.OWNER:
        return Response(
            {"error": "Cannot assign owner role. Transfer ownership instead."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if membership.role == ProjectMembership.Role.OWNER:
        return Response(
            {"error": "Cannot change the owner's role."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_role = membership.role
    membership.role = new_role
    membership.save(update_fields=["role", "updated_at"])
    log_audit(
        request, AuditLog.Action.MEMBER_ROLE_CHANGED, "membership", membership.id, project,
        {"member_username": membership.user.username, "old_role": old_role, "new_role": new_role},
    )
    return Response(ProjectMembershipSerializer(membership).data)
