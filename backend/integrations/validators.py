"""Validators and SSRF-safe HTTP utilities for integration configuration."""

import ipaddress
import socket
from urllib.parse import urlparse

from requests.adapters import HTTPAdapter
from urllib3.util.connection import allowed_gai_family

from rest_framework.exceptions import ValidationError

from core.constants import BLOCKED_NETWORKS


def _check_ip_blocked(ip_str):
    """Raise ValueError if the IP is in a blocked network."""
    ip = ipaddress.ip_address(ip_str)
    for network in BLOCKED_NETWORKS:
        if ip in network:
            raise ValueError(
                f"Blocked private/internal IP address: {ip}"
            )


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


class SSRFSafeAdapter(HTTPAdapter):
    """requests adapter that re-validates resolved IPs at connect time.

    This prevents DNS rebinding attacks where a hostname resolves to a
    public IP during validation but to a private IP when the actual
    HTTP request is made.
    """

    def send(self, request, *args, **kwargs):
        parsed = urlparse(request.url)
        hostname = parsed.hostname
        if hostname:
            try:
                resolved = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
            except socket.gaierror:
                raise ConnectionError(f"Cannot resolve hostname: {hostname}")

            for family, _, _, _, sockaddr in resolved:
                try:
                    _check_ip_blocked(sockaddr[0])
                except ValueError as e:
                    raise ConnectionError(str(e))

        return super().send(request, *args, **kwargs)
