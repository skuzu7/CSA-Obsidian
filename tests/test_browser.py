import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from stealth_browser.config import BrowserConfig


def test_browser_manager_init_defaults():
    from stealth_browser.browser import BrowserManager
    bm = BrowserManager()
    assert bm._cfx is None
    assert bm._context is None
    assert bm._chrome_cookies == []


def test_browser_manager_init_with_config():
    from stealth_browser.browser import BrowserManager
    cfg = BrowserConfig(headless=True)
    bm = BrowserManager(cfg)
    assert bm._config is cfg


def test_context_raises_if_not_entered():
    from stealth_browser.browser import BrowserManager
    bm = BrowserManager()
    with pytest.raises(RuntimeError, match="context manager"):
        _ = bm.context


async def test_close_calls_aexit():
    from stealth_browser.browser import BrowserManager
    bm = BrowserManager()

    mock_cfx = AsyncMock()
    bm._cfx = mock_cfx

    await bm.close()
    mock_cfx.__aexit__.assert_called_once_with(None, None, None)
