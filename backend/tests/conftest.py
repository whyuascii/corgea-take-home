import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from findings.models import Finding, Rule
from projects.membership import ProjectMembership
from projects.models import Project
from scans.ingestion import ingest_scan
from scans.models import Scan

User = get_user_model()

SAMPLE_SEMGREP_RESULTS = {
    "results": [
        {
            "check_id": "python.django.security.injection.sql-injection",
            "path": "app/views.py",
            "start": {"line": 42, "col": 1},
            "end": {"line": 42, "col": 50},
            "extra": {
                "severity": "ERROR",
                "message": "Possible SQL injection",
                "lines": "cursor.execute(query)",
                "metadata": {
                    "owasp": ["A03:2021"],
                    "cwe": ["CWE-89"],
                    "confidence": "HIGH",
                    "likelihood": "HIGH",
                    "impact": "HIGH",
                },
            },
        },
        {
            "check_id": "python.django.security.audit.missing-throttle",
            "path": "config/settings.py",
            "start": {"line": 67, "col": 1},
            "end": {"line": 67, "col": 30},
            "extra": {
                "severity": "WARNING",
                "message": "Missing throttle config",
                "lines": "REST_FRAMEWORK = {}",
                "metadata": {},
            },
        },
    ],
    "errors": [],
}


def get_results(response):
    """Extract results from response, handling both paginated and non-paginated formats."""
    data = response.json()
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    if isinstance(data, list):
        return data
    return data


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass1234",
    )


@pytest.fixture
def other_user(db):
    """Create a second test user for isolation tests."""
    return User.objects.create_user(
        username="otheruser",
        email="other@example.com",
        password="otherpass1234",
    )


@pytest.fixture
def auth_client(user):
    """APIClient authenticated with token."""
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def other_auth_client(other_user):
    """APIClient authenticated as a different user."""
    token, _ = Token.objects.get_or_create(user=other_user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def admin_user(db):
    """Create a test user with admin role for RBAC tests."""
    return User.objects.create_user(
        username="adminuser", email="admin@example.com", password="adminpass1234!",
    )


@pytest.fixture
def member_user(db):
    """Create a test user with member role for RBAC tests."""
    return User.objects.create_user(
        username="memberuser", email="member@example.com", password="memberpass1234!",
    )


@pytest.fixture
def viewer_user(db):
    """Create a test user with viewer role for RBAC tests."""
    return User.objects.create_user(
        username="vieweruser", email="viewer@example.com", password="viewerpass1234!",
    )


@pytest.fixture
def project(user):
    """Create a test project owned by the default user."""
    p = Project.objects.create(
        owner=user,
        name="Test Project",
        slug="test-project",
        description="A project for testing",
        repository_url="https://github.com/example/repo",
    )

    ProjectMembership.objects.get_or_create(
        project=p, user=user,
        defaults={"role": ProjectMembership.Role.OWNER},
    )
    return p


@pytest.fixture
def sample_semgrep_results():
    """Return a minimal valid semgrep results payload."""
    return SAMPLE_SEMGREP_RESULTS


@pytest.fixture
def scan_with_findings(project, sample_semgrep_results):
    """Create a scan and ingest findings, returning the scan."""
    scan = Scan.objects.create(
        project=project,
        source=Scan.Source.UPLOAD,
        raw_report=sample_semgrep_results,
    )
    ingest_scan(scan)
    scan.refresh_from_db()
    return scan


@pytest.fixture
def finding(scan_with_findings):
    """Return the first finding from the scan."""
    return Finding.objects.filter(
        project=scan_with_findings.project
    ).order_by("created_at").first()


@pytest.fixture
def rule(scan_with_findings):
    """Return the first rule from the scan."""
    return Rule.objects.filter(
        project=scan_with_findings.project
    ).order_by("created_at").first()
