class BrowserError(Exception):
    pass


AutomationError = BrowserError


class NavigationTimeout(BrowserError):
    def __init__(self, url: str, timeout_ms: int = 30000) -> None:
        super().__init__(f"Navigation timeout: {url} (timeout={timeout_ms}ms)")
        self.url = url
        self.timeout_ms = timeout_ms


class ElementNotFound(BrowserError):
    def __init__(self, selector: str) -> None:
        super().__init__(f"Element not found: {selector}")
        self.selector = selector


class PageCrashed(BrowserError):
    def __init__(self, reason: str = "") -> None:
        super().__init__(f"Page crashed: {reason}" if reason else "Page crashed")
        self.reason = reason


class SessionExpired(BrowserError):
    def __init__(self, detail: str = "") -> None:
        super().__init__(f"Session expired: {detail}" if detail else "Session expired")
        self.detail = detail


class RefStale(BrowserError):
    """Snapshot ref no longer resolves to a DOM element."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BrowserLaunchError(BrowserError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Browser launch failed: {reason}")
        self.reason = reason


class CookieImportError(BrowserError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Cookie import failed: {reason}")
        self.reason = reason


class SnapshotError(BrowserError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Snapshot error: {reason}")
        self.reason = reason


class JavaScriptError(BrowserError):
    def __init__(self, js: str, reason: str) -> None:
        super().__init__(f"JavaScript error: {reason}")
        self.js = js
        self.reason = reason
