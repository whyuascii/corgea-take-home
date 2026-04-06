import ipaddress
import os


# Number of trusted reverse proxies in front of the app.
# 0 = no proxy (ignore X-Forwarded-For entirely, use REMOTE_ADDR).
# 1 = one proxy (use rightmost XFF entry).
# In production behind a load balancer, set TRUSTED_PROXY_COUNT=1.
TRUSTED_PROXY_COUNT = int(os.environ.get("TRUSTED_PROXY_COUNT", "0"))


def is_valid_ip(value):
    """Return True if *value* is a valid IPv4 or IPv6 address string."""
    try:
        ipaddress.ip_address(value)
        return True
    except (ValueError, TypeError):
        return False


def get_client_ip(request):
    """Extract the client IP from the request.

    When TRUSTED_PROXY_COUNT > 0, uses the Nth-from-right entry in
    X-Forwarded-For (the rightmost entry added by the outermost trusted proxy).
    When TRUSTED_PROXY_COUNT == 0, ignores XFF entirely and uses REMOTE_ADDR
    to prevent spoofing.
    """
    if TRUSTED_PROXY_COUNT > 0:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",")]
            # The client IP is at index -(TRUSTED_PROXY_COUNT) from the right
            # because each proxy appends to the end.
            idx = len(parts) - TRUSTED_PROXY_COUNT
            if idx >= 0:
                candidate = parts[idx]
                if is_valid_ip(candidate):
                    return candidate

    remote = request.META.get("REMOTE_ADDR", "")
    if remote and is_valid_ip(remote):
        return remote
    return None
