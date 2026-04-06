import logging
from datetime import timedelta

import requests
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django_q.tasks import async_task

from core.cache import invalidate_project_cache
from core.constants import HISTORY_BATCH_SIZE, MAX_SCAN_RESULTS, SYNC_TICKET_FALLBACK_LIMIT, VALID_SEVERITIES
from core.realtime import broadcast_dashboard_update, broadcast_scan_complete, broadcast_scan_progress
from findings.models import Finding, FindingHistory, Rule, SLAPolicy
from integrations.ticket_service import close_tickets_for_finding, create_tickets_for_finding
from scans.parsers import parse

logger = logging.getLogger(__name__)


def get_or_create_finding(project, rule, path, start_line, end_line, defaults):
    """Atomic get-or-create with row lock on existing rows for concurrent scans."""
    try:
        finding, created = Finding.objects.get_or_create(
            project=project,
            rule=rule,
            file_path=path,
            line_start=start_line,
            line_end=end_line,
            defaults=defaults,
        )
    except IntegrityError:
        finding = (
            Finding.objects.select_for_update()
            .get(
                project=project, rule=rule, file_path=path,
                line_start=start_line, line_end=end_line,
            )
        )
        return finding, False

    if not created:
        # Re-fetch with a row lock so status transitions are safe
        finding = (
            Finding.objects.select_for_update()
            .get(pk=finding.pk)
        )

    return finding, created


def _prefetch_sla_policies(project):
    """Load all SLA policies for a project into a severity->hours map."""
    return dict(
        SLAPolicy.objects.filter(project=project)
        .values_list("severity", "max_resolution_hours")
    )


def _prefetch_fp_rule_ids(project):
    """Load rule IDs already marked as FP anywhere for this owner."""
    return set(
        Finding.objects.filter(
            project__owner=project.owner,
            is_false_positive=True,
        ).values_list("rule__semgrep_rule_id", flat=True)
    )


def compute_sla_deadline(sla_map, severity):
    """Return a deadline from the prefetched SLA map, or None."""
    hours = sla_map.get(severity)
    if hours is not None:
        return timezone.now() + timedelta(hours=hours)
    return None


def propagate_false_positive(finding, rule_id, fp_rule_ids):
    """Auto-mark a finding as FP if its rule is already FP elsewhere."""
    if rule_id in fp_rule_ids:
        finding.is_false_positive = True
        finding.false_positive_reason = "Auto-propagated: rule marked as false positive"


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

    disappeared.update(status=Finding.Status.RESOLVED)

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
        for finding in ticket_candidates:
            async_task("integrations.tasks.create_tickets_async", str(finding.id))
    except (ConnectionError, OSError, ValueError):
        logger.exception("Failed to enqueue ticket tasks — falling back to sync (limited to %d)", SYNC_TICKET_FALLBACK_LIMIT)
        for finding in ticket_candidates[:SYNC_TICKET_FALLBACK_LIMIT]:
            try:
                create_tickets_for_finding(finding)
            except (requests.RequestException, ConnectionError, ValueError):
                logger.exception("Failed to create tickets for finding %s", finding.id)


def dispatch_ticket_closure(resolved_finding_ids):
    """Enqueue ticket closure for resolved findings that have external tickets."""
    if not resolved_finding_ids:
        return

    ticketed_findings = Finding.objects.filter(
        id__in=resolved_finding_ids,
    ).filter(
        Q(jira_ticket_id__gt="") | Q(linear_ticket_id__gt="")
    )

    ticketed_ids = list(ticketed_findings.values_list("id", flat=True))
    if not ticketed_ids:
        return

    try:
        for fid in ticketed_ids:
            async_task("integrations.tasks.close_tickets_async", str(fid))
    except (ConnectionError, OSError, ValueError):
        logger.exception("Failed to enqueue ticket closure tasks — falling back to sync (limited to %d)", SYNC_TICKET_FALLBACK_LIMIT)
        for finding in ticketed_findings[:SYNC_TICKET_FALLBACK_LIMIT]:
            try:
                close_tickets_for_finding(finding)
            except (requests.RequestException, ConnectionError, ValueError):
                logger.exception("Failed to close tickets for finding %s", finding.id)


def dispatch_notifications(scan, project, summary):
    """Fire-and-forget: email, WebSocket broadcast, cache invalidation."""
    try:
        async_task("scans.tasks.send_scan_notifications", str(scan.id))
    except (ConnectionError, OSError, ValueError):
        logger.debug("Could not enqueue scan notification for scan %s", scan.id)

    try:
        broadcast_scan_complete(project.slug, scan.id, summary)
    except (OSError, ConnectionError, RuntimeError):
        logger.debug("Could not broadcast scan complete for scan %s", scan.id)

    try:
        broadcast_dashboard_update(str(project.owner_id), {
            "event": "scan_complete",
            "project_slug": project.slug,
            "scan_id": str(scan.id),
            "summary": summary,
        })
    except (OSError, ConnectionError, RuntimeError):
        logger.debug("Could not broadcast dashboard update for project %s", project.id)

    try:
        invalidate_project_cache(project.id, project_slug=project.slug)
    except (ConnectionError, OSError):
        logger.debug("Could not invalidate cache for project %s", project.id)


