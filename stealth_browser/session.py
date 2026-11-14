from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from stealth_browser.file_security import ensure_private_directory, restrict_private_file

logger = logging.getLogger(__name__)


def _write_private_json(path: Path, value: Any) -> None:
    """Atomically write sensitive session material with owner-only access."""
    parent = ensure_private_directory(path.parent)
    destination = parent / path.name
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=parent)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            fd = -1
            json.dump(value, file, indent=2, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        # Replacing a symlink replaces the link itself; it never writes through it.
        os.replace(temporary_name, destination)
        restrict_private_file(destination)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


async def save_cookies(page: Page, path: Path) -> None:
    cookies = await page.context.cookies()
    _write_private_json(path, cookies)
    logger.debug("Saved %d cookies to %s", len(cookies), path)


async def load_cookies(page: Page, path: Path) -> None:
    if not path.exists():
        logger.debug("Cookie file not found: %s", path)
        return
    ensure_private_directory(path.parent)
    restrict_private_file(path)
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
