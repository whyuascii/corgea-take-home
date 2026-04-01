import logging

import requests
from django.db import IntegrityError, transaction
from django.utils import timezone

from core.constants import HISTORY_BATCH_SIZE, MAX_SCAN_RESULTS, SYNC_TICKET_FALLBACK_LIMIT
from findings.models import Finding, FindingHistory, Rule, SLAPolicy
from scans.parsers import parse

logger = logging.getLogger(__name__)


def get_or_create_finding(project, rule, path, start_line, end_line, defaults):
    """Atomic get-or-create with IntegrityError retry for concurrent scans."""
    try:
        return Finding.objects.get_or_create(
            project=project,
            rule=rule,
            file_path=path,
            line_start=start_line,
            line_end=end_line,
            defaults=defaults,
        )
    except IntegrityError:
        return (
            Finding.objects.get(
                project=project, rule=rule, file_path=path,
                line_start=start_line, line_end=end_line,
            ),
            False,
        )


def compute_sla_deadline(project, severity):
    """Look up SLA policy for this severity and return a deadline, or None."""
    try:
        from datetime import timedelta
        policy = SLAPolicy.objects.get(project=project, severity=severity)
        return timezone.now() + timedelta(hours=policy.max_resolution_hours)
    except (SLAPolicy.DoesNotExist, ValueError, TypeError):
        return None


def propagate_false_positive(finding, rule_id, project):
    """Auto-mark a finding as FP if the same rule is FP elsewhere for this owner."""

    is_fp_elsewhere = Finding.objects.filter(
        rule__semgrep_rule_id=rule_id,
        project__owner=project.owner,
        is_false_positive=True,
    ).exclude(id=finding.id).exists()

    if is_fp_elsewhere:
        finding.is_false_positive = True
        finding.false_positive_reason = "Auto-propagated: rule marked as false positive"
        finding.save(update_fields=["is_false_positive", "false_positive_reason"])


def resolve_disappeared_findings(project, seen_finding_ids, scan):
    """Bulk-resolve active findings that were not present in this scan."""
    active_statuses = [
        Finding.Status.NEW, Finding.Status.OPEN, Finding.Status.REOPENED,
    ]
    disappeared = (
        Finding.objects.select_for_update()
        .filter(project=project, status__in=active_statuses)
        .exclude(id__in=seen_finding_ids)
        .exclude(is_false_positive=True)
    )

    resolved_ids = list(disappeared.values_list("id", flat=True))
    if not resolved_ids:
        return resolved_ids

    Finding.objects.filter(id__in=resolved_ids).update(
        status=Finding.Status.RESOLVED,
    )

    resolve_history = [
        FindingHistory(
            finding_id=fid, scan=scan,
            old_status="", new_status=Finding.Status.RESOLVED,
        )
        for fid in resolved_ids
    ]
    FindingHistory.objects.bulk_create(resolve_history, batch_size=HISTORY_BATCH_SIZE)

    return resolved_ids


def dispatch_ticket_creation(ticket_candidates):
    """Enqueue ticket creation via django-q2, falling back to synchronous."""
    if not ticket_candidates:
        return

    try:
        from django_q.tasks import async_task
        for finding in ticket_candidates:
            async_task("integrations.tasks.create_tickets_async", str(finding.id))
    except (ImportError, requests.RequestException, ConnectionError, ValueError):
        logger.exception("Failed to enqueue ticket tasks — falling back to sync (limited to 10)")
        try:
            from integrations.ticket_service import create_tickets_for_finding
            for finding in ticket_candidates[:SYNC_TICKET_FALLBACK_LIMIT]:
                try:
                    create_tickets_for_finding(finding)
                except (requests.RequestException, ConnectionError, ValueError):
                    logger.exception("Failed to create tickets for finding %s", finding.id)
        except ImportError:
            pass


def dispatch_ticket_closure(resolved_finding_ids):
    """Enqueue ticket closure for resolved findings that have external tickets."""
    if not resolved_finding_ids:
        return

    from django.db.models import Q

    ticketed_findings = Finding.objects.filter(
        id__in=resolved_finding_ids,
    ).filter(
        Q(jira_ticket_id__gt="") | Q(linear_ticket_id__gt="")
    )

    ticketed_ids = list(ticketed_findings.values_list("id", flat=True))
    if not ticketed_ids:
        return

    try:
        from django_q.tasks import async_task
        for fid in ticketed_ids:
            async_task("integrations.tasks.close_tickets_async", str(fid))
    except (ImportError, requests.RequestException, ConnectionError, ValueError):
        logger.exception("Failed to enqueue ticket closure tasks — falling back to sync (limited to %d)", SYNC_TICKET_FALLBACK_LIMIT)
        try:
            from integrations.ticket_service import close_tickets_for_finding
            for finding in ticketed_findings[:SYNC_TICKET_FALLBACK_LIMIT]:
                try:
                    close_tickets_for_finding(finding)
                except (requests.RequestException, ConnectionError, ValueError):
                    logger.exception("Failed to close tickets for finding %s", finding.id)
        except ImportError:
            pass


def dispatch_notifications(scan, project, summary):
    """Fire-and-forget: email, WebSocket broadcast, cache invalidation."""
    try:
        from django_q.tasks import async_task
        async_task("scans.tasks.send_scan_notifications", str(scan.id))
    except (ImportError, ConnectionError, ValueError):
        logger.debug("Could not enqueue scan notification for scan %s", scan.id)

    try:
        from core.realtime import broadcast_scan_complete
        broadcast_scan_complete(project.slug, scan.id, summary)
    except (OSError, ConnectionError, RuntimeError):
        logger.debug("Could not broadcast scan complete for scan %s", scan.id)

    try:
        from core.cache import invalidate_project_cache
        invalidate_project_cache(project.id, project_slug=project.slug)
    except (ImportError, ConnectionError, OSError):
        logger.debug("Could not invalidate cache for project %s", project.id)

