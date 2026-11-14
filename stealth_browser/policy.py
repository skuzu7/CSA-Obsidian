from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _normalize_hostname(host: str) -> str:
    host = host.rstrip(".").lower()
    if not host:
        raise ValueError("Host must not be empty")
    try:
        return ipaddress.ip_address(host).compressed
    except ValueError:
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError(f"Invalid hostname: {host!r}") from exc
        if len(ascii_host) > 253 or not all(\n            _LABEL.fullmatch(part) for part in ascii_host.split(".")\n        ):
            raise ValueError(f"Invalid hostname: {host!r}")
        return ascii_host


def normalize_host_rule(rule: str) -> str:
    """Normalize an exact host or *.domain rule, optionally with an explicit port."""
    if not isinstance(rule, str):
        raise ValueError("Allowed-host entries must be strings")
    raw = rule.strip()
    wildcard = raw.startswith("*.")
    authority = raw[2:] if wildcard else raw
    if not authority or "*" in authority or any(char in authority for char in "/?#@\\"):
        raise ValueError(f"Invalid allowed-host entry: {rule!r}")
    try:
        parsed = urlsplit("//" + authority)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"Invalid allowed-host entry: {rule!r}") from exc
    if not host or parsed.path or parsed.query or parsed.fragment or parsed.username is not None:
        raise ValueError(f"Invalid allowed-host entry: {rule!r}")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(f"Invalid port in allowed-host entry: {rule!r}")
    normalized = _normalize_hostname(host)
    try:
        is_ip = ipaddress.ip_address(normalized)
    except ValueError:
        is_ip = None
    if wildcard and is_ip is not None:
        raise ValueError("Wildcard entries must use a DNS hostname, not an IP address")
    if ":" in normalized:
        normalized = f"[{normalized}]"
    prefix = "*." if wildcard else ""
    return f"{prefix}{normalized}" + (f":{port}" if port is not None else "")


def parse_allowed_hosts(value: str | None) -> tuple[str, ...]:
    """Parse comma-separated exact hosts and optional *.subdomain rules."""
    if not value or not value.strip():
        return ()
    return tuple(\n        dict.fromkeys(normalize_host_rule(item) for item in value.split(",") if item.strip())\n    )


def is_url_allowed(url: str, allowed_hosts: tuple[str, ...] | list[str]) -> bool:
    """Fail closed unless an HTTP(S) URL matches an explicit host rule.

    A rule without a port allows only the scheme's default port. Use host:port
    for local development servers or other non-standard ports. about:blank,
    data:, and blob: are local browser resources and do not create network egress.
    """
    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        if scheme == "about":
            return parsed.path == "blank" and not parsed.netloc
        if scheme in {"data", "blob"}:
            return True
        if scheme not in {"http", "https"} or parsed.username is not None:
            return False
        host = parsed.hostname
        port = parsed.port
        if not host:
            return False
        normalized_host = _normalize_hostname(host)
    except (TypeError, ValueError):
        return False

    effective_port = port if port is not None else (443 if scheme == "https" else 80)
    for raw_rule in allowed_hosts:
        try:
            rule = normalize_host_rule(raw_rule)
            wildcard = rule.startswith("*.")
            authority = rule[2:] if wildcard else rule
            rule_parts = urlsplit("//" + authority)
            rule_host = rule_parts.hostname
            rule_port = rule_parts.port
        except (TypeError, ValueError):
            continue
        if not rule_host:
            continue
        normalized_rule_host = _normalize_hostname(rule_host)
        if rule_port is None:
            if effective_port != (443 if scheme == "https" else 80):
                continue
        elif effective_port != rule_port:
            continue
        if wildcard:
            if normalized_host.endswith("." + normalized_rule_host):
                return True
        elif normalized_host == normalized_rule_host:
            return True
    return False


def safe_origin(url: str) -> str:
    """Return scheme and authority without user-info, path, query, or fragment."""
    try:
        parsed = urlsplit(url)
        if not parsed.scheme or not parsed.hostname:
            return "[NON_HTTP_URL]"
        host = parsed.hostname
        if ":" in host:
            host = f"[{host}]"
        port = parsed.port
        authority = host + (f":{port}" if port is not None else "")
        return f"{parsed.scheme.lower()}://{authority}"
    except ValueError:
        return "[INVALID_URL]"
