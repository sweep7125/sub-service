"""Network-related utilities."""

import ipaddress
from urllib.parse import urlparse

from flask import Request


def parse_dns_override(dns_string: str | None) -> tuple[str | None, str | None]:
    """Parse DNS override string into hostname and IP address.

    Handles both raw IP/hostnames and full URLs.

    Args:
        dns_string: DNS override string (hostname, IP, or URL)

    Returns:
        Tuple of (hostname, ip_address) where ip_address is None if hostname
        is not a valid IP address

    Example:
        >>> parse_dns_override("8.8.8.8")
        ('8.8.8.8', '8.8.8.8')
        >>> parse_dns_override("https://dns.google")
        ('dns.google', None)
    """
    if not dns_string:
        return None, None

    trimmed = dns_string.strip()
    parsed = urlparse(trimmed)

    # Extract hostname from URL or use string as-is
    hostname = parsed.hostname if (parsed.scheme and parsed.netloc) else trimmed

    if not hostname:
        return None, None

    # Try to parse as IP address
    try:
        ip_addr = ipaddress.ip_address(hostname)
        return hostname, str(ip_addr)
    except ValueError:
        return hostname, None


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