def _process_new_finding(finding, scan, nr, project, ticket_candidates, history_buffer):
    """Set up a newly created finding: FP propagation, SLA, history."""
    propagate_false_positive(finding, nr.check_id, project)

    sla_deadline = compute_sla_deadline(project, nr.severity)
    if sla_deadline:
        finding.sla_deadline = sla_deadline
        finding.save(update_fields=["sla_deadline"])

    history_buffer.append(
        FindingHistory(
            finding=finding, scan=scan,
            old_status="", new_status=Finding.Status.NEW,
        )
    )
    ticket_candidates.append(finding)


def _process_existing_finding(finding, scan, nr, ticket_candidates, history_buffer):
    """Update an existing finding: refresh metadata, handle lifecycle transitions."""
    finding.last_seen_scan = scan
    finding.code_snippet = nr.snippet
    finding.metadata = nr.metadata

    if finding.is_false_positive:
        finding.save(update_fields=["last_seen_scan", "code_snippet", "metadata", "updated_at"])
        return False

    reopened = False
    if finding.status == Finding.Status.RESOLVED:
        old_status = finding.status
        finding.status = Finding.Status.REOPENED
        reopened = True
        history_buffer.append(
            FindingHistory(
                finding=finding, scan=scan,
                old_status=old_status, new_status=Finding.Status.REOPENED,
            )
        )
        ticket_candidates.append(finding)
    elif finding.status == Finding.Status.NEW:
        finding.status = Finding.Status.OPEN
        history_buffer.append(
            FindingHistory(
                finding=finding, scan=scan,
                old_status=Finding.Status.NEW, new_status=Finding.Status.OPEN,
            )
        )

    finding.save()
    return reopened


def ingest_scan(scan):
    """Ingest a scan report: parse, deduplicate, transition statuses, dispatch side effects.

    Pipeline
    --------
    1. Parse raw report via format-specific parser (Semgrep / SARIF).
    2. For each result, get-or-create Rule and Finding (dedup by
       project + rule + file_path + line_start + line_end).
    3. New findings: propagate FP status, compute SLA deadline, queue tickets.
    4. Existing findings: RESOLVED → REOPENED, NEW → OPEN.
    5. Bulk-resolve findings not present in this scan.
    6. Dispatch side effects: tickets, email, WebSocket broadcast, cache invalidation.
    """
    report = scan.raw_report
    project = scan.project

    normalized_results, detected_type = parse(report, getattr(scan, "scanner_type", None))

    if scan.scanner_type in (None, "", "generic"):
        scan.scanner_type = detected_type

    truncated = len(normalized_results) > MAX_SCAN_RESULTS
    if truncated:
        logger.warning(
            "Scan %s: %d results exceed cap of %d — processing first %d only",
            scan.id, len(normalized_results), MAX_SCAN_RESULTS, MAX_SCAN_RESULTS,
        )
        normalized_results = normalized_results[:MAX_SCAN_RESULTS]

    new_count = 0
    reopened_count = 0
    seen_finding_ids = set()
    ticket_candidates = []
    history_buffer = []
    skipped_count = 0

    with transaction.atomic():
        for nr in normalized_results:
            if not nr.check_id or not nr.path:
                skipped_count += 1
                continue

            try:
                rule, _ = Rule.objects.get_or_create(
                    project=project,
                    semgrep_rule_id=nr.check_id,
                    defaults={"severity": nr.severity, "message": nr.message},
                )
            except IntegrityError:
                rule = Rule.objects.get(project=project, semgrep_rule_id=nr.check_id)

            if rule.status == Rule.Status.IGNORED:
                continue

            finding, created = get_or_create_finding(
                project, rule, nr.path, nr.line_start, nr.line_end,
                defaults={
                    "code_snippet": nr.snippet,
                    "metadata": nr.metadata,
                    "status": Finding.Status.NEW,
                    "first_seen_scan": scan,
                    "last_seen_scan": scan,
                },
            )

            if created:
                _process_new_finding(finding, scan, nr, project, ticket_candidates, history_buffer)
                new_count += 1
            else:
                reopened = _process_existing_finding(finding, scan, nr, ticket_candidates, history_buffer)
                if reopened:
                    reopened_count += 1

            seen_finding_ids.add(finding.id)

            if len(history_buffer) >= HISTORY_BATCH_SIZE:
                FindingHistory.objects.bulk_create(history_buffer)
                history_buffer.clear()

        if history_buffer:
            FindingHistory.objects.bulk_create(history_buffer)
            history_buffer.clear()

        resolved_ids = resolve_disappeared_findings(project, seen_finding_ids, scan)
        resolved_count = len(resolved_ids)

        scan.total_findings_count = len(normalized_results)
        scan.new_count = new_count
        scan.resolved_count = resolved_count
        scan.reopened_count = reopened_count
        scan.save(update_fields=[
            "total_findings_count", "new_count", "resolved_count", "reopened_count",
            "scanner_type",
        ])

    summary = {
        "total": len(normalized_results),
        "new": new_count,
        "resolved": resolved_count,
        "reopened": reopened_count,
    }
    if skipped_count:
        summary["skipped"] = skipped_count
        summary["skipped_reason"] = "Malformed results missing required fields (check_id, path)"
    if truncated:
        summary["truncated"] = True
        summary["truncated_reason"] = f"Report exceeded {MAX_SCAN_RESULTS} results; remainder was dropped"

    dispatch_ticket_creation(ticket_candidates)
    dispatch_ticket_closure(resolved_ids)
    dispatch_notifications(scan, project, summary)

    return summary
