from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import LoginAttempt, PasswordResetToken

User = get_user_model()


@pytest.fixture
def pw_user(db):
    return User.objects.create_user(
        username="pwuser", email="pw@example.com", password="OldPassword123!"
    )


@pytest.fixture
def anon_client():
    return APIClient()

@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Clear the throttle cache before each test so rate limits don't bleed across tests."""
    cache.clear()


class TestForgotPassword:
    def test_returns_200_for_existing_email(self, anon_client, pw_user):
        resp = anon_client.post(
            "/api/auth/forgot-password/", {"email": "pw@example.com"}, format="json"
        )
        assert resp.status_code == 200
        assert PasswordResetToken.objects.filter(user=pw_user).exists()

    def test_returns_200_for_nonexistent_email(self, anon_client, db):
        resp = anon_client.post(
            "/api/auth/forgot-password/", {"email": "noone@example.com"}, format="json"
        )
        assert resp.status_code == 200  # Prevents user enumeration

    def test_invalidates_previous_tokens(self, anon_client, pw_user):
        anon_client.post(
            "/api/auth/forgot-password/", {"email": "pw@example.com"}, format="json"
        )
        first_token = PasswordResetToken.objects.filter(user=pw_user, used_at__isnull=True).first()
        assert first_token is not None

        anon_client.post(
            "/api/auth/forgot-password/", {"email": "pw@example.com"}, format="json"
        )
        first_token.refresh_from_db()
        assert first_token.used_at is not None

    def test_missing_email_returns_400(self, anon_client, db):
        resp = anon_client.post("/api/auth/forgot-password/", {}, format="json")
        assert resp.status_code == 400


class TestResetPassword:
    def test_successful_reset(self, anon_client, pw_user):
        token = PasswordResetToken.objects.create(user=pw_user)
        resp = anon_client.post(
            "/api/auth/reset-password/",
            {"token": token.token, "password": "NewSecurePass456!"},
            format="json",
        )
        assert resp.status_code == 200
        pw_user.refresh_from_db()
        assert pw_user.check_password("NewSecurePass456!")

    def test_invalidates_all_sessions(self, anon_client, pw_user):
        # Create a session token first
        Token.objects.create(user=pw_user)
        assert Token.objects.filter(user=pw_user).count() == 1

        token = PasswordResetToken.objects.create(user=pw_user)
        anon_client.post(
            "/api/auth/reset-password/",
            {"token": token.token, "password": "NewSecurePass456!"},
            format="json",
        )
        assert Token.objects.filter(user=pw_user).count() == 0

    def test_expired_token_fails(self, anon_client, pw_user):
        token = PasswordResetToken.objects.create(
            user=pw_user, expires_at=timezone.now() - timedelta(hours=1)
        )
        resp = anon_client.post(
            "/api/auth/reset-password/",
            {"token": token.token, "password": "NewSecurePass456!"},
            format="json",
        )
        assert resp.status_code == 400

    def test_used_token_fails(self, anon_client, pw_user):
        token = PasswordResetToken.objects.create(user=pw_user, used_at=timezone.now())
        resp = anon_client.post(
            "/api/auth/reset-password/",
            {"token": token.token, "password": "NewSecurePass456!"},
            format="json",
        )
        assert resp.status_code == 400

    def test_invalid_token_fails(self, anon_client, db):
        resp = anon_client.post(
            "/api/auth/reset-password/",
            {"token": "nonexistent-token", "password": "NewSecurePass456!"},
            format="json",
        )
        assert resp.status_code == 400

    def test_weak_password_rejected(self, anon_client, pw_user):
        token = PasswordResetToken.objects.create(user=pw_user)
        resp = anon_client.post(
            "/api/auth/reset-password/",
            {"token": token.token, "password": "123"},
            format="json",
        )
        assert resp.status_code == 400


class TestLoginRateLimiting:
    def test_lockout_after_5_failures(self, anon_client, pw_user):
        for _ in range(5):
            anon_client.post(
                "/api/auth/login/",
                {"username": "pwuser", "password": "wrongpassword"},
                format="json",
            )

        resp = anon_client.post(
            "/api/auth/login/",
            {"username": "pwuser", "password": "OldPassword123!"},
            format="json",
        )
        assert resp.status_code == 429

    def test_successful_login_still_allowed_before_lockout(self, anon_client, pw_user):
        for _ in range(4):
            anon_client.post(
                "/api/auth/login/",
                {"username": "pwuser", "password": "wrongpassword"},
                format="json",
            )

        resp = anon_client.post(
            "/api/auth/login/",
            {"username": "pwuser", "password": "OldPassword123!"},
            format="json",
        )
        assert resp.status_code == 200

    def test_login_attempts_recorded(self, anon_client, pw_user):
        anon_client.post(
            "/api/auth/login/",
            {"username": "pwuser", "password": "wrongpassword"},
            format="json",
        )
        assert LoginAttempt.objects.filter(username="pwuser", success=False).count() == 1

        anon_client.post(
            "/api/auth/login/",
            {"username": "pwuser", "password": "OldPassword123!"},
            format="json",
        )
        assert LoginAttempt.objects.filter(username="pwuser", success=True).count() == 1
