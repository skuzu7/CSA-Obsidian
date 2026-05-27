from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def save_cookies(page: Page, path: Path) -> None:
    cookies = await page.context.cookies()
    path.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
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
