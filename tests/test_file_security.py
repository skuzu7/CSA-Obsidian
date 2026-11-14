import os
import subprocess
from types import SimpleNamespace

import pytest

import stealth_browser.file_security as security


def test_posix_directory_is_owner_only(tmp_path):
    if os.name != "posix":
        pytest.skip("POSIX permissions are not Windows ACLs")
    import stat

    path = security.ensure_private_directory(tmp_path / "private")
    assert stat.S_IMODE(path.stat().st_mode) == 0o700


def test_windows_acl_grants_user_system_admin_and_removes_broad_groups(monkeypatch, tmp_path):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "whoami":
            return SimpleNamespace(
                stdout='"DOMAIN\\user","S-1-5-21-111-222-333-1001"\n'
            )
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(security, "_is_windows", lambda: True)
    monkeypatch.setattr(security.subprocess, "run", fake_run)

    path = security.ensure_private_directory(tmp_path / "profile")

    assert path.is_dir()
    assert len(calls) == 2 + len(security._RESTRICTED_GROUP_SIDS)
    grant = calls[1]
    assert "/inheritance:r" in grant
    assert "/T" in grant and "/C" in grant
    assert "*S-1-5-21-111-222-333-1001:(OI)(CI)F" in grant
    assert "*S-1-5-18:(OI)(CI)F" in grant
    assert "*S-1-5-32-544:(OI)(CI)F" in grant
    removed = {call[-1] for call in calls[2:]}
    assert removed == {f"*{sid}" for sid in security._RESTRICTED_GROUP_SIDS}
    assert all(call[0] in {"whoami", "icacls"} for call in calls)


def test_windows_acl_failure_fails_closed(monkeypatch, tmp_path):
    def fake_run(command, **kwargs):
        if command[0] == "whoami":
            return SimpleNamespace(stdout='"DOMAIN\\user","S-1-5-21-111-222-333-1001"\n')
        raise subprocess.CalledProcessError(1, command, stderr="Access denied")

    monkeypatch.setattr(security, "_is_windows", lambda: True)
    monkeypatch.setattr(security.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        security.ensure_private_directory(tmp_path / "profile")


def test_windows_acl_for_private_file(monkeypatch, tmp_path):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "whoami":
            return SimpleNamespace(stdout='"DOMAIN\\user","S-1-5-21-111-222-333-1001"\n')
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(security, "_is_windows", lambda: True)
    monkeypatch.setattr(security.subprocess, "run", fake_run)
    path = tmp_path / "cookies.json"
    path.write_text("{}", encoding="utf-8")

    security.restrict_private_file(path)

    assert len(calls) == 2 + len(security._RESTRICTED_GROUP_SIDS)
    grant = calls[1]
    assert "/inheritance:r" in grant
    assert "*S-1-5-21-111-222-333-1001:F" in grant
    assert "*S-1-5-18:F" in grant
    assert "*S-1-5-32-544:F" in grant


@pytest.mark.skipif(os.name != "nt", reason="Windows ACL integration test")
def test_windows_profile_and_cookie_acl_are_private(tmp_path):
    import os as os_module

    profile = security.ensure_private_directory(tmp_path / "browser-profile")
    cookie_file = profile / "cookies.json"
    cookie_file.write_text("{}", encoding="utf-8")
    security.restrict_private_file(cookie_file)

    sid = security._current_user_sid()
    script = (
        "$acl = Get-Acl -LiteralPath $env:ACL_TEST_PATH; "
        "$acl.Access | ForEach-Object { "
        "$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value "
        "}"
    )
    for path in (profile, cookie_file):
        env = os_module.environ.copy()
        env["ACL_TEST_PATH"] = str(path)
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
            env=env,
        )
        sids = set(result.stdout.split())
        assert sid in sids
        for group_sid in security._RESTRICTED_GROUP_SIDS:
            assert group_sid not in sids
