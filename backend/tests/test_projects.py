import pytest
from rest_framework import status

from tests.conftest import get_results


@pytest.mark.django_db
class TestProjects:

    def test_list_projects(self, auth_client, project):
        resp = auth_client.get("/api/projects/")
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1
        slugs = [p["slug"] for p in results]
        assert project.slug in slugs

    def test_create_project(self, auth_client):
        resp = auth_client.post("/api/projects/", {
            "name": "New Project",
            "description": "A brand new project",
            "repository_url": "https://github.com/example/new",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "New Project"
        assert data["slug"] == "new-project"
        assert "api_key" in data

    def test_get_project(self, auth_client, project):
        resp = auth_client.get(f"/api/projects/{project.slug}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["slug"] == project.slug
        assert data["name"] == project.name
        assert "findings_summary" in data

    def test_update_project(self, auth_client, project):
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/",
            {"description": "Updated description"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["description"] == "Updated description"

    def test_delete_project(self, auth_client, project):
        resp = auth_client.delete(f"/api/projects/{project.slug}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_regenerate_api_key(self, auth_client, project):
        old_api_key = project.api_key
        resp = auth_client.post(
            f"/api/projects/{project.slug}/regenerate_api_key/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "api_key" in data
        assert data["api_key"] != old_api_key

    def test_other_user_cannot_see_project(self, other_auth_client, project):
        resp = other_auth_client.get(f"/api/projects/{project.slug}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
