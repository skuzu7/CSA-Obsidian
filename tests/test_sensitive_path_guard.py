"""Security regressions for protecting browser sessions in Git."""

import pytest

from scripts.check_sensitive_paths import is_sensitive_path


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "profiles/default/cookies.sqlite",
        "sessions/2026-11-15.json",
        "browser_profiles/operator/login.json",
        "user-data/Default/Network/Cookies",
        "cookie_dump.json",
        "exports/session_state.json",
        "tests/test-artifact.har",
        "keys/client.pem",
        "secrets/auth.p12",
        "debug.sqlite3",
        "windows\\profiles\\default\\Cookies",
    ],
)
def test_sensitive_runtime_files_are_blocked(path: str) -> None:
    assert is_sensitive_path(path)


@pytest.mark.parametrize(
    "path",
    [
        ".env.example",
        "stealth_browser/session.py",
        "stealth_browser/chrome_import.py",
        "tests/test_cookie_export.py",
        "docs/ASSURANCE_CASE.md",
        "README.md",
        "scripts/check_sensitive_paths.py",
    ],
)
def test_safe_source_and_template_paths_are_not_blocked(path: str) -> None:
    assert not is_sensitive_path(path)
