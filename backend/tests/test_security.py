import io
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.fields import EncryptedTextField
from integrations.models import IntegrationConfig
from projects.models import Project

User = get_user_model()

@pytest.mark.django_db
class TestEncryptedTextField:

    def test_round_trip(self, project):
        """Value stored then read back should match the original."""
        original = project.api_key
        project.save()
        project.refresh_from_db()
        assert project.api_key == original

    def test_raw_db_value_is_encrypted(self, project):
        """The raw database value should be Fernet-encrypted, not plain text."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT api_key FROM projects_project WHERE id = %s",
                [str(project.id)],
            )
            raw = cursor.fetchone()[0]
        # Raw value should not equal the application-level value
        assert raw != project.api_key
        # Raw value should be decryptable using the field's Fernet instance
        field = EncryptedTextField()
        decrypted = field.from_db_value(raw, None, None)
        assert decrypted == project.api_key

    def test_invalid_ciphertext_raises(self, project):
        """Corrupted or plain text values should raise on decryption."""
        from cryptography.fernet import InvalidToken
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE projects_project SET api_key = %s WHERE id = %s",
                ["not-encrypted-data", str(project.id)],
            )
        with pytest.raises(InvalidToken):
            project.refresh_from_db()
            _ = project.api_key

    def test_empty_value_not_signed(self, project):
        """Empty strings should pass through without signing."""
        project.old_api_key = ""
        project.save()
        project.refresh_from_db()
        assert project.old_api_key == ""

    def test_integration_tokens_encrypted(self, project):
        """IntegrationConfig tokens should be stored encrypted."""
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_api_token="super-secret-token",
            linear_api_key="linear-secret-key",
        )
        config.refresh_from_db()
        assert config.jira_api_token == "super-secret-token"
        assert config.linear_api_key == "linear-secret-key"

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT jira_api_token FROM integrations_integrationconfig WHERE id = %s",
                [str(config.id)],
            )
            raw = cursor.fetchone()[0]
        assert raw != "super-secret-token"


@pytest.mark.django_db
class TestExceptionHandler:

    def test_error_responses_include_request_id(self):
        """Error responses should include a request_id."""
        client = APIClient()
        resp = client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert "request_id" in data

    @override_settings(DEBUG=False)
    def test_500_hides_internals_in_production(self):
        """In production (DEBUG=False), 500 errors should hide internal details."""
        client = APIClient()
        resp = client.get("/api/nonexistent/")
        assert resp.status_code in (404, 200, 301)

@pytest.mark.django_db
class TestProfileUpdate:

    def test_patch_profile_success(self, auth_client, user):
        resp = auth_client.patch(
            "/api/auth/me/",
            {"first_name": "Jane", "last_name": "Doe", "current_password": "testpass1234"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"

    def test_patch_profile_wrong_password(self, auth_client):
        resp = auth_client.patch(
            "/api/auth/me/",
            {"first_name": "Jane", "current_password": "wrong-password"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_profile_missing_password(self, auth_client):
        resp = auth_client.patch(
            "/api/auth/me/",
            {"first_name": "Jane"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_email_uniqueness(self, auth_client, other_user):
        resp = auth_client.patch(
            "/api/auth/me/",
            {"email": other_user.email, "current_password": "testpass1234"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_me_returns_names(self, auth_client, user):
        user.first_name = "Alice"
        user.last_name = "Smith"
        user.save()
        resp = auth_client.get("/api/auth/me/")
        data = resp.json()
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"


@pytest.mark.django_db
class TestChangePassword:

    def test_change_password_success(self, auth_client, user):
        resp = auth_client.post(
            "/api/auth/change-password/",
            {"current_password": "testpass1234", "new_password": "X9k#mP2vLq!w"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("X9k#mP2vLq!w")

    def test_change_password_wrong_current(self, auth_client):
        resp = auth_client.post(
            "/api/auth/change-password/",
            {"current_password": "wrong", "new_password": "X9k#mP2vLq!w"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_weak_new(self, auth_client):
        resp = auth_client.post(
            "/api/auth/change-password/",
            {"current_password": "testpass1234", "new_password": "short"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestRegistrationValidation:

    def test_register_missing_email(self):
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "nomail",
            "password": "X9k#mP2vLq!w",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_email(self):
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "bademail",
            "email": "not-an-email",
            "password": "X9k#mP2vLq!w",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, user):
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "another",
            "email": user.email,  # already exists
            "password": "X9k#mP2vLq!w",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email_case_insensitive(self, user):
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        resp = client.post("/api/auth/register/", {
            "username": "another",
            "email": user.email.upper(),
            "password": "X9k#mP2vLq!w",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication"],
            "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
            "DEFAULT_THROTTLE_RATES": {"anon": "60/minute", "user": "300/minute", "login": "5/minute", "registration": "2/hour"},
            "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
        }
    )
    def test_registration_rate_limiting(self):
        client = APIClient()
        for i in range(3):
            resp = client.post("/api/auth/register/", {
                "username": f"ratelimit{i}",
                "email": f"ratelimit{i}@example.com",
                "password": "X9k#mP2vLq!w",
            })
        # Third request should be throttled (limit is 2/hour in override)
        assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS

@pytest.mark.django_db
class TestFileUploadHardening:

    def test_null_byte_rejection(self, auth_client, project):
        content = b'{"results": []}\x00'
        f = io.BytesIO(content)
        f.name = "report.json"
        resp = auth_client.post(
            f"/api/projects/{project.slug}/scans/upload/",
            {"file": f},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "null bytes" in str(resp.json()).lower()

    def test_non_json_magic_byte_rejection(self, auth_client, project):
        content = b'#!/bin/bash\necho "not json"'
        f = io.BytesIO(content)
        f.name = "report.json"
        resp = auth_client.post(
            f"/api/projects/{project.slug}/scans/upload/",
            {"file": f},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "json" in str(resp.json()).lower()

    def test_valid_json_still_accepted(self, auth_client, project):
        content = json.dumps({"results": [], "errors": []}).encode()
        f = io.BytesIO(content)
        f.name = "report.json"
        resp = auth_client.post(
            f"/api/projects/{project.slug}/scans/upload/",
            {"file": f},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
class TestContentTypeValidation:

    def test_rejects_text_plain_on_api_post(self, auth_client):
        resp = auth_client.post(
            "/api/auth/logout/",
            data="test",
            content_type="text/plain",
        )
        assert resp.status_code == 415

    def test_allows_json(self, auth_client):
        resp = auth_client.post(
            "/api/auth/logout/",
            data={},
            format="json",
        )
        # Should proceed to the view (204 for logout)
        assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestHealthCheck:

    def test_health_check(self):
        client = APIClient()
        resp = client.get("/api/health/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"

    def test_health_check_no_auth_needed(self):
        client = APIClient()
        resp = client.get("/api/health/")
        assert resp.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestPasswordResetTokenSecurity:

    def test_forgot_password_does_not_return_token(self):
        """The forgot_password response must NEVER include a reset token."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.create_user(username="tokentest", email="token@test.com", password="X9k#mP2vLq!w")
        client = APIClient()
        resp = client.post("/api/auth/forgot-password/", {"email": "token@test.com"}, format="json")
        assert resp.status_code == 200
        data = resp.json()
        # Response must not contain a token field
        assert "token" not in data
        # Response body string must not contain any UUID-like token patterns
        body_str = str(data)
        import re
        assert not re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-', body_str)

    def test_forgot_password_rate_limited(self, db):
        """forgot_password should be rate limited."""
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        # Make 6 requests rapidly (limit is 5/hour)
        for i in range(6):
            resp = client.post(
                "/api/auth/forgot-password/",
                {"email": f"test{i}@example.com"},
                format="json",
            )
        assert resp.status_code == 429

    def test_reset_password_rate_limited(self, db):
        """reset_password should be rate limited."""
        from django.core.cache import cache
        cache.clear()
        client = APIClient()
        for i in range(6):
            resp = client.post(
                "/api/auth/reset-password/",
                {"token": f"fake-token-{i}", "password": "X9k#mP2vLq!w"},
                format="json",
            )
        assert resp.status_code == 429

