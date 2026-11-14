import pytest

from stealth_browser.policy import (
    is_url_allowed,
    normalize_host_rule,
    parse_allowed_hosts,
    safe_origin,
)


def test_parse_allowed_hosts_normalizes_and_deduplicates():
    assert parse_allowed_hosts("EXAMPLE.com., *.Sub.Example.org, example.com") == (
        "example.com",
        "*.sub.example.org",
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        "https://example.com",
        "example.com/path",
        "user@example.com",
        "*.127.0.0.1",
        "example.com:99999",
        "bad host",
    ],
)
def test_normalize_host_rule_rejects_invalid_entries(value):
    with pytest.raises(ValueError):
        normalize_host_rule(value)


def test_empty_allowlist_denies_all_network_hosts():
    assert not is_url_allowed("https://example.com", ())
    assert not is_url_allowed("http://localhost:3000", ())


def test_exact_host_matches_only_default_web_ports():
    assert is_url_allowed("https://example.com/path", ("example.com",))
    assert is_url_allowed("http://example.com/path", ("example.com",))
    assert not is_url_allowed("https://example.com:8443/path", ("example.com",))


def test_explicit_port_matches_only_that_port():
    assert is_url_allowed("http://localhost:3000/health", ("localhost:3000",))
    assert not is_url_allowed("http://localhost:3001/health", ("localhost:3000",))
    assert not is_url_allowed("https://localhost:3000/health", ("localhost:3000",))


def test_wildcard_matches_subdomains_but_not_apex():
    assert is_url_allowed("https://api.example.com/v1", ("*.example.com",))
    assert is_url_allowed("https://deep.api.example.com", ("*.example.com",))
    assert not is_url_allowed("https://example.com", ("*.example.com",))
    assert not is_url_allowed("https://evil-example.com", ("*.example.com",))


def test_allowlist_normalizes_idna_and_ipv6():
    assert is_url_allowed("https://xn--bcher-kva.example", ("bücher.example",))
    assert is_url_allowed("http://[::1]:8080", ("[::1]:8080",))


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "https://user:password@example.com/",
        "https://example.com:8443/",
        "not a url",
    ],
)
def test_disallowed_schemes_userinfo_and_ports_are_blocked(url):
    assert not is_url_allowed(url, ("example.com",))


def test_local_browser_resource_schemes_do_not_create_network_egress():
    assert is_url_allowed("about:blank", ())
    assert is_url_allowed("data:text/plain,hello", ())
    assert is_url_allowed("blob:https://untrusted.example/123", ())
    assert not is_url_allowed("about:config", ())


def test_safe_origin_drops_credentials_paths_and_query_values():
    assert safe_origin(
        "https://user:password@example.com/private/path?token=secret#fragment"
    ) == "https://example.com"
