import asyncio
from unittest.mock import MagicMock

import pytest


def make_page():
    page = MagicMock()
    page.on = MagicMock()
    page.remove_listener = MagicMock()
    return page


@pytest.fixture
def interceptor():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    return RequestInterceptor(page, url_pattern="*example.com*", header_names=["x-token"])


def test_attach_registers_listener(interceptor):
    interceptor.attach()
    interceptor._page.on.assert_called_once_with("request", interceptor._on_request)


def test_detach_removes_listener(interceptor):
    interceptor.attach()
    interceptor.detach()
    interceptor._page.remove_listener.assert_called_once_with("request", interceptor._on_request)


def test_captured_is_deque(interceptor):
    import collections
    assert isinstance(interceptor.captured, collections.deque)
    assert interceptor.captured.maxlen == 500


async def test_context_manager_attaches_and_detaches():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    async with RequestInterceptor(page) as ic:
        page.on.assert_called_once_with("request", ic._on_request)
    page.remove_listener.assert_called_once_with("request", ic._on_request)


def test_on_request_filters_by_url_pattern():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    ic = RequestInterceptor(page, url_pattern="*binance.com*")

    req_match = MagicMock()
    req_match.url = "https://api.binance.com/api/v3/ping"
    req_match.method = "GET"
    req_match.headers = {"x-token": "abc"}

    req_no_match = MagicMock()
    req_no_match.url = "https://google.com"
    req_no_match.method = "GET"
    req_no_match.headers = {}

    ic._on_request(req_match)
    ic._on_request(req_no_match)

    assert len(ic.captured) == 1
    assert ic.captured[0]["url"] == "https://api.binance.com/api/v3/ping"


def test_on_request_filters_by_header_names():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    ic = RequestInterceptor(page, url_pattern="*", header_names=["x-token"])

    req_with_header = MagicMock()
    req_with_header.url = "https://example.com"
    req_with_header.method = "GET"
    req_with_header.headers = {"x-token": "abc123", "content-type": "json"}

    req_without_header = MagicMock()
    req_without_header.url = "https://example.com/img"
    req_without_header.method = "GET"
    req_without_header.headers = {"content-type": "image/png"}

    ic._on_request(req_with_header)
    ic._on_request(req_without_header)

    assert len(ic.captured) == 1


async def test_wait_for_header_finds_existing():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    ic = RequestInterceptor(page)

    ic.captured.append({"url": "https://x.com", "method": "GET", "headers": {"x-token": "val123"}})
    ic._event.set()

    result = await ic.wait_for_header("x-token", timeout=1.0)
    assert result == "val123"


async def test_wait_for_header_case_insensitive():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    ic = RequestInterceptor(page)

    ic.captured.append({"url": "https://x.com", "method": "GET", "headers": {"X-Token": "ABC"}})
    ic._event.set()

    result = await ic.wait_for_header("x-token", timeout=1.0)
    assert result == "ABC"


async def test_wait_for_header_timeout():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    ic = RequestInterceptor(page)

    with pytest.raises(TimeoutError):
        await ic.wait_for_header("missing-header", timeout=0.05)


async def test_wait_for_header_triggered_by_event():
    from stealth_browser.intercept import RequestInterceptor
    page = make_page()
    ic = RequestInterceptor(page)

    async def inject_after_delay():
        await asyncio.sleep(0.05)
        ic.captured.append({"url": "https://x.com", "method": "GET", "headers": {"auth": "token42"}})
        ic._event.set()

    asyncio.create_task(inject_after_delay())
    result = await ic.wait_for_header("auth", timeout=1.0)
    assert result == "token42"
