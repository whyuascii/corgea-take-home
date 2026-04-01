"""Parser for Semgrep JSON output."""

import logging

from core.constants import MAX_SCAN_RESULTS, MAX_SNIPPET_LEN

from .base import NormalizedResult, normalize_path

logger = logging.getLogger(__name__)


def _truncate_snippet(snippet):
    if isinstance(snippet, str) and len(snippet) > MAX_SNIPPET_LEN:
        return snippet[:MAX_SNIPPET_LEN] + "\n... [truncated]"
    return snippet if isinstance(snippet, str) else ""


def _sanitise_metadata(metadata_raw, fix_suggestion):
    if not isinstance(metadata_raw, dict):
        metadata_raw = {}
    return {
        "owasp": metadata_raw.get("owasp", []),
        "cwe": metadata_raw.get("cwe", []),
        "references": metadata_raw.get("references", []),
        "category": metadata_raw.get("category", ""),
        "technology": metadata_raw.get("technology", []),
        "subcategory": metadata_raw.get("subcategory", []),
        "likelihood": metadata_raw.get("likelihood", ""),
        "impact": metadata_raw.get("impact", ""),
        "confidence": metadata_raw.get("confidence", ""),
        "vulnerability_class": metadata_raw.get("vulnerability_class", []),
        "source": metadata_raw.get("source", ""),
        "shortlink": metadata_raw.get("shortlink", ""),
        "fix": fix_suggestion if isinstance(fix_suggestion, str) else "",
    }


def parse_semgrep(data):
    """Parse Semgrep JSON report into normalized results."""
    results = data.get("results", [])
    if not isinstance(results, list):
        return []

    if len(results) > MAX_SCAN_RESULTS:
        logger.warning("Semgrep report has %d results, capping at %d", len(results), MAX_SCAN_RESULTS)
        results = results[:MAX_SCAN_RESULTS]

    normalized = []
    for result in results:
        if not isinstance(result, dict):
            continue

        check_id = result.get("check_id", "")
        path = normalize_path(result.get("path", ""))
        if not check_id or not path:
            continue

        start = result.get("start", {})
        end = result.get("end", {})
        extra = result.get("extra", {})
        if not isinstance(extra, dict):
            extra = {}

        normalized.append(NormalizedResult(
            check_id=check_id,
            path=path,
            line_start=start.get("line", 0) if isinstance(start, dict) else 0,
            line_end=end.get("line", 0) if isinstance(end, dict) else 0,
            col_start=start.get("col", 0) if isinstance(start, dict) else 0,
            col_end=end.get("col", 0) if isinstance(end, dict) else 0,
            severity=extra.get("severity", "WARNING"),
            message=extra.get("message", ""),
            snippet=_truncate_snippet(extra.get("lines", "")),
            metadata=_sanitise_metadata(extra.get("metadata", {}), extra.get("fix", "")),
        ))

    return normalized
