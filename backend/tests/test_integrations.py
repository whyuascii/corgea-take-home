import pytest
from rest_framework import status

from findings.models import Finding, FindingHistory
from integrations.models import IntegrationConfig, StatusMapping
from tests.conftest import get_results


@pytest.mark.django_db
class TestIntegrations:

    def test_create_integration(self, auth_client, project):
        resp = auth_client.post(
            f"/api/projects/{project.slug}/integrations/",
            {
                "provider": "jira",
                "is_enabled": False,
                "jira_instance_url": "https://myteam.atlassian.net",
                "jira_project_key": "VULN",
                "jira_user_email": "user@example.com",
                "jira_api_token": "secret-token-123",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["provider"] == "jira"
        assert data["jira_project_key"] == "VULN"
        assert "webhook_secret" in data
        # Token is write-only, should not appear in response
        assert "jira_api_token" not in data or data.get("jira_api_token") is None
        # But the boolean flag should indicate it was set
        assert data["jira_api_token_set"] is True

    def test_list_integrations(self, auth_client, project):
        IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_instance_url="https://myteam.atlassian.net",
            jira_project_key="VULN",
        )
        resp = auth_client.get(
            f"/api/projects/{project.slug}/integrations/"
        )
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1

    def test_update_integration(self, auth_client, project):
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_instance_url="https://old.atlassian.net",
            jira_project_key="OLD",
        )
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/integrations/{config.id}/",
            {"jira_project_key": "NEW", "is_enabled": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["jira_project_key"] == "NEW"
        assert data["is_enabled"] is True

    def test_delete_integration(self, auth_client, project):
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.LINEAR,
            linear_team_id="team-123",
        )
        resp = auth_client.delete(
            f"/api/projects/{project.slug}/integrations/{config.id}/"
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not IntegrationConfig.objects.filter(id=config.id).exists()

    def test_create_status_mapping(self, auth_client, project):
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_instance_url="https://myteam.atlassian.net",
            jira_project_key="VULN",
        )
        resp = auth_client.post(
            f"/api/projects/{project.slug}/integrations/{config.id}/mappings/",
            {"external_status": "Done", "internal_status": "resolved"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["external_status"] == "Done"
        assert data["internal_status"] == "resolved"

    def test_jira_webhook(self, finding):
        """Jira webhook syncs finding status via status mapping."""
        from rest_framework.test import APIClient
        project = finding.project
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            is_enabled=True,
            jira_instance_url="https://myteam.atlassian.net",
            jira_project_key="VULN",
        )
        StatusMapping.objects.create(
            integration=config,
            external_status="Done",
            internal_status="resolved",
        )
        # Attach a jira ticket to the finding
        finding.jira_ticket_id = "VULN-42"
        finding.jira_ticket_url = "https://myteam.atlassian.net/browse/VULN-42"
        finding.save(update_fields=["jira_ticket_id", "jira_ticket_url"])

        client = APIClient()
        resp = client.post(
            f"/api/webhooks/jira/{config.webhook_secret}/",
            {
                "issue": {
                    "key": "VULN-42",
                    "fields": {
                        "status": {"name": "Done"},
                    },
                }
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

        finding.refresh_from_db()
        assert finding.status == "resolved"

    def test_linear_webhook(self, finding):
        """Linear webhook syncs finding status via status mapping."""
        from rest_framework.test import APIClient
        project = finding.project
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.LINEAR,
            is_enabled=True,
            linear_team_id="team-abc",
        )
        StatusMapping.objects.create(
            integration=config,
            external_status="Done",
            internal_status="resolved",
        )
        # Attach a linear ticket to the finding
        finding.linear_ticket_id = "LIN-123"
        finding.linear_ticket_url = "https://linear.app/team/issue/LIN-123"
        finding.save(update_fields=["linear_ticket_id", "linear_ticket_url"])

        client = APIClient()
        resp = client.post(
            f"/api/webhooks/linear/{config.webhook_secret}/",
            {
                "action": "update",
                "data": {
                    "id": "LIN-123",
                    "state": {"name": "Done"},
                },
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK

        finding.refresh_from_db()
        assert finding.status == "resolved"
