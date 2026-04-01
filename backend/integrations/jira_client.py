import logging

import requests
from requests.auth import HTTPBasicAuth

from core.constants import INTEGRATION_API_TIMEOUT, INTEGRATION_CREATE_TIMEOUT

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
            timeout=INTEGRATION_API_TIMEOUT,
            allow_redirects=False,
        )
        if resp.status_code == 200:
            return {"ok": True, "project_name": resp.json().get("name", "")}
        return {"ok": False, "error": f"HTTP {resp.status_code}: Check credentials and project key"}
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
            timeout=INTEGRATION_API_TIMEOUT,
            allow_redirects=False,
        )
        if resp.status_code == 200:
            data = resp.json()
            status_key = (
                data.get("fields", {})
                .get("status", {})
                .get("statusCategory", {})
                .get("key")
            )
            if status_key is None:
                logger.warning(
                    "Jira issue %s response missing expected status fields",
                    issue_key,
                )
            return status_key
        logger.warning(
            "Failed to fetch Jira issue %s status: HTTP %s",
            issue_key, resp.status_code,
        )
        return None
    except (requests.RequestException, ConnectionError, KeyError):
        logger.warning(
            "Failed to fetch Jira issue %s status", issue_key, exc_info=True,
        )
        return None


def transition_jira_issue_to_done(config, issue_key):
    """Transition a Jira issue to a 'done' status category.

    Returns True if transitioned, False if already done or no done-transition available.
    Lets exceptions propagate to the caller.
    """
    current_status = get_jira_issue_status(config, issue_key)
    if current_status == "done":
        return False

    resp = requests.get(
        f"{_base_url(config)}/rest/api/3/issue/{issue_key}/transitions",
        auth=_auth(config),
        headers={"Accept": "application/json"},
        timeout=INTEGRATION_API_TIMEOUT,
        allow_redirects=False,
    )
    resp.raise_for_status()

    transitions = resp.json().get("transitions", [])
    done_transition = next(
        (
            t for t in transitions
            if t.get("to", {}).get("statusCategory", {}).get("key") == "done"
        ),
        None,
    )
    if done_transition is None:
        logger.warning(
            "No done-category transition available for Jira issue %s", issue_key,
        )
        return False

    resp = requests.post(
        f"{_base_url(config)}/rest/api/3/issue/{issue_key}/transitions",
        auth=_auth(config),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={"transition": {"id": done_transition["id"]}},
        timeout=INTEGRATION_API_TIMEOUT,
        allow_redirects=False,
    )
    resp.raise_for_status()
    logger.info("Transitioned Jira issue %s to done", issue_key)
    return True


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
        timeout=INTEGRATION_CREATE_TIMEOUT,
        allow_redirects=False,
    )
    resp.raise_for_status()
    data = resp.json()
    issue_key = data.get("key")
    if not issue_key:
        raise Exception("Jira API response missing 'key' field")
    issue_url = f"{_base_url(config)}/browse/{issue_key}"
    return issue_key, issue_url
