import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


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
