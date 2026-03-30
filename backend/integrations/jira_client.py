import logging

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


def _auth(config):
    return HTTPBasicAuth(config.jira_user_email, config.jira_api_token)


def _base_url(config):
    return config.jira_instance_url.rstrip("/")


def test_jira_connection(config):
    """Test Jira credentials by fetching the project."""
    try:
        resp = requests.get(
            f"{_base_url(config)}/rest/api/3/project/{config.jira_project_key}",
            auth=_auth(config),
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            return {"ok": True, "project_name": resp.json().get("name", "")}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}


def get_jira_issue_status(config, issue_key):
    """Fetch the status category key for a Jira issue.

    Returns the status category key (e.g., "done", "indeterminate", "new")
    or None if the API call fails.
    """
    try:
        resp = requests.get(
            f"{_base_url(config)}/rest/api/3/issue/{issue_key}?fields=status",
            auth=_auth(config),
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["fields"]["status"]["statusCategory"]["key"]
        logger.warning(
            "Failed to fetch Jira issue %s status: HTTP %s",
            issue_key, resp.status_code,
        )
        return None
    except Exception:
        logger.warning(
            "Failed to fetch Jira issue %s status", issue_key, exc_info=True,
        )
        return None


def create_jira_issue(config, finding):
    """Create a Jira issue for a finding. Returns (issue_key, issue_url) or raises."""
    payload = {
        "fields": {
            "project": {"key": config.jira_project_key},
            "summary": f"[{finding.rule.severity.upper()}] {finding.rule.semgrep_rule_id}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Vulnerability found in {finding.file_path} "
                                    f"(lines {finding.line_start}-{finding.line_end})\n\n"
                                    f"Rule: {finding.rule.semgrep_rule_id}\n"
                                    f"Severity: {finding.rule.severity}\n"
                                    f"Message: {finding.rule.message}"
                                ),
                            }
                        ],
                    }
                ],
            },
            "issuetype": {"name": "Bug"},
        }
    }

    resp = requests.post(
        f"{_base_url(config)}/rest/api/3/issue",
        auth=_auth(config),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    issue_key = data["key"]
    issue_url = f"{_base_url(config)}/browse/{issue_key}"
    return issue_key, issue_url
