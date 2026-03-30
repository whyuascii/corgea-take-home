import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAuth:

    def test_register(self):
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "new@example.com"

    def test_login(self, user):
        client = APIClient()
        resp = client.post("/api/auth/login/", {
            "username": "testuser",
            "password": "testpass1234",
        })
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "token" in data
        assert data["user"]["username"] == "testuser"

    def test_logout(self, auth_client):
        resp = auth_client.post("/api/auth/logout/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_me(self, auth_client, user):
        resp = auth_client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["username"] == user.username
        assert data["email"] == user.email

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        resp = client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
