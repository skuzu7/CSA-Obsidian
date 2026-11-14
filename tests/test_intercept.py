import asyncio
import collections
from unittest.mock import MagicMock

import pytest

from stealth_browser.intercept import REDACTED, RequestInterceptor


def make_page():
    page = MagicMock()
    page.on = MagicMock()
    page.remove_listener = MagicMock()
    return page


@pytest.fixture
def interceptor():
    return RequestInterceptor(make_page(), url_pattern="*example.com*", header_names=["x-token"])


def request(url="https://example.com", headers=None):
    item = MagicMock()
    item.url = url
    item.method = "GET"
    item.headers = headers or {}
    return item


def test_attach_registers_listener(interceptor):
    interceptor.attach()
    interceptor._page.on.assert_called_once_with("request", interceptor._on_request)


def test_detach_removes_listener(interceptor):
    interceptor.attach()
    interceptor.detach()
    interceptor._page.remove_listener.assert_called_once_with("request", interceptor._on_request)


def test_captured_is_bounded_deque(interceptor):
    assert isinstance(interceptor.captured, collections.deque)
    assert interceptor.captured.maxlen == 500


async def test_context_manager_attaches_and_detaches():
    page = make_page()
    async with RequestInterceptor(page) as instance:
        page.on.assert_called_once_with("request", instance._on_request)
    page.remove_listener.assert_called_once_with("request", instance._on_request)


def test_on_request_filters_by_url_pattern():
    instance = RequestInterceptor(make_page(), url_pattern="*binance.com*")
    instance._on_request(request("https://api.binance.com/api/v3/ping", {"content-type": "application/json"}))
    instance._on_request(request("https://google.com", {"content-type": "text/html"}))
    assert len(instance.captured) == 1
    assert instance.captured[0]["url"] == "https://api.binance.com/api/v3/ping"


def test_sensitive_and_unknown_header_values_are_redacted():
    instance = RequestInterceptor(make_page())
    instance._on_request(
        request(
            headers={
                "content-type": "application/json",
                "authorization": "Bearer never-store-this",
                "cookie": "session=never-store-this",
                "x-api-key": "never-store-this",
                "x-csrf-token": "never-store-this",
                "x-trace-id": "custom-value",
            }
        )
    )
    headers = instance.captured[0]["headers"]
    assert headers["content-type"] == "application/json"
    for name in ("authorization", "cookie", "x-api-key", "x-csrf-token", "x-trace-id"):
        assert headers[name] == REDACTED
    assert "never-store-this" not in repr(instance.captured)
    assert "custom-value" not in repr(instance.captured)


def test_header_filter_only_stores_selected_names_and_redacts_custom_values():
    instance = RequestInterceptor(make_page(), header_names=["x-token"])
    instance._on_request(request(headers={"x-token": "secret-value", "content-type": "application/json"}))
    assert instance.captured[0]["headers"] == {"x-token": REDACTED}


async def test_wait_for_header_finds_existing_allowlisted_header():
    instance = RequestInterceptor(make_page())
    instance.captured.append(
        {"url": "https://x.com", "method": "GET", "headers": {"content-type": "application/json"}}
    )
    assert await instance.wait_for_header("content-type", timeout=1.0) == "application/json"


async def test_wait_for_header_is_case_insensitive():
    instance = RequestInterceptor(make_page())
    instance.captured.append(
        {"url": "https://x.com", "method": "GET", "headers": {"Content-Type": "application/json"}}
    )
    assert await instance.wait_for_header("CONTENT-TYPE", timeout=1.0) == "application/json"


async def test_wait_for_header_rejects_sensitive_or_custom_names():
    instance = RequestInterceptor(make_page())
    for name in ("authorization", "cookie", "x-api-key", "x-token", "x-csrf-token"):
        with pytest.raises(ValueError, match="allowlisted"):
            await instance.wait_for_header(name, timeout=0.01)


async def test_wait_for_header_timeout():
    instance = RequestInterceptor(make_page())
    with pytest.raises(TimeoutError):
        await instance.wait_for_header("content-type", timeout=0.05)


async def test_wait_for_header_triggered_by_event():
    instance = RequestInterceptor(make_page())

    async def inject_after_delay():
        await asyncio.sleep(0.05)
        instance.captured.append(
            {"url": "https://x.com", "method": "GET", "headers": {"content-type": "application/json"}}
        )
        instance._event.set()

    asyncio.create_task(inject_after_delay())
    assert await instance.wait_for_header("content-type", timeout=1.0) == "application/json"
