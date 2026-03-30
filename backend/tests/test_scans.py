import io
import json

import pytest
from rest_framework import status

from findings.models import Finding, Rule
from tests.conftest import SAMPLE_SEMGREP_RESULTS, get_results


@pytest.mark.django_db
class TestScans:

    def test_list_scans(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(f"/api/projects/{project.slug}/scans/")
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1

    def test_scan_detail(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/scans/{scan_with_findings.id}/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == str(scan_with_findings.id)
        assert data["source"] == "upload"

    def test_upload_scan(self, auth_client, project, sample_semgrep_results):
        file_content = json.dumps(sample_semgrep_results).encode("utf-8")
        upload_file = io.BytesIO(file_content)
        upload_file.name = "results.json"
        resp = auth_client.post(
            f"/api/projects/{project.slug}/scans/upload/",
            {"file": upload_file},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "scan" in data
        assert "summary" in data
        assert data["scan"]["source"] == "upload"
        assert data["summary"]["total"] == 2

    def test_push_scan(self, project, sample_semgrep_results):
        """Push scan using API key auth (no token auth needed)."""
        from rest_framework.test import APIClient
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Api-Key {project.api_key}")
        resp = client.post(
            f"/api/projects/{project.slug}/scans/push/",
            sample_semgrep_results,
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "scan" in data
        assert data["scan"]["source"] == "api"
        assert "summary" in data

    def test_scan_latest(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/scans/latest/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == str(scan_with_findings.id)

    def test_ci_snippets(self, auth_client, project):
        resp = auth_client.get(
            f"/api/projects/{project.slug}/scans/ci-snippets/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "github_actions" in data
        assert "circleci" in data
        assert "gitlab_ci" in data
        assert "shell" in data
        # Verify snippets contain the project slug and API key
        assert project.slug in data["github_actions"]
        assert project.api_key in data["github_actions"]

    def test_ingestion_creates_findings(self, scan_with_findings):
        """Verify that ingest_scan creates the expected Rules and Findings."""
        project = scan_with_findings.project
        rules = Rule.objects.filter(project=project)
        findings = Finding.objects.filter(project=project)

        assert rules.count() == 2
        assert findings.count() == 2

        # Verify the scan counters were updated
        assert scan_with_findings.total_findings_count == 2
        assert scan_with_findings.new_count == 2

        # Verify rule details
        sql_rule = rules.get(
            semgrep_rule_id="python.django.security.injection.sql-injection"
        )
        assert sql_rule.severity == "ERROR"
        assert sql_rule.message == "Possible SQL injection"

        # Verify finding details
        sql_finding = findings.get(rule=sql_rule)
        assert sql_finding.file_path == "app/views.py"
        assert sql_finding.line_start == 42
        assert sql_finding.status == "new"
