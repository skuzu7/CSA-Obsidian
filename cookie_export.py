"""Explicit, private-at-creation export of synthetic or user-owned browser cookies."""

from __future__ import annotations

import json
import os
from pathlib import Path

from stealth_browser.file_security import restrict_private_file


def persist_cookie_export(cookies: list[dict], output: Path | None) -> Path | None:
    """Keep cookies in memory unless a caller explicitly supplies a new file path.

    The exported file is restricted before any cookie values are written.
    Existing destinations are never overwritten and parent permissions are untouched.
    """
    if output is None:
        return None

    destination = Path(output).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(destination, flags, 0o600)
    try:
        # Apply the file DACL before writing secrets; never expose values under
        # inherited permissions from a user-selected shared destination folder.
        restrict_private_file(destination)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            fd = -1
            json.dump(cookies, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
    except Exception:
        if fd >= 0:
            os.close(fd)
        destination.unlink(missing_ok=True)
        raise
    return destination
