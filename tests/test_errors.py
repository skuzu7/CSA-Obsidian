import pytest
from stealth_browser.errors import (
    AutomationError, BrowserError, BrowserLaunchError, CookieImportError,
    ElementNotFound, JavaScriptError, NavigationTimeout, PageCrashed,
    RefStale, SessionExpired, SnapshotError,
)


def test_browser_error_is_exception():
    e = BrowserError("msg")
    assert isinstance(e, Exception)
    assert str(e) == "msg"


def test_automation_error_alias():
    assert AutomationError is BrowserError


def test_navigation_timeout_attributes():
    e = NavigationTimeout("https://example.com", 5000)
    assert e.url == "https://example.com"
    assert e.timeout_ms == 5000
    assert "https://example.com" in str(e)
    assert isinstance(e, BrowserError)


def test_navigation_timeout_default_timeout():
    e = NavigationTimeout("https://x.com")
    assert e.timeout_ms == 30000


def test_element_not_found():
    e = ElementNotFound("#submit-btn")
    assert e.selector == "#submit-btn"
    assert isinstance(e, BrowserError)


def test_page_crashed_with_reason():
    e = PageCrashed("OOM")
    assert e.reason == "OOM"
    assert "OOM" in str(e)


def test_page_crashed_empty_reason():
    e = PageCrashed()
    assert e.reason == ""
    assert "crashed" in str(e).lower()


def test_session_expired():
    e = SessionExpired("token invalid")
    assert e.detail == "token invalid"


def test_session_expired_default():
    e = SessionExpired()
    assert e.detail == ""


def test_ref_stale():
    e = RefStale("ref 5 out of range")
    assert e.detail == "ref 5 out of range"


def test_browser_launch_error():
    e = BrowserLaunchError("port blocked")
    assert e.reason == "port blocked"
    assert "port blocked" in str(e)


def test_cookie_import_error():
    e = CookieImportError("v20 encryption")
    assert e.reason == "v20 encryption"


def test_snapshot_error():
    e = SnapshotError("bad json")
    assert e.reason == "bad json"


def test_javascript_error():
    e = JavaScriptError("1+1", "syntax error")
    assert e.js == "1+1"
    assert e.reason == "syntax error"
    assert isinstance(e, BrowserError)
