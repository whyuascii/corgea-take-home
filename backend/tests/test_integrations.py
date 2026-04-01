import hashlib
import hmac
import json
from unittest.mock import patch, MagicMock

import pytest
from django.db.models import Q
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
        assert "webhook_url" in data
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

        payload = json.dumps({
            "issue": {
                "key": "VULN-42",
                "fields": {
                    "status": {"name": "Done"},
                },
            }
        }).encode()
        signature = hmac.new(
            config.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        client = APIClient()
        resp = client.post(
            f"/api/webhooks/jira/{config.webhook_secret}/",
            payload,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE=signature,
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

        payload = json.dumps({
            "action": "update",
            "data": {
                "id": "LIN-123",
                "state": {"name": "Done"},
            },
        }).encode()
        signature = hmac.new(
            config.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        client = APIClient()
        resp = client.post(
            f"/api/webhooks/linear/{config.webhook_secret}/",
            payload,
            content_type="application/json",
            HTTP_LINEAR_SIGNATURE=signature,
        )
        assert resp.status_code == status.HTTP_200_OK

        finding.refresh_from_db()
        assert finding.status == "resolved"


@pytest.mark.django_db
class TestTicketClosure:

    def _make_config(self, project, provider="jira"):
        if provider == "jira":
            return IntegrationConfig.objects.create(
                project=project,
                provider=IntegrationConfig.Provider.JIRA,
                is_enabled=True,
                jira_instance_url="https://myteam.atlassian.net",
                jira_project_key="VULN",
                jira_user_email="user@example.com",
                jira_api_token="secret",
            )
        return IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.LINEAR,
            is_enabled=True,
            linear_team_id="team-abc",
            linear_api_key="lin_api_key",
        )

    @patch("integrations.ticket_service.transition_jira_issue_to_done", return_value=True)
    def test_close_jira_ticket_on_resolve(self, mock_transition, finding):
        self._make_config(finding.project, "jira")
        finding.jira_ticket_id = "VULN-42"
        finding.jira_ticket_url = "https://myteam.atlassian.net/browse/VULN-42"
        finding.save(update_fields=["jira_ticket_id", "jira_ticket_url"])

        from integrations.ticket_service import close_tickets_for_finding
        close_tickets_for_finding(finding)

        mock_transition.assert_called_once()
        history = FindingHistory.objects.filter(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
        )
        assert history.exists()
        assert "VULN-42" in history.first().notes

    @patch("integrations.ticket_service.transition_linear_issue_to_done", return_value=True)
    def test_close_linear_ticket_on_resolve(self, mock_transition, finding):
        self._make_config(finding.project, "linear")
        finding.linear_ticket_id = "LIN-123"
        finding.linear_ticket_url = "https://linear.app/team/issue/LIN-123"
        finding.save(update_fields=["linear_ticket_id", "linear_ticket_url"])

        from integrations.ticket_service import close_tickets_for_finding
        close_tickets_for_finding(finding)

        mock_transition.assert_called_once()
        history = FindingHistory.objects.filter(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
        )
        assert history.exists()
        assert "LIN-123" in history.first().notes

    def test_skip_closure_when_no_ticket(self, finding):
        self._make_config(finding.project, "jira")
        assert not finding.jira_ticket_id
        assert not finding.linear_ticket_id

        from integrations.ticket_service import close_tickets_for_finding
        close_tickets_for_finding(finding)

        assert not FindingHistory.objects.filter(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
        ).exists()

    @patch("integrations.ticket_service.transition_jira_issue_to_done", return_value=False)
    def test_skip_closure_when_already_done(self, mock_transition, finding):
        self._make_config(finding.project, "jira")
        finding.jira_ticket_id = "VULN-99"
        finding.jira_ticket_url = "https://myteam.atlassian.net/browse/VULN-99"
        finding.save(update_fields=["jira_ticket_id", "jira_ticket_url"])

        from integrations.ticket_service import close_tickets_for_finding
        close_tickets_for_finding(finding)

        mock_transition.assert_called_once()
        assert not FindingHistory.objects.filter(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
        ).exists()

    @patch("integrations.ticket_service.transition_jira_issue_to_done", side_effect=Exception("API error"))
    def test_closure_failure_logged_not_raised(self, mock_transition, finding):
        self._make_config(finding.project, "jira")
        finding.jira_ticket_id = "VULN-50"
        finding.jira_ticket_url = "https://myteam.atlassian.net/browse/VULN-50"
        finding.save(update_fields=["jira_ticket_id", "jira_ticket_url"])

        from integrations.ticket_service import close_tickets_for_finding
        # Should not raise
        close_tickets_for_finding(finding)

        assert not FindingHistory.objects.filter(
            finding=finding,
            change_type=FindingHistory.ChangeType.TICKET_CLOSED,
        ).exists()

    @patch("integrations.ticket_service.close_tickets_for_finding")
    def test_dispatch_ticket_closure_filters_ticketed(self, mock_close, finding):
        """Only findings with ticket IDs get closure dispatched."""
        finding_with_ticket = finding
        finding_with_ticket.jira_ticket_id = "VULN-10"
        finding_with_ticket.save(update_fields=["jira_ticket_id"])

        from findings.models import Rule
        rule = Rule.objects.filter(project=finding.project).first()
        finding_no_ticket = Finding.objects.create(
            project=finding.project,
            rule=rule,
            file_path="other/file.py",
            line_start=1,
            line_end=1,
            status=Finding.Status.RESOLVED,
        )

        from scans.ingestion import dispatch_ticket_closure
        dispatch_ticket_closure([finding_with_ticket.id, finding_no_ticket.id])

        # Sync fallback should only close the one with a ticket
        assert mock_close.call_count == 1
