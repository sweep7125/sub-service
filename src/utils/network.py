"""Network-related utilities."""

from flask import Request


def get_client_ip(request: Request) -> str:
    """Get real client IP address from request.

    Handles reverse proxy headers (X-Forwarded-For, X-Real-IP) from nginx.
    Falls back to direct connection IP if headers are not present.

    Args:
        request: Flask request object

    Returns:
        Client IP address as string

    Example:
        >>> # Behind nginx with X-Forwarded-For: 203.0.113.1, 198.51.100.1
        >>> get_client_ip(request)
        '203.0.113.1'
    """
    # Priority 1: X-Forwarded-For (leftmost IP is the original client)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP from comma-separated list
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip

    # Priority 2: X-Real-IP (nginx specific)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Priority 3: Direct connection (no proxy)
    remote_addr = request.remote_addr
    return remote_addr if remote_addr else "unknown"