def _process_new_finding(finding, scan, nr, project, sla_map, fp_rule_ids,
                         ticket_candidates, history_buffer):
    """Set up a newly created finding: FP propagation, SLA, history."""
    propagate_false_positive(finding, nr.check_id, fp_rule_ids)

    sla_deadline = compute_sla_deadline(sla_map, nr.severity)
    if sla_deadline:
        finding.sla_deadline = sla_deadline

    history_buffer.append(
        FindingHistory(
            finding=finding, scan=scan,
            old_status="", new_status=Finding.Status.NEW,
        )
    )
    ticket_candidates.append(finding)


def _process_existing_finding(finding, scan, nr, ticket_candidates, history_buffer):
    """Update an existing finding: refresh metadata, handle lifecycle transitions.

    The caller must have locked the row via select_for_update() so that
    status reads and writes are serialised across concurrent scans.
    """
    finding.last_seen_scan = scan
    finding.code_snippet = nr.snippet
    finding.metadata = nr.metadata

    if finding.is_false_positive:
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

    return reopened


# Fields written by _process_new_finding / _process_existing_finding
_NEW_FINDING_UPDATE_FIELDS = [
    "is_false_positive", "false_positive_reason", "sla_deadline",
]
_EXISTING_FINDING_UPDATE_FIELDS = [
    "last_seen_scan", "code_snippet", "metadata", "status",
]


def _broadcast_progress(project_slug, scan_id, processed, total):
    """Send a WebSocket progress event (best-effort, outside transaction)."""
    try:
        broadcast_scan_progress(project_slug, {
            "event": "scan_progress",
            "scan_id": str(scan_id),
            "processed": processed,
            "total": total,
        })
    except (OSError, ConnectionError, RuntimeError):
        pass


def ingest_scan(scan):
    """Ingest a scan report: parse, deduplicate, transition statuses, dispatch side effects.

    Pipeline
    --------
    1. Parse raw report via format-specific parser (Semgrep / SARIF).
    2. For each result, get-or-create Rule and Finding (dedup by
       project + rule + file_path + line_start + line_end).
    3. New findings: propagate FP status, compute SLA deadline, queue tickets.
    4. Existing findings: RESOLVED -> REOPENED, NEW -> OPEN.
    5. Bulk-resolve findings not present in this scan.
    6. Dispatch side effects: tickets, email, WebSocket broadcast, cache invalidation.
    """
    report = scan.raw_report
    project = scan.project

    # -- Parse (outside transaction -- pure CPU, no DB writes) --
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

    # -- Prefetch lookups once (outside transaction -- read-only) --
    sla_map = _prefetch_sla_policies(project)
    fp_rule_ids = _prefetch_fp_rule_ids(project)

    new_count = 0
    reopened_count = 0
    seen_finding_ids = set()
    ticket_candidates = []
    history_buffer = []
    new_findings_to_update = []
    existing_findings_to_update = []
    skipped_count = 0
    total_results = len(normalized_results)
    processed_count = 0
    progress_events = []

    # -- All-or-nothing transaction --
    try:
        with transaction.atomic():
            for nr in normalized_results:
                if not nr.check_id or not nr.path:
                    skipped_count += 1
                    continue

                severity = nr.severity if nr.severity in VALID_SEVERITIES else "WARNING"
                try:
                    rule, _ = Rule.objects.get_or_create(
                        project=project,
                        semgrep_rule_id=nr.check_id,
                        defaults={"severity": severity, "message": nr.message},
                    )
                except IntegrityError:
                    rule = Rule.objects.select_for_update().get(
                        project=project, semgrep_rule_id=nr.check_id,
                    )

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
                    _process_new_finding(
                        finding, scan, nr, project, sla_map, fp_rule_ids,
                        ticket_candidates, history_buffer,
                    )
                    new_findings_to_update.append(finding)
                    new_count += 1
                else:
                    reopened = _process_existing_finding(
                        finding, scan, nr, ticket_candidates, history_buffer,
                    )
                    existing_findings_to_update.append(finding)
                    if reopened:
                        reopened_count += 1

                seen_finding_ids.add(finding.id)
                processed_count += 1

                if processed_count % 100 == 0 or processed_count == total_results:
                    progress_events.append((processed_count, total_results))

                if len(history_buffer) >= HISTORY_BATCH_SIZE:
                    FindingHistory.objects.bulk_create(history_buffer)
                    history_buffer.clear()

            # Flush remaining history
            if history_buffer:
                FindingHistory.objects.bulk_create(history_buffer)
                history_buffer.clear()

            # Bulk-update new findings (FP flag, SLA deadline)
            if new_findings_to_update:
                Finding.objects.bulk_update(
                    new_findings_to_update, _NEW_FINDING_UPDATE_FIELDS,
                    batch_size=HISTORY_BATCH_SIZE,
                )

            # Bulk-update existing findings (status, metadata, last_seen_scan)
            if existing_findings_to_update:
                Finding.objects.bulk_update(
                    existing_findings_to_update, _EXISTING_FINDING_UPDATE_FIELDS,
                    batch_size=HISTORY_BATCH_SIZE,
                )

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
    except Exception:
        logger.exception("Scan %s ingestion failed — transaction rolled back", scan.id)
        raise

    # -- Side effects: only after successful commit --

    # Deliver progress events that were queued during the transaction
    for processed, total in progress_events:
        _broadcast_progress(project.slug, scan.id, processed, total)

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
