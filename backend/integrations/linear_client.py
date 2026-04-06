import logging

import requests

from core.constants import INTEGRATION_API_TIMEOUT, INTEGRATION_CREATE_TIMEOUT, LINEAR_API_URL
from integrations.exceptions import IntegrationAPIError
from integrations.validators import SSRFSafeAdapter

logger = logging.getLogger(__name__)


def _session():
    """Build a requests.Session with SSRF protection on every request."""
    s = requests.Session()
    s.mount("http://", SSRFSafeAdapter())
    s.mount("https://", SSRFSafeAdapter())
    return s


def _headers(config):
    api_key = config.linear_api_key
    # Linear API expects "Bearer <token>" format
    if not api_key.startswith("Bearer "):
        api_key = f"Bearer {api_key}"
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }


def test_linear_connection(config):
    """Test Linear credentials by fetching the team."""
    query = """
    query($teamId: String!) {
        team(id: $teamId) {
            id
            name
        }
    }
    """
    try:
        resp = _session().post(
            LINEAR_API_URL,
            headers=_headers(config),
            json={"query": query, "variables": {"teamId": config.linear_team_id}},
            timeout=INTEGRATION_API_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data", {}).get("team"):
                team_name = data.get("data", {}).get("team", {}).get("name", "")
                return {"ok": True, "team_name": team_name}
            errors = data.get("errors", [{}])
            return {"ok": False, "error": errors[0].get("message", "Team not found")}
        return {"ok": False, "error": f"HTTP {resp.status_code}: Check API key and team ID"}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}


def get_linear_issue_status(config, issue_id):
    """Fetch the state type for a Linear issue.

    Returns the state type string (e.g., "backlog", "unstarted", "started",
    "completed", "cancelled") or None if the API call fails.
    """
    query = """
    query($issueId: String!) {
        issue(id: $issueId) {
            state {
                type
            }
        }
    }
    """
    try:
        resp = _session().post(
            LINEAR_API_URL,
            headers=_headers(config),
            json={"query": query, "variables": {"issueId": issue_id}},
            timeout=INTEGRATION_API_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            issue = data.get("data", {}).get("issue")
            if issue and issue.get("state"):
                return issue.get("state", {}).get("type")
            logger.warning(
                "Linear issue %s not found or has no state", issue_id,
            )
            return None
        logger.warning(
            "Failed to fetch Linear issue %s status: HTTP %s",
            issue_id, resp.status_code,
        )
        return None
    except (requests.RequestException, ConnectionError, KeyError):
        logger.warning(
            "Failed to fetch Linear issue %s status", issue_id, exc_info=True,
        )
        return None


def transition_linear_issue_to_done(config, issue_id):
    """Transition a Linear issue to a 'completed' workflow state.

    Returns True if transitioned, False if already completed/cancelled or
    no completed state found. Lets exceptions propagate to the caller.
    """
    current_status = get_linear_issue_status(config, issue_id)
    if current_status in ("completed", "cancelled"):
        return False

    # Query the team's workflow states to find the completed state
    states_query = """
    query($teamId: String!) {
        team(id: $teamId) {
            states {
                nodes {
                    id
                    type
                }
            }
        }
    }
    """
    resp = _session().post(
        LINEAR_API_URL,
        headers=_headers(config),
        json={"query": states_query, "variables": {"teamId": config.linear_team_id}},
        timeout=INTEGRATION_API_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("errors"):
        raise IntegrationAPIError(data["errors"][0].get("message", "Linear API error"))

    states = (
        data.get("data", {}).get("team", {}).get("states", {}).get("nodes", [])
    )
    completed_state = next(
        (s for s in states if s.get("type") == "completed"), None,
    )
    if completed_state is None:
        logger.warning(
            "No completed workflow state found for Linear team %s",
            config.linear_team_id,
        )
        return False

    # Transition the issue
    mutation = """
    mutation($issueId: String!, $stateId: String!) {
        issueUpdate(id: $issueId, input: { stateId: $stateId }) {
            success
        }
    }
    """
    resp = _session().post(
        LINEAR_API_URL,
        headers=_headers(config),
        json={
            "query": mutation,
            "variables": {
                "issueId": issue_id,
                "stateId": completed_state["id"],
            },
        },
        timeout=INTEGRATION_API_TIMEOUT,
    )
    resp.raise_for_status()
    result = resp.json()

    if result.get("errors"):
        raise IntegrationAPIError(result["errors"][0].get("message", "Linear API error"))

    success = result.get("data", {}).get("issueUpdate", {}).get("success", False)
    if success:
        logger.info("Transitioned Linear issue %s to completed", issue_id)
    return success


def create_linear_issue(config, finding):
    """Create a Linear issue for a finding. Returns (issue_id, issue_url) or raises."""
    mutation = """
    mutation($teamId: String!, $title: String!, $description: String) {
        issueCreate(input: {
            teamId: $teamId
            title: $title
            description: $description
        }) {
            success
            issue {
                id
                identifier
                url
            }
        }
    }
    """
    description = (
        f"**Vulnerability found in `{finding.file_path}` "
        f"(lines {finding.line_start}-{finding.line_end})**\n\n"
        f"**Rule:** {finding.rule.semgrep_rule_id}\n"
        f"**Severity:** {finding.rule.severity}\n"
        f"**Message:** {finding.rule.message}"
    )
    if finding.code_snippet:
        description += f"\n\n```\n{finding.code_snippet}\n```"

    variables = {
        "teamId": config.linear_team_id,
        "title": f"[{finding.rule.severity.upper()}] {finding.rule.semgrep_rule_id}",
        "description": description,
    }

    resp = _session().post(
        LINEAR_API_URL,
        headers=_headers(config),
        json={"query": mutation, "variables": variables},
        timeout=INTEGRATION_CREATE_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("errors"):
        error_msg = data.get("errors", [{}])[0].get("message", "Linear API error")
        raise IntegrationAPIError(error_msg)

    issue_create = data.get("data", {}).get("issueCreate", {})
    issue = issue_create.get("issue")
    if not issue:
        raise IntegrationAPIError(
            "Linear API response missing issue data in issueCreate"
        )
    issue_id = issue.get("id")
    issue_url = issue.get("url")
    if not issue_id or not issue_url:
        raise IntegrationAPIError(
            "Linear API response missing 'id' or 'url' in issue data"
        )
    return issue_id, issue_url
