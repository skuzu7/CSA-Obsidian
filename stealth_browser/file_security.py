from __future__ import annotations

import csv
import os
import re
import subprocess
from pathlib import Path

_SID_PATTERN = re.compile(r"^S-1-\d+(?:-\d+){1,15}$")
# Broad principals must not retain inherited or explicit access to browser state.
_RESTRICTED_GROUP_SIDS = (
    "S-1-1-0",       # Everyone
    "S-1-5-32-545",  # Builtin Users
    "S-1-5-11",      # Authenticated Users
    "S-1-5-4",       # Interactive
    "S-1-5-14",      # Remote Interactive Logon
    "S-1-5-2",       # Network
)
_SYSTEM_SID = "S-1-5-18"
_ADMINISTRATORS_SID = "S-1-5-32-544"


def _is_windows() -> bool:
    return os.name == "nt"


def _current_user_sid() -> str:
    result = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    for row in csv.reader(result.stdout.splitlines()):
        for value in reversed(row):
            sid = value.strip()
            if _SID_PATTERN.fullmatch(sid):
                return sid
    raise RuntimeError("Could not determine the current Windows user SID")


def _run_icacls(path: Path, *, directory: bool) -> None:
    sid = _current_user_sid()
    inheritance = "(OI)(CI)F" if directory else "F"
    grants = [
        f"*{sid}:{inheritance}",
        f"*{_SYSTEM_SID}:{inheritance}",
        f"*{_ADMINISTRATORS_SID}:{inheritance}",
    ]
    command = ["icacls", str(path), "/inheritance:r", "/grant:r", *grants]
    if directory:
        command.extend(["/T", "/C"])
    subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)

    for group_sid in _RESTRICTED_GROUP_SIDS:
        command = ["icacls", str(path), "/remove:g", f"*{group_sid}"]
        if directory:
            command.extend(["/T", "/C"])
        subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)


def ensure_private_directory(path: Path) -> Path:
    """Create a directory and restrict it to the current user (plus OS admins/system)."""
    path = Path(path).expanduser()
    if path.is_symlink():
        raise OSError(f"Refusing to secure a symlink directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    resolved = path.resolve(strict=True)
    if _is_windows():
        _run_icacls(resolved, directory=True)
    else:
        os.chmod(resolved, 0o700)
    return resolved


def restrict_private_file(path: Path) -> None:
    """Restrict a sensitive file after an atomic write."""
    if path.is_symlink():
        raise OSError(f"Refusing to secure a symlink file: {path}")
    if _is_windows():
        _run_icacls(path, directory=False)
    else:
        os.chmod(path, 0o600)
