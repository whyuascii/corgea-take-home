from .base import NormalizedResult
from .semgrep import parse_semgrep
from .sarif import parse_sarif

__all__ = ["NormalizedResult", "parse_semgrep", "parse_sarif", "detect_format", "parse"]


def detect_format(data):
    """Auto-detect scan report format from JSON structure."""
    if not isinstance(data, dict):
        return "generic"
    if "runs" in data and isinstance(data.get("runs"), list):
        return "sarif"
    if "results" in data and isinstance(data.get("results"), list):
        return "semgrep"
    return "generic"


def parse(data, scanner_type=None):
    """Parse scan data into normalized results. Auto-detects format if scanner_type not given."""
    if scanner_type is None or scanner_type == "generic":
        scanner_type = detect_format(data)

    if scanner_type == "sarif":
        return parse_sarif(data), "sarif"
    else:
        return parse_semgrep(data), "semgrep"
