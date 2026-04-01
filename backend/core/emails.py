import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _base_url():
    """Return the frontend base URL for building email links."""
    return getattr(settings, "VULNTRACKER_BASE_URL", "http://localhost:3000").rstrip("/")


def _send(*, subject, plain_body, html_body, recipient, context_label):
    """Send a single email, logging failures without raising."""
    try:
        send_mail(
            subject=subject,
            message=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_body,
        )
    except (SMTPException, ConnectionError, OSError):
        logger.exception("Failed to send %s email to %s", context_label, recipient)

def send_password_reset_email(user, token_str):
    """Send a password reset email with a one-time token link."""
    reset_url = f"{_base_url()}/reset-password?token={token_str}"
    _send(
        subject="VulnTracker — Password Reset",
        plain_body=f"Reset your password: {reset_url}",
        html_body=render_to_string("emails/password_reset.html", {
            "user": user,
            "reset_url": reset_url,
        }),
        recipient=user.email,
        context_label="password reset",
    )


def send_scan_complete_email(scan):
    """Send a scan-complete summary email to the project owner."""
    owner = scan.project.owner
    if not owner.email:
        return

    project = scan.project
    scan_url = f"{_base_url()}/projects/{project.slug}/scans/{scan.id}"
    _send(
        subject=f"VulnTracker — Scan complete for {project.name}",
        plain_body=(
            f"Scan complete for {project.name}: "
            f"{scan.new_count} new, {scan.resolved_count} resolved, "
            f"{scan.reopened_count} reopened."
        ),
        html_body=render_to_string("emails/scan_complete.html", {
            "project": project,
            "scan": scan,
            "scan_url": scan_url,
        }),
        recipient=owner.email,
        context_label="scan complete",
    )


def send_sla_breach_email(project, breached_findings):
    """Send an SLA breach notification to the project owner."""
    owner = project.owner
    if not owner.email:
        return

    dashboard_url = f"{_base_url()}/projects/{project.slug}/compliance"
    _send(
        subject=f"VulnTracker — SLA breach alert for {project.name}",
        plain_body=f"{len(breached_findings)} findings have breached their SLA in {project.name}.",
        html_body=render_to_string("emails/sla_breach.html", {
            "project": project,
            "findings": breached_findings,
            "dashboard_url": dashboard_url,
        }),
        recipient=owner.email,
        context_label="SLA breach",
    )
