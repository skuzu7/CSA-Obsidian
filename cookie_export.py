"""Explicit, private-at-creation export of synthetic or user-owned browser cookies."""

from __future__ import annotations

import json
import os
from pathlib import Path


def persist_cookie_export(cookies: list[dict], output: Path | None) -> Path | None:
    """Keep cookies in memory unless a caller explicitly supplies a new file path.

    On POSIX, creation is owner-only (0600). On Windows the parent directory's
    ACL can still affect access; do not treat filesystem mode as an ACL audit.
    """
    if output is None:
        return None

    destination = Path(output)
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(cookies, file, indent=2, ensure_ascii=False)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination
