import logging

from core.constants import MAX_SCAN_RESULTS, MAX_SNIPPET_LEN, SARIF_SEVERITY_MAP

from .base import NormalizedResult, normalize_path

logger = logging.getLogger(__name__)


def parse_sarif(data):
    """Parse SARIF v2.1.0 JSON report into normalized results."""
    runs = data.get("runs", [])
    if not isinstance(runs, list):
        return []

    normalized = []
    for run in runs:
        if not isinstance(run, dict):
            continue

        tool = run.get("tool", {})
        driver = tool.get("driver", {}) if isinstance(tool, dict) else {}
        rules_list = driver.get("rules", []) if isinstance(driver, dict) else []
        rule_map = {}
        for rule_def in rules_list:
            if isinstance(rule_def, dict) and "id" in rule_def:
                rule_map[rule_def["id"]] = rule_def

        results = run.get("results", [])
        if not isinstance(results, list):
            continue

        for result in results:
            if not isinstance(result, dict):
                continue
            if len(normalized) >= MAX_SCAN_RESULTS:
                logger.warning("SARIF report exceeds %d results cap", MAX_SCAN_RESULTS)
                break

            rule_id = result.get("ruleId", "")
            if not rule_id:
                continue

            level = result.get("level", "warning")
            severity = SARIF_SEVERITY_MAP.get(level, "WARNING")

            msg = result.get("message", {})
            message = msg.get("text", "") if isinstance(msg, dict) else ""

            locations = result.get("locations", [])
            path = ""
            line_start = line_end = col_start = col_end = 0
            snippet = ""

            if locations and isinstance(locations, list):
                loc = locations[0]
                if isinstance(loc, dict):
                    phys = loc.get("physicalLocation", {})
                    if isinstance(phys, dict):
                        artifact = phys.get("artifactLocation", {})
                        if isinstance(artifact, dict):
                            path = artifact.get("uri", "")
                        region = phys.get("region", {})
                        if isinstance(region, dict):
                            line_start = region.get("startLine", 0)
                            line_end = region.get("endLine", line_start)
                            col_start = region.get("startColumn", 0)
                            col_end = region.get("endColumn", 0)
                            snip = region.get("snippet", {})
                            if isinstance(snip, dict):
                                snippet = snip.get("text", "")

            path = normalize_path(path)
            if not path:
                continue

            if isinstance(snippet, str) and len(snippet) > MAX_SNIPPET_LEN:
                snippet = snippet[:MAX_SNIPPET_LEN] + "\n... [truncated]"

            metadata = {}
            rule_def = rule_map.get(rule_id, {})
            if isinstance(rule_def, dict):
                props = rule_def.get("properties", {})
                if isinstance(props, dict):
                    metadata["cwe"] = props.get("cwe", [])
                    metadata["owasp"] = props.get("owasp", [])
                    metadata["tags"] = props.get("tags", [])
                    metadata["category"] = props.get("category", "")
                help_obj = rule_def.get("help", {})
                if isinstance(help_obj, dict):
                    metadata["references"] = [help_obj.get("text", "")]

            normalized.append(NormalizedResult(
                check_id=rule_id,
                path=path,
                line_start=line_start,
                line_end=line_end,
                col_start=col_start,
                col_end=col_end,
                severity=severity,
                message=message,
                snippet=snippet,
                metadata=metadata,
            ))

    return normalized
