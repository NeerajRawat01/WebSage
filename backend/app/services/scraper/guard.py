import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException, status

from app.core.config import ALLOWED_SCHEMES, DISALLOW_PRIVATE_IPS


def _is_private_or_reserved_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_multicast
            or ip_obj.is_unspecified
        )
    except ValueError:
        return True


def validate_url_and_resolve(target_url: str) -> tuple[str, str]:
    """Validate scheme and resolve hostname; optionally block private IPs.

    Returns a tuple of (normalized_url, resolved_ip).
    Raises HTTPException 400/403 on invalid or disallowed targets.
    """
    parsed = urlparse(target_url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL scheme must be one of: {', '.join(sorted(ALLOWED_SCHEMES))}",
        )
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="URL must include hostname")

    hostname = parsed.hostname
    try:
        # Prefer IPv4; fall back to IPv6
        addr_info = socket.getaddrinfo(hostname, None)
        ip = next((ai[4][0] for ai in addr_info if ai[0] in (socket.AF_INET, socket.AF_INET6)), None)
        if not ip:
            raise RuntimeError("Could not resolve hostname")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not resolve target host")

    if DISALLOW_PRIVATE_IPS and _is_private_or_reserved_ip(ip):
        raise HTTPException(status_code=403, detail="Access to private/reserved IPs is disallowed")

    # Normalize URL (strip fragments)
    normalized = parsed._replace(fragment="").geturl()
    return normalized, ip


