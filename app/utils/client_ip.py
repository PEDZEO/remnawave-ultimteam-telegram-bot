"""Trusted proxy-aware client IP extraction."""

from ipaddress import ip_address, ip_network

from starlette.requests import Request


_TRUSTED_PROXY_NETWORKS = (
    ip_network('10.0.0.0/8'),
    ip_network('127.0.0.0/8'),
    ip_network('169.254.0.0/16'),
    ip_network('172.16.0.0/12'),
    ip_network('192.168.0.0/16'),
    ip_network('::1/128'),
    ip_network('fc00::/7'),
    ip_network('fe80::/10'),
)


def _is_trusted_proxy_address(value) -> bool:
    return any(value in network for network in _TRUSTED_PROXY_NETWORKS if value.version == network.version)


def get_trusted_client_ip(request: Request) -> str:
    """Return the right-most untrusted hop, ignoring spoofed forwarded prefixes."""
    direct_ip = request.client.host if request.client else 'unknown'
    try:
        direct_address = ip_address(direct_ip)
    except ValueError:
        return direct_ip

    if not _is_trusted_proxy_address(direct_address):
        return str(direct_address)

    forwarded_addresses = []
    for candidate in request.headers.get('x-forwarded-for', '').split(','):
        try:
            forwarded_addresses.append(ip_address(candidate.strip()))
        except ValueError:
            continue

    for candidate in reversed(forwarded_addresses):
        if not _is_trusted_proxy_address(candidate):
            return str(candidate)

    return str(forwarded_addresses[0]) if forwarded_addresses else str(direct_address)
