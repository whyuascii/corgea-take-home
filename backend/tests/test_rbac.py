import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from projects.membership import ProjectMembership
from projects.models import Project

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(username="owner", email="owner@example.com", password="ownerpass1234!")


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="adminuser", email="admin@example.com", password="adminpass1234!")


@pytest.fixture
def member_user(db):
    return User.objects.create_user(username="memberuser", email="member@example.com", password="memberpass1234!")


@pytest.fixture
def viewer_user(db):
    return User.objects.create_user(username="vieweruser", email="viewer@example.com", password="viewerpass1234!")


@pytest.fixture
def non_member(db):
    return User.objects.create_user(username="nonmember", email="nonmember@example.com", password="nonmemberpass1234!")


@pytest.fixture
def rbac_project(owner):
    project = Project.objects.create(
        owner=owner, name="RBAC Project", slug="rbac-project"
    )
    ProjectMembership.objects.create(
        project=project, user=owner, role=ProjectMembership.Role.OWNER
    )
    return project


@pytest.fixture
def setup_members(rbac_project, admin_user, member_user, viewer_user):
    ProjectMembership.objects.create(
        project=rbac_project, user=admin_user, role=ProjectMembership.Role.ADMIN
    )
    ProjectMembership.objects.create(
        project=rbac_project, user=member_user, role=ProjectMembership.Role.MEMBER
    )
    ProjectMembership.objects.create(
        project=rbac_project, user=viewer_user, role=ProjectMembership.Role.VIEWER
    )


def _client_for(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client

class TestProjectMembershipModel:
    def test_role_hierarchy(self):
        assert ProjectMembership.has_role("owner", "viewer")
        assert ProjectMembership.has_role("owner", "owner")
        assert ProjectMembership.has_role("admin", "member")
        assert not ProjectMembership.has_role("viewer", "member")
        assert not ProjectMembership.has_role("member", "admin")

    def test_unique_constraint(self, rbac_project, admin_user, setup_members):
        with pytest.raises(Exception):
            ProjectMembership.objects.create(
                project=rbac_project, user=admin_user, role=ProjectMembership.Role.MEMBER
            )

class TestMemberManagementAPI:
    def test_owner_can_list_members(self, owner, rbac_project, setup_members):
        client = _client_for(owner)
        resp = client.get(f"/api/projects/{rbac_project.slug}/members/")
        assert resp.status_code == 200
        assert len(resp.json()) == 4  # owner + admin + member + viewer

    def test_viewer_can_list_members(self, viewer_user, rbac_project, setup_members):
        client = _client_for(viewer_user)
        resp = client.get(f"/api/projects/{rbac_project.slug}/members/")
        assert resp.status_code == 200

    def test_non_member_cannot_list_members(self, non_member, rbac_project, setup_members):
        client = _client_for(non_member)
        resp = client.get(f"/api/projects/{rbac_project.slug}/members/")
        assert resp.status_code == 404

    def test_owner_can_add_member(self, owner, rbac_project, non_member):
        client = _client_for(owner)
        resp = client.post(
            f"/api/projects/{rbac_project.slug}/members/",
            {"user_id": non_member.pk, "role": "member"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "member"

    def test_non_owner_cannot_add_member(self, admin_user, rbac_project, setup_members, non_member):
        client = _client_for(admin_user)
        resp = client.post(
            f"/api/projects/{rbac_project.slug}/members/",
            {"user_id": non_member.pk, "role": "member"},
            format="json",
        )
        assert resp.status_code == 404  # RBAC denies, returns 404

    def test_cannot_add_another_owner(self, owner, rbac_project, non_member):
        client = _client_for(owner)
        resp = client.post(
            f"/api/projects/{rbac_project.slug}/members/",
            {"user_id": non_member.pk, "role": "owner"},
            format="json",
        )
        assert resp.status_code == 400

    def test_cannot_add_duplicate_member(self, owner, rbac_project, admin_user, setup_members):
        client = _client_for(owner)
        resp = client.post(
            f"/api/projects/{rbac_project.slug}/members/",
            {"user_id": admin_user.pk, "role": "member"},
            format="json",
        )
        assert resp.status_code == 409

    def test_owner_can_change_member_role(self, owner, rbac_project, member_user, setup_members):
        client = _client_for(owner)
        membership = ProjectMembership.objects.get(project=rbac_project, user=member_user)
        resp = client.patch(
            f"/api/projects/{rbac_project.slug}/members/{membership.id}/",
            {"role": "admin"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_cannot_change_owner_role(self, owner, rbac_project):
        client = _client_for(owner)
        membership = ProjectMembership.objects.get(project=rbac_project, user=owner)
        resp = client.patch(
            f"/api/projects/{rbac_project.slug}/members/{membership.id}/",
            {"role": "admin"},
            format="json",
        )
        assert resp.status_code == 400

    def test_owner_can_remove_member(self, owner, rbac_project, member_user, setup_members):
        client = _client_for(owner)
        membership = ProjectMembership.objects.get(project=rbac_project, user=member_user)
        resp = client.delete(f"/api/projects/{rbac_project.slug}/members/{membership.id}/")
        assert resp.status_code == 204
        assert not ProjectMembership.objects.filter(id=membership.id).exists()

    def test_cannot_remove_owner(self, owner, rbac_project):
        client = _client_for(owner)
        membership = ProjectMembership.objects.get(project=rbac_project, user=owner)
        resp = client.delete(f"/api/projects/{rbac_project.slug}/members/{membership.id}/")
        assert resp.status_code == 400

class TestRBACViewAccess:
    def test_viewer_can_read_findings(self, viewer_user, rbac_project, setup_members):
        client = _client_for(viewer_user)
        resp = client.get(f"/api/projects/{rbac_project.slug}/findings/")
        assert resp.status_code == 200

    def test_viewer_cannot_bulk_update(self, viewer_user, rbac_project, setup_members):
        client = _client_for(viewer_user)
        resp = client.post(
            f"/api/projects/{rbac_project.slug}/findings/bulk/",
            {"finding_ids": [], "action": "status_change", "status": "open"},
            format="json",
        )
        assert resp.status_code == 404

    def test_member_can_bulk_update(self, member_user, rbac_project, setup_members):
        client = _client_for(member_user)
        resp = client.post(
            f"/api/projects/{rbac_project.slug}/findings/bulk/",
            {"finding_ids": [], "action": "status_change", "status": "open"},
            format="json",
        )
        assert resp.status_code == 400

    def test_viewer_cannot_access_audit_log(self, viewer_user, rbac_project, setup_members):
        client = _client_for(viewer_user)
        resp = client.get(f"/api/projects/{rbac_project.slug}/findings/audit-log/")
        assert resp.status_code == 404

    def test_admin_can_access_audit_log(self, admin_user, rbac_project, setup_members):
        client = _client_for(admin_user)
        resp = client.get(f"/api/projects/{rbac_project.slug}/findings/audit-log/")
        assert resp.status_code == 200

    def test_non_member_cannot_access_project(self, non_member, rbac_project):
        client = _client_for(non_member)
        resp = client.get(f"/api/projects/{rbac_project.slug}/findings/")
        assert resp.status_code == 404
