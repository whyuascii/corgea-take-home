from rest_framework.decorators import api_view
from rest_framework.response import Response

from .helpers import get_project_for_user


@api_view(["GET"])
def ci_snippets(request, project_slug):
    """Return ready-to-use CI/CD configuration snippets for GitHub Actions, CircleCI, GitLab CI, and shell."""
    project = get_project_for_user(request, project_slug)
    base_url = request.build_absolute_uri('/').rstrip('/')

    snippets = {
        "github_actions": f"""name: Semgrep Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Semgrep
        run: pip install semgrep
      - name: Run Semgrep
        run: semgrep --config auto --json . > results.json
      - name: Push to VulnTracker
        run: |
          curl -sf -X POST {base_url}/api/projects/{project.slug}/scans/push/ \\
            -H "Authorization: Api-Key {project.api_key}" \\
            -H "Content-Type: application/json" \\
            -d @results.json""",

        "circleci": f"""version: 2.1
jobs:
  semgrep-scan:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run: pip install semgrep
      - run: semgrep --config auto --json . > results.json
      - run: |
          curl -sf -X POST {base_url}/api/projects/{project.slug}/scans/push/ \\
            -H "Authorization: Api-Key {project.api_key}" \\
            -H "Content-Type: application/json" \\
            -d @results.json
workflows:
  security:
    jobs:
      - semgrep-scan""",

        "gitlab_ci": f"""semgrep-scan:
  image: python:3.12-slim
  stage: test
  script:
    - pip install semgrep
    - semgrep --config auto --json . > results.json
    - |
      curl -sf -X POST {base_url}/api/projects/{project.slug}/scans/push/ \\
        -H "Authorization: Api-Key {project.api_key}" \\
        -H "Content-Type: application/json" \\
        -d @results.json
  only:
    - main
    - merge_requests""",

        "shell": f"""#!/bin/bash
set -e
semgrep --config auto --json . > /tmp/results.json
curl -sf -X POST {base_url}/api/projects/{project.slug}/scans/push/ \\
  -H "Authorization: Api-Key {project.api_key}" \\
  -H "Content-Type: application/json" \\
  -d @/tmp/results.json
echo "Scan pushed to VulnTracker!\"""",
    }
    return Response(snippets)
