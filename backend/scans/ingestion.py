import logging

from django.db import transaction

from findings.models import Finding, FindingHistory, Rule

logger = logging.getLogger(__name__)


def ingest_scan(scan):
    report = scan.raw_report
    results = report.get("results", [])
    project = scan.project

    new_count = 0
    reopened_count = 0
    seen_finding_ids = set()
    ticket_candidates = []

    skipped_count = 0

    with transaction.atomic():
        for i, result in enumerate(results):
            if not isinstance(result, dict):
                logger.warning("Scan %s: result at index %d is not a dict, skipping", scan.id, i)
                skipped_count += 1
                continue

            rule_id = result.get("check_id", "")
            path = result.get("path", "")
            if not rule_id or not path:
                logger.warning(
                    "Scan %s: result at index %d missing check_id or path, skipping",
                    scan.id, i,
                )
                skipped_count += 1
                continue

            start_line = result.get("start", {}).get("line", 0)
            end_line = result.get("end", {}).get("line", 0)
            extra = result.get("extra", {})
            severity = extra.get("severity", "WARNING")
            message = extra.get("message", "")
            snippet = extra.get("lines", "")

            metadata_raw = extra.get("metadata", {})
            fix_suggestion = extra.get("fix", "")

            finding_metadata = {
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
                "fix": fix_suggestion,
            }

            rule, _ = Rule.objects.get_or_create(
                project=project,
                semgrep_rule_id=rule_id,
                defaults={"severity": severity, "message": message},
            )

            if rule.status == Rule.Status.IGNORED:
                continue

            finding, created = Finding.objects.get_or_create(
                project=project,
                rule=rule,
                file_path=path,
                line_start=start_line,
                line_end=end_line,
                defaults={
                    "code_snippet": snippet,
                    "metadata": finding_metadata,
                    "status": Finding.Status.NEW,
                    "first_seen_scan": scan,
                    "last_seen_scan": scan,
                },
            )

            if created:
                # Auto-propagate false positive status from cross-project FP rules
                existing_fp = Finding.objects.filter(
                    rule__semgrep_rule_id=rule_id,
                    project__owner=project.owner,
                    is_false_positive=True,
                ).exclude(id=finding.id).exists()
                if existing_fp:
                    finding.is_false_positive = True
                    finding.false_positive_reason = "Auto-propagated: rule marked as false positive"
                    finding.save(update_fields=["is_false_positive", "false_positive_reason"])

                new_count += 1
                FindingHistory.objects.create(
                    finding=finding,
                    scan=scan,
                    old_status="",
                    new_status=Finding.Status.NEW,
                )
                ticket_candidates.append(finding)
            else:
                finding.last_seen_scan = scan
                finding.code_snippet = snippet
                finding.metadata = finding_metadata

                if finding.is_false_positive:
                    finding.save(update_fields=["last_seen_scan", "code_snippet", "metadata", "updated_at"])
                    seen_finding_ids.add(finding.id)
                    continue

                if finding.status == Finding.Status.RESOLVED:
                    old_status = finding.status
                    finding.status = Finding.Status.REOPENED
                    reopened_count += 1
                    FindingHistory.objects.create(
                        finding=finding,
                        scan=scan,
                        old_status=old_status,
                        new_status=Finding.Status.REOPENED,
                    )
                    ticket_candidates.append(finding)
                elif finding.status == Finding.Status.NEW:
                    finding.status = Finding.Status.OPEN
                    FindingHistory.objects.create(
                        finding=finding,
                        scan=scan,
                        old_status=Finding.Status.NEW,
                        new_status=Finding.Status.OPEN,
                    )

                finding.save()

            seen_finding_ids.add(finding.id)

        active_statuses = [
            Finding.Status.NEW, Finding.Status.OPEN, Finding.Status.REOPENED,
        ]
        disappeared = Finding.objects.filter(
            project=project, status__in=active_statuses
        ).exclude(id__in=seen_finding_ids).exclude(is_false_positive=True)

        resolved_count = disappeared.count()
        for finding in disappeared:
            old_status = finding.status
            finding.status = Finding.Status.RESOLVED
            finding.save(update_fields=["status", "updated_at"])
            FindingHistory.objects.create(
                finding=finding,
                scan=scan,
                old_status=old_status,
                new_status=Finding.Status.RESOLVED,
            )

        scan.total_findings_count = len(results)
        scan.new_count = new_count
        scan.resolved_count = resolved_count
        scan.reopened_count = reopened_count
        scan.save(update_fields=[
            "total_findings_count", "new_count", "resolved_count", "reopened_count",
        ])

    # Create tickets after transaction commits — failures must not block the scan
    if ticket_candidates:
        try:
            from integrations.ticket_service import create_tickets_for_finding
            for finding in ticket_candidates:
                try:
                    create_tickets_for_finding(finding)
                except Exception:
                    logger.exception(
                        "Failed to create tickets for finding %s", finding.id
                    )
        except ImportError:
            pass

    summary = {
        "total": len(results),
        "new": new_count,
        "resolved": resolved_count,
        "reopened": reopened_count,
    }
    if skipped_count:
        summary["skipped"] = skipped_count
        summary["skipped_reason"] = "Malformed results missing required fields (check_id, path)"
    return summary
