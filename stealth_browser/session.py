from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.async_api import Page


async def save_cookies(page: Page, path: Path) -> None:
    cookies = await page.context.cookies()
    path.write_text(json.dumps(cookies, indent=2))


async def load_cookies(page: Page, path: Path) -> None:
    if not path.exists():
        return
    cookies = json.loads(path.read_text())
    await page.context.add_cookies(cookies)


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
