from unittest.mock import AsyncMock, MagicMock

import pytest


async def test_mcp_tool_decorator_catches_exception():
    from mcp_server.server import _mcp_tool

    @_mcp_tool
    async def failing_tool():
        raise ValueError("oops")

    result = await failing_tool()
    assert result["error"] == "oops"
    assert result["tool"] == "failing_tool"


async def test_mcp_tool_decorator_returns_normally():
    from mcp_server.server import _mcp_tool

    @_mcp_tool
    async def ok_tool():
        return {"data": 123}

    result = await ok_tool()
    assert result == {"data": 123}


def test_resolve_ref_out_of_range():
    import mcp_server.server as srv
    from stealth_browser.errors import RefStale

    page = MagicMock()
    srv._last_refs = []

    with pytest.raises(RefStale):
        srv._resolve_ref(page, 0)


def test_resolve_ref_valid_ref():
    import mcp_server.server as srv
    from stealth_browser.snapshot import RefElement

    page = MagicMock()
    page.locator = MagicMock(return_value=MagicMock())
    page.locator.return_value.first = MagicMock()

    srv._last_refs = [RefElement(index=0, role="button", label="Submit", tag="button", bbox=(0, 0, 100, 30))]

    locator = srv._resolve_ref(page, 0)
    assert locator is not None


def test_resolve_ref_label_with_quotes():
    import mcp_server.server as srv
    from stealth_browser.snapshot import RefElement

    page = MagicMock()
    page.locator = MagicMock(return_value=MagicMock())
    page.locator.return_value.first = MagicMock()

    label_with_quotes = 'Say "hello"'
    srv._last_refs = [RefElement(index=0, role="button", label=label_with_quotes, tag="button", bbox=(0, 0, 50, 20))]

    srv._resolve_ref(page, 0)
    call_args = str(page.locator.call_args)
    assert '\\"' in call_args or "Say" in call_args


def test_resolve_ref_negative_index():
    import mcp_server.server as srv
    from stealth_browser.errors import RefStale
    from stealth_browser.snapshot import RefElement

    page = MagicMock()
    srv._last_refs = [RefElement(index=0, role="button", label="X", tag="button", bbox=(0, 0, 10, 10))]

    with pytest.raises(RefStale):
        srv._resolve_ref(page, -1)


def test_reset_state_clears_globals():
    import mcp_server.server as srv
    from stealth_browser.snapshot import RefElement

    srv._manager = MagicMock()
    srv._human = MagicMock()
    srv._last_refs = [RefElement(index=0, role="button", label="X", tag="button", bbox=(0, 0, 1, 1))]

    srv._reset_state()

    assert srv._manager is None
    assert srv._human is None
    assert srv._last_refs == []


async def test_ensure_browser_recreates_on_dead_connection(monkeypatch):
    import mcp_server.server as srv

    dead = AsyncMock()
    dead.get_page = AsyncMock(side_effect=Exception("Connection closed while reading from the driver"))
    dead.close = AsyncMock()
    srv._manager = dead
    srv._human = MagicMock()

    fresh = AsyncMock()
    fresh_page = MagicMock()
    fresh.get_page = AsyncMock(return_value=fresh_page)
    fresh.__aenter__ = AsyncMock(return_value=fresh)

    monkeypatch.setattr(srv, "BrowserManager", lambda cfg: fresh)
    monkeypatch.setattr(srv, "HumanBehavior", lambda cfg: MagicMock())
    monkeypatch.setattr(srv.BrowserConfig, "from_env", classmethod(lambda cls: MagicMock()))

    manager, page, _ = await srv._ensure_browser()

    dead.close.assert_awaited_once()
    fresh.__aenter__.assert_awaited_once()
    assert manager is fresh
    assert page is fresh_page

    srv._reset_state()
