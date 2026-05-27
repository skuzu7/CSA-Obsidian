from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from stealth_browser.config import BrowserConfig


@pytest.fixture
def cfg():
    return BrowserConfig()


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example Page")
    page.content = AsyncMock(return_value="<html><body>Hello</body></html>")
    page.screenshot = AsyncMock(return_value=b"\x89PNG\r\n")
    page.evaluate = AsyncMock(return_value=None)
    page.context = AsyncMock()
    page.context.cookies = AsyncMock(return_value=[])
    page.keyboard = AsyncMock()
    page.mouse = AsyncMock()
    return page