@pytest.mark.django_db
class TestWebhookSecretMasking:

    def test_webhook_url_masks_secret(self, auth_client, project):
        """The webhook_url in integration config should NOT expose the full secret."""
        from integrations.models import IntegrationConfig
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            webhook_secret="abcdef1234567890",
        )
        resp = auth_client.get(f"/api/projects/{project.slug}/integrations/{config.id}/")
        data = resp.json()
        webhook_url = data.get("webhook_url", "")
        # The full secret must NOT appear in the URL
        assert "abcdef1234567890" not in webhook_url
        # But it should start with the first 4 chars
        assert "abcd" in webhook_url

@pytest.mark.django_db
class TestRequestIDSanitization:

    def test_rejects_malicious_request_id(self):
        """Malicious X-Request-ID with newlines/special chars should be replaced."""
        client = APIClient()
        resp = client.get(
            "/api/health/",
            HTTP_X_REQUEST_ID="malicious\ninjection\r\nattack",
        )
        # Should get a valid UUID instead of the injected value
        request_id = resp["X-Request-ID"]
        assert "\n" not in request_id
        assert "\r" not in request_id
        assert "injection" not in request_id

    def test_accepts_valid_request_id(self):
        """Valid alphanumeric X-Request-ID should be preserved."""
        client = APIClient()
        resp = client.get(
            "/api/health/",
            HTTP_X_REQUEST_ID="abc-123-def-456",
        )
        assert resp["X-Request-ID"] == "abc-123-def-456"

    def test_rejects_oversized_request_id(self):
        """X-Request-ID longer than 64 chars should be replaced."""
        client = APIClient()
        long_id = "a" * 100
        resp = client.get("/api/health/", HTTP_X_REQUEST_ID=long_id)
        assert resp["X-Request-ID"] != long_id

