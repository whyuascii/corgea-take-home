import ipaddress

def is_valid_ip(value):
    """Return True if *value* is a valid IPv4 or IPv6 address string."""
    try:
        ipaddress.ip_address(value)
        return True
    except (ValueError, TypeError):
        return False


def get_client_ip(request):
    """Extract the client IP from the request."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
        if is_valid_ip(candidate):
            return candidate

    remote = request.META.get("REMOTE_ADDR", "")
    if remote and is_valid_ip(remote):
        return remote
    return None
