from __future__ import annotations

import asyncio
import logging
from functools import wraps

from mcp.server.fastmcp import FastMCP
from playwright.async_api import Locator, Page

from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.errors import RefStale
from stealth_browser.humanize import HumanBehavior
from stealth_browser.page_ops import evaluate, extract_text, get_cookies, screenshot_b64
from stealth_browser.session import load_cookies, save_cookies
from stealth_browser.snapshot import RefElement, take_snapshot

logger = logging.getLogger(__name__)

mcp = FastMCP("stealth-browser")

_manager: BrowserManager | None = None
_human: HumanBehavior | None = None
_last_refs: list[RefElement] = []
_lock = asyncio.Lock()


def _mcp_tool(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            logger.error("%s failed: %s", fn.__name__, e, exc_info=True)
            return {"error": str(e), "tool": fn.__name__}
    return wrapper


async def _ensure_browser() -> tuple[BrowserManager, Page, HumanBehavior]:
    global _manager, _human
    async with _lock:
        if _manager is None:
            cfg = BrowserConfig.from_env()
            _manager = BrowserManager(cfg)
            await _manager.__aenter__()
            _human = HumanBehavior(cfg)
    page = await _manager.get_page()
    return _manager, page, _human


async def _auto_snapshot(page: Page) -> dict:
    global _last_refs
    async with _lock:
        snap = await take_snapshot(page)
        _last_refs = snap.refs
    return snap.to_dict()


def _resolve_ref(page: Page, ref: int) -> Locator:
    if ref < 0 or ref >= len(_last_refs):
        raise RefStale(f"ref {ref} out of range (have {len(_last_refs)} refs)")
    element = _last_refs[ref]
    if element.label:
        safe_label = element.label.replace('"', '\\"')
        locator = page.locator(f'{element.tag}:has-text("{safe_label}")').first
    else:
        locator = page.locator(element.tag).first
    return locator


@mcp.tool()
@_mcp_tool
async def browser_open(url: str) -> dict:
    """Navigate to a URL and return a snapshot of the page with all interactive elements."""
    _, page, _ = await _ensure_browser()
    await page.goto(url)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_snapshot(include_screenshot: bool = False) -> dict:
    """Take a snapshot of the current page. Returns all interactive elements with ref indices, page title, URL, and markdown content. Set include_screenshot=True to also get a base64 PNG."""
    _, page, _ = await _ensure_browser()
    snap = await take_snapshot(page, include_screenshot=include_screenshot)
    async with _lock:
        global _last_refs
        _last_refs = snap.refs
    return snap.to_dict()


@mcp.tool()
@_mcp_tool
async def browser_screenshot() -> dict:
    """Capture a full-page screenshot as a base64-encoded PNG string."""
    _, page, _ = await _ensure_browser()
    return {"image": await screenshot_b64(page)}


@mcp.tool()
@_mcp_tool
async def browser_navigate_back() -> dict:
    """Navigate back in the browser history and return a snapshot of the resulting page."""
    _, page, _ = await _ensure_browser()
    await page.go_back()
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_refresh() -> dict:
    """Reload the current page and return a fresh snapshot."""
    _, page, _ = await _ensure_browser()
    await page.reload()
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_click(ref: int) -> dict:
    """Click an interactive element identified by its ref index from the last snapshot. Returns an updated snapshot."""
    _, page, human = await _ensure_browser()
    locator = _resolve_ref(page, ref)
    await human.click(page, locator)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_type(ref: int, text: str, clear_first: bool = True) -> dict:
    """Type text into an input element identified by its ref index. Clicks the element first, optionally clears existing content, then types with human-like timing. Returns an updated snapshot."""
    _, page, human = await _ensure_browser()
    locator = _resolve_ref(page, ref)
    await human.click(page, locator)
    if clear_first:
        await locator.clear()
    await human.type_text(page, text)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_select(ref: int, value: str) -> dict:
    """Select an option by value in a <select> element identified by its ref index. Returns an updated snapshot."""
    _, page, _ = await _ensure_browser()
    locator = _resolve_ref(page, ref)
    await locator.select_option(value)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_hover(ref: int) -> dict:
    """Hover over an element identified by its ref index. Useful for triggering tooltips or dropdown menus. Returns an updated snapshot."""
    _, page, human = await _ensure_browser()
    locator = _resolve_ref(page, ref)
    await human.hover(page, locator)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_scroll(direction: str = "down", pixels: int = 300) -> dict:
    """Scroll the page up or down by the given number of pixels. direction must be 'up' or 'down'. Returns an updated snapshot."""
    _, page, human = await _ensure_browser()
    delta = pixels if direction == "down" else -pixels
    await human.scroll(page, delta)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_press_key(key: str) -> dict:
    """Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown'). Returns an updated snapshot."""
    _, page, _ = await _ensure_browser()
    await page.keyboard.press(key)
    return await _auto_snapshot(page)


@mcp.tool()
@_mcp_tool
async def browser_get_text() -> dict:
    """Extract the visible text content of the current page as markdown."""
    _, page, _ = await _ensure_browser()
    text = await extract_text(page)
    return {"markdown": text}


@mcp.tool()
@_mcp_tool
async def browser_get_cookies() -> dict:
    """Return all cookies for the current page context as a list of cookie objects."""
    _, page, _ = await _ensure_browser()
    cookies = await get_cookies(page)
    return {"cookies": cookies}


@mcp.tool()
@_mcp_tool
async def browser_evaluate(js: str) -> dict:
    """Execute arbitrary JavaScript in the page context and return the result."""
    _, page, _ = await _ensure_browser()
    result = await evaluate(page, js)
    return {"result": result}


@mcp.tool()
@_mcp_tool
async def browser_save_session(name: str = "default") -> dict:
    """Save current browser cookies to a named session file for later restoration."""
    _, page, _ = await _ensure_browser()
    cfg = BrowserConfig.from_env()
    path = cfg.profile_dir.parent / name / "cookies.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    await save_cookies(page, path)
    return {"path": str(path)}


@mcp.tool()
@_mcp_tool
async def browser_load_session(name: str = "default") -> dict:
    """Load cookies from a previously saved named session into the current browser context."""
    _, page, _ = await _ensure_browser()
    cfg = BrowserConfig.from_env()
    path = cfg.profile_dir.parent / name / "cookies.json"
    await load_cookies(page, path)
    return {"ok": True}


@mcp.tool()
@_mcp_tool
async def browser_close() -> dict:
    """Close the browser and reset internal state. Use before reinitializing with different settings."""
    global _manager, _human, _last_refs
    async with _lock:
        if _manager is not None:
            await _manager.close()
            _manager = None
            _human = None
            _last_refs = []
    return {"ok": True}


def run():
    mcp.run()


if __name__ == "__main__":
    run()
