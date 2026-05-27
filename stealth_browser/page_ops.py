from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

import trafilatura
from playwright.async_api import Locator, Page

from stealth_browser.errors import NavigationTimeout, ElementNotFound
from stealth_browser.humanize import HumanBehavior

logger = logging.getLogger(__name__)


async def navigate(page: Page, url: str, wait_until: str = "domcontentloaded") -> None:
    logger.debug("navigate → %s", url)
    try:
        await page.goto(url, wait_until=wait_until)
    except Exception as exc:
        if "Timeout" in type(exc).__name__:
            logger.warning("Navigation timeout: %s", url)
            raise NavigationTimeout(url) from exc
        raise


async def wait_for_selector(page: Page, selector: str, timeout: int = 10000) -> Locator:
    locator = page.locator(selector)
    try:
        await locator.wait_for(timeout=timeout)
    except Exception as exc:
        if "Timeout" in type(exc).__name__:
            raise ElementNotFound(selector) from exc
        raise
    return locator


async def screenshot(page: Page) -> bytes:
    return await page.screenshot()


async def screenshot_b64(page: Page) -> str:
    return base64.b64encode(await page.screenshot()).decode()


async def extract_text(page: Page) -> str:
    html = await page.content()
    result = await asyncio.to_thread(trafilatura.extract, html, output_format="markdown")
    return result or ""


async def get_cookies(page: Page) -> list[dict]:
    return await page.context.cookies()


async def set_cookies(page: Page, cookies: list[dict]) -> None:
    await page.context.add_cookies(cookies)


async def evaluate(page: Page, js: str) -> Any:
    return await page.evaluate(js)


async def fill(page: Page, selector: str, value: str, human: HumanBehavior | None = None) -> None:
    if human:
        locator = page.locator(selector)
        await locator.click()
        await locator.fill("")
        await human.type_text(page, value)
    else:
        await page.locator(selector).fill(value)


async def select_option(page: Page, selector: str, value: str) -> None:
    await page.locator(selector).select_option(value)
