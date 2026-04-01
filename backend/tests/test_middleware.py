import pytest
from rest_framework.test import APIClient


@pytest.fixture
def anon_client():
    return APIClient()


class TestRequestIDMiddleware:
    def test_response_has_request_id(self, anon_client):
        resp = anon_client.get("/api/auth/login/")
        assert "X-Request-ID" in resp

    def test_preserves_client_request_id(self, anon_client):
        resp = anon_client.get(
            "/api/auth/login/", HTTP_X_REQUEST_ID="test-trace-id-123"
        )
        assert resp["X-Request-ID"] == "test-trace-id-123"


class TestBotProtectionMiddleware:
    @pytest.mark.parametrize(
        "user_agent",
        [
            "GPTBot/1.0",
            "CCBot/2.0 (https://commoncrawl.org/faq/)",
            "anthropic-ai",
            "ClaudeBot/1.0",
            "Mozilla/5.0 (compatible; Google-Extended)",
            "Mozilla/5.0 Bytespider",
        ],
    )
    def test_blocks_known_bots(self, anon_client, user_agent):
        resp = anon_client.get("/api/auth/login/", HTTP_USER_AGENT=user_agent)
        assert resp.status_code == 403

    def test_allows_normal_browsers(self, anon_client):
        resp = anon_client.get(
            "/api/auth/login/",
            HTTP_USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        )
        assert resp.status_code != 403

    def test_allows_curl(self, anon_client):
        resp = anon_client.get(
            "/api/auth/login/", HTTP_USER_AGENT="curl/7.88.1"
        )
        assert resp.status_code != 403


class TestSecurityHeadersMiddleware:
    def test_csp_header(self, anon_client):
        resp = anon_client.get("/api/auth/login/")
        assert "Content-Security-Policy" in resp
        assert "default-src 'none'" in resp["Content-Security-Policy"]

    def test_permissions_policy_header(self, anon_client):
        resp = anon_client.get("/api/auth/login/")
        assert "Permissions-Policy" in resp
        assert "camera=()" in resp["Permissions-Policy"]

    def test_referrer_policy_header(self, anon_client):
        resp = anon_client.get("/api/auth/login/")
        assert resp["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_coop_header(self, anon_client):
        resp = anon_client.get("/api/auth/login/")
        assert resp["Cross-Origin-Opener-Policy"] == "same-origin"
