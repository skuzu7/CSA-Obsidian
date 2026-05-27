class BrowserError(Exception):
    pass


class NavigationTimeout(BrowserError):
    pass


class ElementNotFound(BrowserError):
    pass


class PageCrashed(BrowserError):
    pass


class SessionExpired(BrowserError):
    pass


class RefStale(BrowserError):
    """Snapshot ref no longer resolves to a DOM element."""
