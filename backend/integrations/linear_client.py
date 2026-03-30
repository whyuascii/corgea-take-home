import logging

import requests

logger = logging.getLogger(__name__)

LINEAR_API_URL = "https://api.linear.app/graphql"


def _headers(config):
    return {
        "Authorization": config.linear_api_key,
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
        resp = requests.post(
            LINEAR_API_URL,
            headers=_headers(config),
            json={"query": query, "variables": {"teamId": config.linear_team_id}},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data", {}).get("team"):
                return {"ok": True, "team_name": data["data"]["team"]["name"]}
            errors = data.get("errors", [{}])
            return {"ok": False, "error": errors[0].get("message", "Team not found")}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
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
        resp = requests.post(
            LINEAR_API_URL,
            headers=_headers(config),
            json={"query": query, "variables": {"issueId": issue_id}},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            issue = data.get("data", {}).get("issue")
            if issue and issue.get("state"):
                return issue["state"]["type"]
            logger.warning(
                "Linear issue %s not found or has no state", issue_id,
            )
            return None
        logger.warning(
            "Failed to fetch Linear issue %s status: HTTP %s",
            issue_id, resp.status_code,
        )
        return None
    except Exception:
        logger.warning(
            "Failed to fetch Linear issue %s status", issue_id, exc_info=True,
        )
        return None


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

    resp = requests.post(
        LINEAR_API_URL,
        headers=_headers(config),
        json={"query": mutation, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("errors"):
        raise Exception(data["errors"][0].get("message", "Linear API error"))

    issue = data["data"]["issueCreate"]["issue"]
    return issue["id"], issue["url"]
