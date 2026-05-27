import base64
from unittest.mock import AsyncMock

import pytest


async def test_screenshot_b64_calls_screenshot(mock_page):
    from stealth_browser.page_ops import screenshot_b64

    mock_page.screenshot = AsyncMock(return_value=b"PNG_DATA")
    result = await screenshot_b64(mock_page)

    expected = base64.b64encode(b"PNG_DATA").decode()
    assert result == expected
    mock_page.screenshot.assert_called_once()


async def test_navigate_raises_navigation_timeout(mock_page):
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    from stealth_browser.errors import NavigationTimeout
    from stealth_browser.page_ops import navigate

    mock_page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("timeout"))

    with pytest.raises(NavigationTimeout):
        await navigate(mock_page, "https://example.com")


async def test_navigate_non_timeout_exception_propagates(mock_page):
    from stealth_browser.page_ops import navigate

    mock_page.goto = AsyncMock(side_effect=ValueError("bad url"))

    with pytest.raises(ValueError):
        await navigate(mock_page, "not-a-url")


async def test_navigate_with_custom_timeout(mock_page):
    from stealth_browser.page_ops import navigate

    mock_page.goto = AsyncMock(return_value=None)
    await navigate(mock_page, "https://example.com", timeout=60_000)
    mock_page.goto.assert_called_once_with(
        "https://example.com", wait_until="domcontentloaded", timeout=60_000
    )


async def test_evaluate(mock_page):
    from stealth_browser.page_ops import evaluate
    mock_page.evaluate = AsyncMock(return_value=42)
    result = await evaluate(mock_page, "1+1")
    assert result == 42


async def test_get_cookies(mock_page):
    from stealth_browser.page_ops import get_cookies
    mock_page.context.cookies = AsyncMock(return_value=[{"name": "session", "value": "abc"}])
    cookies = await get_cookies(mock_page)
    assert len(cookies) == 1
    assert cookies[0]["name"] == "session"
