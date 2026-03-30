import pytest
from rest_framework import status

from tests.conftest import get_results


@pytest.mark.django_db
class TestOverview:

    def test_overview_summary(self, auth_client, scan_with_findings):
        resp = auth_client.get("/api/overview/summary/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "total_findings" in data
        assert "total_active" in data
        assert "total_false_positives" in data
        assert "severity_distribution" in data
        assert "project_activity" in data
        assert data["total_findings"] >= 2

    def test_overview_rules(self, auth_client, scan_with_findings):
        resp = auth_client.get("/api/overview/rules/")
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1
        first = results[0]
        assert "semgrep_rule_id" in first
        assert "severity" in first
        assert "finding_count" in first
        assert "project_count" in first

    def test_overview_findings(self, auth_client, scan_with_findings):
        resp = auth_client.get("/api/overview/findings/")
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1
        first = results[0]
        assert "project_slug" in first
        assert "project_name" in first
        assert "rule_id_display" in first
