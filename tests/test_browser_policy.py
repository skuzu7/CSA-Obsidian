from unittest.mock import AsyncMock, MagicMock

import pytest

from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig


@pytest.mark.asyncio
async def test_browser_route_blocks_non_allowlisted_origin():
    manager = BrowserManager(BrowserConfig(allowed_hosts=("example.com",)))
    route = MagicMock()
    route.request.url = "https://evil.example/private?token=secret"
    route.abort = AsyncMock()
    route.continue_ = AsyncMock()

    await manager._route_request(route)

    route.abort.assert_awaited_once_with("blockedbyclient")
    route.continue_.assert_not_awaited()


@pytest.mark.asyncio
async def test_browser_route_allows_matching_host_and_blocks_other_port():
    manager = BrowserManager(BrowserConfig(allowed_hosts=("localhost:3000",)))
    allowed = MagicMock()
    allowed.request.url = "http://localhost:3000/health"
    allowed.abort = AsyncMock()
    allowed.continue_ = AsyncMock()
    denied = MagicMock()
    denied.request.url = "http://localhost:3001/health"
    denied.abort = AsyncMock()
    denied.continue_ = AsyncMock()

    await manager._route_request(allowed)
    await manager._route_request(denied)

    allowed.continue_.assert_awaited_once()
    denied.abort.assert_awaited_once_with("blockedbyclient")


@pytest.mark.asyncio
async def test_browser_route_denies_external_requests_by_default():
    manager = BrowserManager(BrowserConfig())
    route = MagicMock()
    route.request.url = "https://example.com"
    route.abort = AsyncMock()
    route.continue_ = AsyncMock()

    await manager._route_request(route)

    route.abort.assert_awaited_once_with("blockedbyclient")