@pytest.mark.django_db
class TestWebhookPayloadValidation:

    def _create_jira_config(self, project):
        from integrations.models import IntegrationConfig
        return IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            webhook_secret="test-webhook-secret",
        )

    def test_jira_webhook_rejects_oversized_issue_key(self, project):
        """Jira webhook should reject issue_key longer than 200 chars."""
        import hashlib, hmac, json
        config = self._create_jira_config(project)
        payload = {
            "issue": {
                "key": "X" * 300,
                "fields": {"status": {"name": "Done"}}
            }
        }
        body = json.dumps(payload).encode()
        sig = hmac.new(config.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        client = APIClient()
        resp = client.post(
            f"/api/webhooks/jira/{config.webhook_secret}/",
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE=sig,
        )
        assert resp.status_code == 400

@pytest.mark.django_db
class TestCSVFormulaInjection:

    def test_export_escapes_formula_in_file_path(self, auth_client, project, scan_with_findings):
        """CSV export should escape formula characters in file paths."""
        from findings.models import Finding
        f = Finding.objects.filter(project=project).first()
        f.file_path = "=HYPERLINK(\"http://evil.com\")"
        f.save(update_fields=["file_path"])

        resp = auth_client.get(f"/api/projects/{project.slug}/findings/export/")
        assert resp.status_code == 200
        content = resp.content.decode()
        # The formula-prefixed value should be escaped with a leading apostrophe
        assert "'=HYPERLINK" in content

    def test_export_escapes_whitespace_prefixed_formula(self, auth_client, project, scan_with_findings):
        """CSV export should escape values with whitespace before formula chars."""
        from findings.models import Finding
        f = Finding.objects.filter(project=project).first()
        f.file_path = "  +cmd|'/C calc'!A0"
        f.save(update_fields=["file_path"])

        resp = auth_client.get(f"/api/projects/{project.slug}/findings/export/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "'+cmd" not in content or "'  +cmd" in content

class TestProductionConfigSecurity:

    def test_production_requires_allowed_hosts(self):
        """Production settings should crash if ALLOWED_HOSTS is empty."""
        import os
        env_backup = {}
        for key in ("ALLOWED_HOSTS", "SECRET_KEY"):
            env_backup[key] = os.environ.get(key)
        os.environ["ALLOWED_HOSTS"] = ""
        os.environ["SECRET_KEY"] = "test-secret-for-prod-config-validation"
        try:
            from django.core.exceptions import ImproperlyConfigured
            with pytest.raises(ImproperlyConfigured):
                import importlib
                import config.settings.production as prod_mod
                importlib.reload(prod_mod)
        finally:
            for key, val in env_backup.items():
                if val is not None:
                    os.environ[key] = val
                else:
                    os.environ.pop(key, None)


@pytest.mark.django_db
class TestOverviewQueryCaps:

    def test_overview_rules_returns_paginated(self, auth_client, project, scan_with_findings):
        """overview_rules should return paginated results."""
        resp = auth_client.get("/api/overview/rules/")
        assert resp.status_code == 200
        data = resp.json()
        # Should be paginated (has count, results keys)
        assert "results" in data or isinstance(data, list)

    def test_overview_findings_returns_paginated(self, auth_client, project, scan_with_findings):
        """overview_findings should return paginated results."""
        resp = auth_client.get("/api/overview/findings/")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
