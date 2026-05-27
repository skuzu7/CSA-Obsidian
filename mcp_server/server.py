from __future__ import annotations

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)
from playwright.async_api import Page, Locator

from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.humanize import HumanBehavior
from stealth_browser.snapshot import take_snapshot, RefElement
from stealth_browser.page_ops import (
    screenshot_b64,
    extract_text,
    get_cookies,
    evaluate,
)
from stealth_browser.session import save_cookies, load_cookies
from stealth_browser.errors import RefStale

mcp = FastMCP("stealth-browser")

_manager: BrowserManager | None = None
_human: HumanBehavior | None = None
_last_refs: list[RefElement] = []


async def _ensure_browser() -> tuple[BrowserManager, Page, HumanBehavior]:
    global _manager, _human
    if _manager is None:
        cfg = BrowserConfig.from_env()
        _manager = BrowserManager(cfg)
        await _manager.__aenter__()
        _human = HumanBehavior(cfg)
    page = await _manager.get_page()
    return _manager, page, _human


async def _auto_snapshot(page: Page) -> dict:
    global _last_refs
    snap = await take_snapshot(page)
    _last_refs = snap.refs
    return snap.to_dict()


def _resolve_ref(page: Page, ref: int) -> Locator:
    if ref < 0 or ref >= len(_last_refs):
        raise RefStale(f"ref {ref} out of range (have {len(_last_refs)} refs)")
    element = _last_refs[ref]
    if element.label:
        locator = page.locator(f'{element.tag}:has-text("{element.label}")').first
    else:
        locator = page.locator(element.tag).first
    return locator


@mcp.tool()
async def browser_open(url: str) -> dict:
    logger.debug("Tool called: browser_open url=%s", url)
    try:
        _, page, _ = await _ensure_browser()
        await page.goto(url)
        return await _auto_snapshot(page)
    except Exception as e:
        logger.error("browser_open failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_snapshot(include_screenshot: bool = False) -> dict:
    try:
        _, page, _ = await _ensure_browser()
        global _last_refs
        snap = await take_snapshot(page, include_screenshot=include_screenshot)
        _last_refs = snap.refs
        return snap.to_dict()
    except Exception as e:
        logger.error("browser_snapshot failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_screenshot() -> dict:
    try:
        _, page, _ = await _ensure_browser()
        return {"image": await screenshot_b64(page)}
    except Exception as e:
        logger.error("browser_screenshot failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_navigate_back() -> dict:
    try:
        _, page, _ = await _ensure_browser()
        await page.go_back()
        snap = await _auto_snapshot(page)
        return {"url": page.url, "title": await page.title(), "snapshot": snap}
    except Exception as e:
        logger.error("browser_navigate_back failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_refresh() -> dict:
    try:
        _, page, _ = await _ensure_browser()
        await page.reload()
        return await _auto_snapshot(page)
    except Exception as e:
        logger.error("browser_refresh failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_click(ref: int) -> dict:
    try:
        _, page, human = await _ensure_browser()
        locator = _resolve_ref(page, ref)
        await human.click(page, locator)
        return await _auto_snapshot(page)
    except Exception as e:
        logger.error("browser_click failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_type(ref: int, text: str, clear_first: bool = True) -> dict:
    try:
        _, page, human = await _ensure_browser()
        locator = _resolve_ref(page, ref)
        await human.click(page, locator)
        if clear_first:
            await locator.clear()
        await human.type_text(page, text)
        return await _auto_snapshot(page)
    except Exception as e:
        logger.error("browser_type failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_select(ref: int, value: str) -> dict:
    try:
        _, page, _ = await _ensure_browser()
        locator = _resolve_ref(page, ref)
        await locator.select_option(value)
        return await _auto_snapshot(page)
    except Exception as e:
        logger.error("browser_select failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_hover(ref: int) -> dict:
    try:
        _, page, human = await _ensure_browser()
        locator = _resolve_ref(page, ref)
        await human.hover(page, locator)
        return await _auto_snapshot(page)
    except Exception as e:
        logger.error("browser_hover failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_scroll(direction: str = "down", pixels: int = 300) -> dict:
    try:
        _, page, human = await _ensure_browser()
        delta = pixels if direction == "down" else -pixels
        await human.scroll(page, delta)
        return {"ok": True}
    except Exception as e:
        logger.error("browser_scroll failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_press_key(key: str) -> dict:
    try:
        _, page, _ = await _ensure_browser()
        await page.keyboard.press(key)
        return {"ok": True}
    except Exception as e:
        logger.error("browser_press_key failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_get_text() -> dict:
    try:
        _, page, _ = await _ensure_browser()
        text = await extract_text(page)
        return {"markdown": text}
    except Exception as e:
        logger.error("browser_get_text failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_get_cookies() -> dict:
    try:
        _, page, _ = await _ensure_browser()
        cookies = await get_cookies(page)
        return {"cookies": cookies}
    except Exception as e:
        logger.error("browser_get_cookies failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_evaluate(js: str) -> dict:
    try:
        _, page, _ = await _ensure_browser()
        result = await evaluate(page, js)
        return {"result": result}
    except Exception as e:
        logger.error("browser_evaluate failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_save_session(name: str = "default") -> dict:
    try:
        _, page, _ = await _ensure_browser()
        path = Path("profiles") / name / "cookies.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        await save_cookies(page, path)
        return {"path": str(path)}
    except Exception as e:
        logger.error("browser_save_session failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


@mcp.tool()
async def browser_load_session(name: str = "default") -> dict:
    try:
        _, page, _ = await _ensure_browser()
        path = Path("profiles") / name / "cookies.json"
        await load_cookies(page, path)
        return {"ok": True}
    except Exception as e:
        logger.error("browser_load_session failed: %s", e)
        return {"error": str(e), "type": type(e).__name__}


def run():
    mcp.run()


if __name__ == "__main__":
    run()
