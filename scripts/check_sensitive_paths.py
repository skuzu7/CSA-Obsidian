"""Reject committed browser state, secrets and session artifacts.

This is a repository *path* audit, not a secret-value scanner or proof that
sensitive content is absent from previous Git history.
Run: python -m scripts.check_sensitive_paths
"""

from __future__ import annotations

import subprocess
from pathlib import PurePosixPath

PRIVATE_DIRS = {
    "profiles",
    "sessions",
    "browser-profiles",
    "browser_profiles",
    "user-data",
    "user_data",
    "session-exports",
    "session_exports",
}
PRIVATE_FILES = {
    ".env",
    "cookies",
    "cookies.json",
    "cookies.txt",
    "cookies.sqlite",
    "cookie_dump.json",
    "storage_state.json",
    "storage-state.json",
    "session_state.json",
    "session-state.json",
    "login_state.json",
}
PRIVATE_EXTENSIONS = {".pem", ".p12", ".pfx", ".key", ".har", ".sqlite3"}


def is_sensitive_path(path: str) -> bool:
    """Conservative guard against tracked runtime material, not source code."""
    name = PurePosixPath(path.replace("\\", "/"))
    segments = [x.casefold() for x in name.parts]
    if not segments or segments[0] in {".", ".."}:
        return True
    if any(x in PRIVATE_DIRS for x in segments[:-1]):
        return True
    basename = segments[-1]
    if basename in PRIVATE_FILES:
        return True
    return PurePosixPath(basename).suffix in PRIVATE_EXTENSIONS


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    tracked = [
        x.decode("utf-8", errors="replace") for x in result.stdout.split(b"\0") if x
    ]
    blocked = sorted(p for p in tracked if is_sensitive_path(p))
    if blocked:
        print("ERROR: tracked files resemble browser-state or secret material:")
        for path in blocked:
            print(f" - {path}")
        print("Remove these files from tracking and investigate history/credential rotation.")
        return 1
    print(f"Path guard passed: {len(tracked)} tracked paths checked.")
    print("Does not scan contents, Git history, runtime files or third-party systems.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
