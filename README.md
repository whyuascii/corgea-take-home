# Corgea Takehome project

---

## Problem Statement

We are frustrated with the way security vulnerabilities are tracked in our codebase. We run automated security scans using tools like Semgrep Community Edition with this command:

```bash
semgrep scan --config auto --json --json-output findings.json
```

which produce JSON reports of issues. Every time we scan, we need to go through all issues, even though the majority are false positives and can be ignored, and it's impossible to see which issues are recurring, who is responsible for addressing them, and whether any have been fixed or reopened.

We need a way to collect these findings, keep track of their status over time, assign them to team members, and maintain a history of changes so we can see when an issue was fixed, reopened, or reassigned. The current process makes it difficult for us to triage and manage security issues efficiently, and it's impacting our ability to maintain secure code.

---


## System Design

```mermaid
flowchart TB
    subgraph Clients
        Browser["Browser<br/>(React/Vite SPA)"]
        CI["CI/CD Pipeline"]
    end

    subgraph Backend["Backend :8000"]
        API["REST API (Django)"]
        Ingestion["Ingestion Pipeline"]
        TicketSvc["Ticket Service"]
    end

    subgraph DB["PostgreSQL :5432"]
        PG[(PostgreSQL 16)]
    end

    subgraph External["External Services"]
        Jira["Jira Cloud REST API"]
        Linear["Linear GraphQL API"]
    end

    Browser -->|"/api proxy"| API
    CI -->|"Api-Key auth"| API

    API --> Ingestion
    Ingestion --> PG
    Ingestion -->|"new + reopened"| TicketSvc

    TicketSvc -->|"create issue"| Jira
    TicketSvc -->|"create issue"| Linear

    Jira -->|"webhook"| API
    Linear -->|"webhook"| API

    API <-->|"CRUD"| PG
```

---

## Finding Lifecycle

```mermaid
flowchart TD
    Start(["Scan uploaded with findings"]) --> Each["For each finding in scan"]

    Each --> RuleCheck{"Rule ignored aka FP?"}
    RuleCheck -->|"Yes"| SkipRule["Skip finding"]

    RuleCheck -->|"No"| SeenBefore{"Seen this<br/>finding before?"}

    SeenBefore -->|"No, first time"| FPCheck{"Same rule marked FP<br/>in another project?"}
    FPCheck -->|"Yes"| AutoFP["Mark as FALSE POSITIVE<br/>(auto-propagated)"]
    FPCheck -->|"No"| MarkNew["Mark as NEW"]
    MarkNew --> NewTicket["Create ticket<br/>(if no active ticket exists)"]

    SeenBefore -->|"Yes, exists"| IsFP{"Marked as<br/>false positive?"}
    IsFP -->|"Yes"| UpdateOnly["Update snippet + metadata only<br/>(status frozen)"]

    IsFP -->|"No"| CurStatus{"Current status?"}
    CurStatus -->|"RESOLVED"| Reopen["Mark as REOPENED"]
    Reopen --> ReopenTicket["Create ticket<br/>(if no active ticket exists)"]
    CurStatus -->|"NEW"| Promote["Promote to OPEN"]
    CurStatus -->|"OPEN / REOPENED"| NoChange["Update snippet + metadata<br/>(status unchanged)"]

    style SkipRule fill:#6b7280,color:#fff
    style AutoFP fill:#a855f7,color:#fff
    style MarkNew fill:#3b82f6,color:#fff
    style NewTicket fill:#fbbf24,color:#000
    style UpdateOnly fill:#6b7280,color:#fff
    style Reopen fill:#f97316,color:#fff
    style ReopenTicket fill:#fbbf24,color:#000
    style Promote fill:#8b5cf6,color:#fff
    style NoChange fill:#6b7280,color:#fff
```

---


## Quick Start

### Prerequisites

- Docker and Docker Compose
- Ports 3000, 8000, and 5433 available

### Steps

```bash
# 1. Clone and start
git clone <repo-url>
cd corgea-take-home
docker compose up --build

# 2. Open http://localhost:3000 and register an account

# 3. Create a project, then upload a Semgrep JSON report

# 4. Or push from CI/CD:
semgrep scan --config auto --json --json-output results.json
curl -X POST http://localhost:8000/api/projects/<slug>/scans/push/ \
  -H "Authorization: Api-Key <your-project-api-key>" \
  -H "Content-Type: application/json" \
  -d @results.json
```

---
