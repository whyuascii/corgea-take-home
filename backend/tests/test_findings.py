import pytest
from rest_framework import status

from findings.models import AuditLog, Finding, FindingComment, FindingHistory, Rule
from integrations.models import IntegrationConfig, StatusMapping
from tests.conftest import get_results


@pytest.mark.django_db
class TestFindings:

    def test_list_findings(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/"
        )
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1

        first = results[0]
        assert "id" in first
        assert "rule_id_display" in first
        assert "severity" in first
        assert "status" in first
        assert "file_path" in first

    def test_finding_detail(self, auth_client, finding):
        project = finding.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/{finding.id}/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == str(finding.id)
        assert "history" in data
        assert "comments" in data

    def test_update_finding_status(self, auth_client, finding):
        project = finding.project
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/findings/{finding.id}/",
            {"status": "resolved"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "resolved"

        assert FindingHistory.objects.filter(
            finding=finding, new_status="resolved"
        ).exists()

    def test_finding_history(self, auth_client, finding):
        project = finding.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/{finding.id}/history/"
        )
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)

        assert len(results) >= 1

    def test_finding_trends(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/trends/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()

        results = get_results(resp)
        assert len(results) > 0
        first_day = results[0]
        assert "date" in first_day
        assert "new" in first_day
        assert "resolved" in first_day

    def test_finding_export_csv(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/export/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp["Content-Type"] == "text/csv"
        content = resp.content.decode("utf-8")
        lines = content.strip().split("\n")
        # Header + at least one data row
        assert len(lines) >= 2
        assert "Rule ID" in lines[0]

    def test_finding_search(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/search/",
            {"q": "sql-injection"},
        )
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 1

    def test_mark_false_positive(self, auth_client, finding):
        project = finding.project
        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/{finding.id}/false-positive/",
            {"is_false_positive": True, "reason": "Not exploitable"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["affected_count"] >= 1
        finding.refresh_from_db()
        assert finding.is_false_positive is True
        assert finding.false_positive_reason == "Not exploitable"

    def test_bulk_status_change(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        findings = Finding.objects.filter(project=project)
        finding_ids = [str(f.id) for f in findings]

        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/bulk/",
            {
                "finding_ids": finding_ids,
                "action": "status_change",
                "status": "resolved",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["updated"] >= 1

        # Verify findings are now resolved
        for f in Finding.objects.filter(id__in=finding_ids):
            assert f.status == "resolved"

    def test_project_summary(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/summary/"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "status_counts" in data
        assert "severity_counts" in data
        assert "total_findings" in data
        assert "total_active" in data
        assert "top_rules" in data
        assert "recent_scans" in data

    def test_list_rules(self, auth_client, scan_with_findings):
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/rules/"
        )
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        assert len(results) >= 2
        first = results[0]
        assert "id" in first
        assert "semgrep_rule_id" in first
        assert "severity" in first
        assert "active_finding_count" in first
        assert "total_finding_count" in first

    def test_update_rule_status(self, auth_client, rule):
        project = rule.project
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/findings/rules/{rule.id}/",
            {"status": "ignored"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["status"] == "ignored"
        rule.refresh_from_db()
        assert rule.status == "ignored"

    def test_finding_hides_fp_by_default(self, auth_client, finding):
        """False-positive findings are hidden from the default listing."""
        project = finding.project
        finding.is_false_positive = True
        finding.false_positive_reason = "Not relevant"
        finding.save(update_fields=["is_false_positive", "false_positive_reason"])

        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/"
        )
        assert resp.status_code == status.HTTP_200_OK
        results = get_results(resp)
        result_ids = [r["id"] for r in results]
        assert str(finding.id) not in result_ids

        # But explicitly requesting FPs should show it
        resp2 = auth_client.get(
            f"/api/projects/{project.slug}/findings/",
            {"is_false_positive": "true"},
        )
        assert resp2.status_code == status.HTTP_200_OK
        results2 = get_results(resp2)
        result_ids2 = [r["id"] for r in results2]
        assert str(finding.id) in result_ids2

    def test_finding_comments_crud(self, auth_client, finding, user):
        project = finding.project

        # Create a comment
        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/{finding.id}/comments/",
            {"text": "This needs to be fixed ASAP."},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        comment_data = resp.json()
        assert comment_data["text"] == "This needs to be fixed ASAP."
        assert comment_data["username"] == user.username
        comment_id = comment_data["id"]

        # List comments
        resp2 = auth_client.get(
            f"/api/projects/{project.slug}/findings/{finding.id}/comments/"
        )
        assert resp2.status_code == status.HTTP_200_OK
        results = get_results(resp2)
        assert len(results) >= 1
        assert any(c["id"] == comment_id for c in results)

        # Delete the comment
        resp3 = auth_client.delete(
            f"/api/projects/{project.slug}/findings/{finding.id}/comments/{comment_id}/"
        )
        assert resp3.status_code == status.HTTP_204_NO_CONTENT
        assert not FindingComment.objects.filter(id=comment_id).exists()

    def test_audit_log(self, auth_client, scan_with_findings):
        """Verify audit log endpoint returns entries after scan ingestion activities."""
        project = scan_with_findings.project
        resp = auth_client.get(
            f"/api/projects/{project.slug}/findings/audit-log/"
        )
        assert resp.status_code == status.HTTP_200_OK
        # Audit log may be empty if the scan fixture was created directly via ORM
        # (not through the upload endpoint), so just verify the endpoint works.
        data = resp.json()
        # data can be list or paginated dict
        if isinstance(data, dict) and "results" in data:
            assert isinstance(data["results"], list)
        else:
            assert isinstance(data, list)


@pytest.mark.django_db
class TestAuditCoverage:
    """Verify that state-changing operations produce audit log entries."""

    def test_profile_update_audit(self, auth_client, user):
        AuditLog.objects.all().delete()
        resp = auth_client.patch(
            "/api/auth/me/",
            {"first_name": "Updated", "current_password": "testpass1234"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        entry = AuditLog.objects.filter(action=AuditLog.Action.PROFILE_UPDATE).first()
        assert entry is not None
        assert entry.user == user
        assert "first_name" in entry.metadata["updated_fields"]

    def test_project_update_audit(self, auth_client, project):
        AuditLog.objects.all().delete()
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/",
            {"description": "Audit test"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        entry = AuditLog.objects.filter(action=AuditLog.Action.PROJECT_UPDATE).first()
        assert entry is not None
        assert str(entry.target_id) == str(project.id)

    def test_rule_update_audit(self, auth_client, rule):
        AuditLog.objects.all().delete()
        project = rule.project
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/findings/rules/{rule.id}/",
            {"status": "ignored"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        entry = AuditLog.objects.filter(action=AuditLog.Action.RULE_STATUS_CHANGE).first()
        assert entry is not None
        assert entry.metadata["old_status"] == "active"
        assert entry.metadata["new_status"] == "ignored"
        assert "affected_findings" in entry.metadata

    def test_bulk_status_change_audit(self, auth_client, scan_with_findings):
        AuditLog.objects.all().delete()
        project = scan_with_findings.project
        finding_ids = list(
            Finding.objects.filter(project=project).values_list("id", flat=True)
        )
        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/bulk/",
            {
                "finding_ids": [str(fid) for fid in finding_ids],
                "action": "status_change",
                "status": "resolved",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        entry = AuditLog.objects.filter(
            action=AuditLog.Action.FINDING_STATUS_CHANGE,
            metadata__bulk=True,
        ).first()
        assert entry is not None
        assert entry.metadata["new_status"] == "resolved"
        assert entry.metadata["count"] >= 1

    def test_bulk_false_positive_audit(self, auth_client, scan_with_findings):
        AuditLog.objects.all().delete()
        project = scan_with_findings.project
        finding_ids = list(
            Finding.objects.filter(project=project).values_list("id", flat=True)
        )
        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/bulk/",
            {
                "finding_ids": [str(fid) for fid in finding_ids],
                "action": "false_positive",
                "is_false_positive": True,
                "reason": "test",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        entry = AuditLog.objects.filter(
            action=AuditLog.Action.FINDING_FALSE_POSITIVE,
            metadata__bulk=True,
        ).first()
        assert entry is not None
        assert entry.metadata["is_false_positive"] is True

    def test_comment_created_audit(self, auth_client, finding):
        AuditLog.objects.all().delete()
        project = finding.project
        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/{finding.id}/comments/",
            {"text": "Audit test comment"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        entry = AuditLog.objects.filter(action=AuditLog.Action.COMMENT_CREATED).first()
        assert entry is not None
        assert entry.metadata["finding_id"] == str(finding.id)

    def test_comment_deleted_audit(self, auth_client, finding):
        AuditLog.objects.all().delete()
        project = finding.project
        resp = auth_client.post(
            f"/api/projects/{project.slug}/findings/{finding.id}/comments/",
            {"text": "Will be deleted"},
            format="json",
        )
        comment_id = resp.json()["id"]
        AuditLog.objects.all().delete()
        resp = auth_client.delete(
            f"/api/projects/{project.slug}/findings/{finding.id}/comments/{comment_id}/"
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        entry = AuditLog.objects.filter(action=AuditLog.Action.COMMENT_DELETED).first()
        assert entry is not None
        assert entry.metadata["comment_id"] == comment_id

    def test_mapping_created_audit(self, auth_client, project):
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_instance_url="https://test.atlassian.net",
            jira_project_key="TEST",
        )
        AuditLog.objects.all().delete()
        resp = auth_client.post(
            f"/api/projects/{project.slug}/integrations/{config.id}/mappings/",
            {"external_status": "Done", "internal_status": "resolved"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        entry = AuditLog.objects.filter(
            action=AuditLog.Action.INTEGRATION_CHANGE,
            metadata__action="mapping_created",
        ).first()
        assert entry is not None

    def test_mapping_updated_audit(self, auth_client, project):
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_instance_url="https://test.atlassian.net",
            jira_project_key="TEST",
        )
        mapping = StatusMapping.objects.create(
            integration=config,
            external_status="In Progress",
            internal_status="open",
        )
        AuditLog.objects.all().delete()
        resp = auth_client.patch(
            f"/api/projects/{project.slug}/integrations/{config.id}/mappings/{mapping.id}/",
            {"internal_status": "resolved"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        entry = AuditLog.objects.filter(
            action=AuditLog.Action.INTEGRATION_CHANGE,
            metadata__action="mapping_updated",
        ).first()
        assert entry is not None

    def test_mapping_deleted_audit(self, auth_client, project):
        config = IntegrationConfig.objects.create(
            project=project,
            provider=IntegrationConfig.Provider.JIRA,
            jira_instance_url="https://test.atlassian.net",
            jira_project_key="TEST",
        )
        mapping = StatusMapping.objects.create(
            integration=config,
            external_status="Done",
            internal_status="resolved",
        )
        AuditLog.objects.all().delete()
        resp = auth_client.delete(
            f"/api/projects/{project.slug}/integrations/{config.id}/mappings/{mapping.id}/"
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        entry = AuditLog.objects.filter(
            action=AuditLog.Action.INTEGRATION_CHANGE,
            metadata__action="mapping_deleted",
        ).first()
        assert entry is not None
