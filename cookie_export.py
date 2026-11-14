"""Explicit, private-at-creation export of synthetic or user-owned browser cookies."""

from __future__ import annotations

import json
import os
from pathlib import Path

from stealth_browser.file_security import restrict_private_file


def persist_cookie_export(cookies: list[dict], output: Path | None) -> Path | None:
    """Keep cookies in memory unless a caller explicitly supplies a new file path.

    The parent directory and exported file are restricted on both POSIX and Windows.
    Existing destinations are never overwritten.
    """
    if output is None:
        return None

    requested = Path(output).expanduser()
    requested.parent.mkdir(parents=True, exist_ok=True)
    destination = requested
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(cookies, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        restrict_private_file(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination
