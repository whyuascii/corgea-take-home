"""Validators for integration configuration fields."""

import ipaddress
import socket
from urllib.parse import urlparse

from rest_framework.exceptions import ValidationError

from core.constants import BLOCKED_NETWORKS


def validate_external_url(url):
    """Validate that a URL resolves to a public (non-private) IP address.

    Prevents SSRF attacks by blocking requests to internal services,
    cloud metadata endpoints (169.254.x.x), and localhost.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise ValidationError("Invalid URL: no hostname found.")

    # Block schemes other than http/https
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("Only http and https URLs are allowed.")

    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValidationError(f"Cannot resolve hostname: {hostname}")

    for family, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        for network in BLOCKED_NETWORKS:
            if ip in network:
                raise ValidationError(
                    f"URL resolves to a private/internal IP address ({ip}). "
                    "Only public URLs are allowed for integrations."
                )
    return url
