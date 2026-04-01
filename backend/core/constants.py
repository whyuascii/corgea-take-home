import ipaddress
import os

def _env_int(name, default):
    """Read an integer from the environment, falling back to *default*."""
    return int(os.environ.get(name, default))

MAX_UPLOAD_BYTES = _env_int("MAX_UPLOAD_BYTES", 50 * 1024 * 1024)  # 50 MB
MAX_SCAN_RESULTS = _env_int("MAX_SCAN_RESULTS", 500_000)
JSON_MAX_NESTING_DEPTH = _env_int("JSON_MAX_NESTING_DEPTH", 64)
HISTORY_BATCH_SIZE = _env_int("HISTORY_BATCH_SIZE", 2_000)

MAX_RULE_ID_LEN = _env_int("MAX_RULE_ID_LEN", 512)
MAX_PATH_LEN = _env_int("MAX_PATH_LEN", 1_024)
MAX_MESSAGE_LEN = _env_int("MAX_MESSAGE_LEN", 10_000)
MAX_SNIPPET_LEN = _env_int("MAX_SNIPPET_LEN", 20_000)
MAX_SEVERITY_LEN = _env_int("MAX_SEVERITY_LEN", 32)

MAX_REASON_LENGTH = _env_int("MAX_REASON_LENGTH", 5_000)
MAX_COMMENT_LENGTH = _env_int("MAX_COMMENT_LENGTH", 10_000)
MAX_NOTES_LENGTH = _env_int("MAX_NOTES_LENGTH", 5_000)

SLA_BATCH_SIZE = _env_int("SLA_BATCH_SIZE", 1_000)
BULK_OPERATION_LIMIT = _env_int("BULK_OPERATION_LIMIT", 1_000)

CACHE_TTL_PROJECT = _env_int("CACHE_TTL_PROJECT", 60)
CACHE_TTL_OVERVIEW = _env_int("CACHE_TTL_OVERVIEW", 120)
CACHE_TTL_VERSION = _env_int("CACHE_TTL_VERSION", 86_400)  # 24 hours

MAX_EXPORT_ROWS = _env_int("MAX_EXPORT_ROWS", 50_000)
OVERVIEW_RULES_LIMIT = _env_int("OVERVIEW_RULES_LIMIT", 500)
OVERVIEW_BREAKDOWN_LIMIT = _env_int("OVERVIEW_BREAKDOWN_LIMIT", 5_000)
TOP_RULES_LIMIT = _env_int("TOP_RULES_LIMIT", 10)
TOP_OWASP_LIMIT = _env_int("TOP_OWASP_LIMIT", 10)
RECENT_SCANS_LIMIT = _env_int("RECENT_SCANS_LIMIT", 10)
DB_ITERATOR_CHUNK_SIZE = _env_int("DB_ITERATOR_CHUNK_SIZE", 2_000)

SEARCH_QUERY_MIN_LEN = _env_int("SEARCH_QUERY_MIN_LEN", 2)
SEARCH_QUERY_MAX_LEN = _env_int("SEARCH_QUERY_MAX_LEN", 200)
DEFAULT_TREND_DAYS = _env_int("DEFAULT_TREND_DAYS", 30)
MAX_TREND_DAYS = _env_int("MAX_TREND_DAYS", 365)

SCAN_PUSH_RATE_LIMIT = _env_int("SCAN_PUSH_RATE_LIMIT", 100)
SCAN_PUSH_RATE_WINDOW = _env_int("SCAN_PUSH_RATE_WINDOW", 3_600)  # 1 hour
SYNC_TICKET_FALLBACK_LIMIT = _env_int("SYNC_TICKET_FALLBACK_LIMIT", 10)

DATA_RETENTION_DAYS = _env_int("DATA_RETENTION_DAYS", 90)

Q_TASK_TIMEOUT = _env_int("Q_TASK_TIMEOUT", 120)
Q_TASK_RETRY = _env_int("Q_TASK_RETRY", 180)

MAX_LOGIN_ATTEMPTS = _env_int("MAX_LOGIN_ATTEMPTS", 5)
LOCKOUT_WINDOW_MINUTES = _env_int("LOCKOUT_WINDOW_MINUTES", 15)
PASSWORD_RESET_EXPIRY_HOURS = _env_int("PASSWORD_RESET_EXPIRY_HOURS", 1)
LOGIN_ATTEMPT_RETENTION_HOURS = _env_int("LOGIN_ATTEMPT_RETENTION_HOURS", 24)
PASSWORD_MIN_LENGTH = _env_int("PASSWORD_MIN_LENGTH", 10)

INTEGRATION_API_TIMEOUT = _env_int("INTEGRATION_API_TIMEOUT", 15)
INTEGRATION_CREATE_TIMEOUT = _env_int("INTEGRATION_CREATE_TIMEOUT", 30)

ALLOWED_EXTENSIONS = {".json", ".sarif"}
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/octet-stream",
    "text/plain",
}

VALID_SCANNER_TYPES = {"semgrep", "sarif", "generic"}
VALID_BULK_ACTIONS = {"status_change", "false_positive"}

SARIF_SEVERITY_MAP = {
    "error": "ERROR",
    "warning": "WARNING",
    "note": "INFO",
    "none": "INFO",
}

LINEAR_API_URL = "https://api.linear.app/graphql"

BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::/128"),
]
