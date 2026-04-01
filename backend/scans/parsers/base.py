"""Base data structures for normalized scan results."""

import posixpath
from dataclasses import dataclass, field

from core.constants import MAX_RULE_ID_LEN, MAX_PATH_LEN, MAX_MESSAGE_LEN, MAX_SNIPPET_LEN, MAX_SEVERITY_LEN


def normalize_path(path):
    """Normalize a file path for consistent deduplication.

    Strips scheme prefixes (file://), resolves .. components, and removes
    leading ./ to ensure consistent unique_together matching.
    """
    if not isinstance(path, str):
        return ""
    for prefix in ("file:///", "file://"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    path = posixpath.normpath(path)
    if path.startswith("./"):
        path = path[2:]
    # Reject absolute paths that look like filesystem traversal
    if path.startswith("/"):
        path = path.lstrip("/")
    return path


@dataclass
class NormalizedResult:
    check_id: str
    path: str
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0
    col_end: int = 0
    severity: str = "WARNING"
    message: str = ""
    snippet: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Truncate oversized string fields at the data-layer boundary."""
        self.check_id = self.check_id[:MAX_RULE_ID_LEN]
        self.path = self.path[:MAX_PATH_LEN]
        self.severity = self.severity[:MAX_SEVERITY_LEN]
        self.message = self.message[:MAX_MESSAGE_LEN]
        self.snippet = self.snippet[:MAX_SNIPPET_LEN]
