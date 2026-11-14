from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


def _write_private_json(path: Path, value: Any) -> None:
    """Write session material with owner-only POSIX permissions.

    O_NOFOLLOW prevents a pre-existing symlink from redirecting the write on
    platforms that support it. Windows ignores POSIX mode bits; its directory
    ACL remains the controlling access boundary.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            fd = -1
            json.dump(value, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


async def save_cookies(page: Page, path: Path) -> None:
    cookies = await page.context.cookies()
    _write_private_json(path, cookies)
    logger.debug("Saved %d cookies to %s", len(cookies), path)


async def load_cookies(page: Page, path: Path) -> None:
    if not path.exists():
        logger.debug("Cookie file not found: %s", path)
        return
    cookies = json.loads(path.read_text(encoding="utf-8"))
    await page.context.add_cookies(cookies)
    logger.debug("Loaded %d cookies from %s", len(cookies), path)


async def export_storage(page: Page, origin: str) -> dict[str, Any]:
    if not page.url.startswith(origin):
        await page.goto(origin, wait_until="commit")
    local = await page.evaluate("() => ({ ...localStorage })")
    session = await page.evaluate("() => ({ ...sessionStorage })")
    return {"localStorage": local, "sessionStorage": session}


async def import_storage(page: Page, origin: str, data: dict[str, Any]) -> None:
    if not page.url.startswith(origin):
        await page.goto(origin, wait_until="commit")
    await page.evaluate(
        "(d) => Object.entries(d).forEach(([k,v]) => localStorage.setItem(k,v))",
        data.get("localStorage", {}),
    )
    await page.evaluate(
        "(d) => Object.entries(d).forEach(([k,v]) => sessionStorage.setItem(k,v))",
        data.get("sessionStorage", {}),
    )
