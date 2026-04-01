import logging

from django_q.models import Schedule

logger = logging.getLogger(__name__)

PERIODIC_SCHEDULES = [
    {
        "name": "cleanup_login_attempts",
        "func": "accounts.tasks.cleanup_login_attempts",
        "schedule_type": Schedule.DAILY,
        "repeats": -1,  # run forever
    },
    {
        "name": "check_sla_breaches",
        "func": "findings.tasks.check_sla_breaches",
        "schedule_type": Schedule.HOURLY,
        "repeats": -1,
    },
    {
        "name": "cleanup_old_scans",
        "func": "scans.tasks.cleanup_old_scans",
        "schedule_type": Schedule.DAILY,
        "repeats": -1,
    },
]


def register_schedules():
    """Create or update all periodic schedules and remove stale ones."""
    registered_names = set()

    for spec in PERIODIC_SCHEDULES:
        name = spec["name"]
        Schedule.objects.update_or_create(
            name=name,
            defaults={
                "func": spec["func"],
                "schedule_type": spec["schedule_type"],
                "repeats": spec["repeats"],
            },
        )
        registered_names.add(name)

    stale = Schedule.objects.filter(name__isnull=False).exclude(name__in=registered_names)
    stale_count, _ = stale.delete()
    if stale_count:
        logger.info("Removed %d stale scheduled task(s)", stale_count)

    logger.info("Registered %d periodic schedule(s)", len(registered_names))
