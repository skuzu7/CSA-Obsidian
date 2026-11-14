from __future__ import annotations

import asyncio
import collections
import fnmatch
import logging

from playwright.async_api import Page, Request

logger = logging.getLogger(__name__)

# Only ordinary protocol metadata is exposed. Unknown/custom headers are
# redacted by default because their names do not prove their values are safe.
SAFE_HEADER_NAMES = frozenset(
    {
        "accept", "accept-encoding", "accept-language", "cache-control",
        "connection", "content-length", "content-type", "dnt", "host",
        "if-modified-since", "if-none-match", "origin", "pragma", "range",
        "referer", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform",
        "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site", "sec-fetch-user",
        "upgrade-insecure-requests", "user-agent",
    }
)
REDACTED = "[REDACTED]"


class RequestInterceptor:
    def __init__(
        self,
        page: Page,
        url_pattern: str = "*",
        header_names: list[str] | None = None,
    ) -> None:
        self._page = page
        self._url_pattern = url_pattern
        self._header_names = {h.lower() for h in header_names} if header_names else None
        self.captured: collections.deque[dict] = collections.deque(maxlen=500)
        self._event = asyncio.Event()

    def _on_request(self, request: Request) -> None:
        if not fnmatch.fnmatch(request.url, self._url_pattern):
            return
        raw_headers = dict(request.headers)
        raw_names = {name.lower() for name in raw_headers}
        if self._header_names is not None and not self._header_names.intersection(raw_names):
            return
        if self._header_names is None:
            selected = raw_headers.items()
        else:
            selected = (
                (name, value)
                for name, value in raw_headers.items()
                if name.lower() in self._header_names
            )
        headers = {
            name: value if name.lower() in SAFE_HEADER_NAMES else REDACTED
            for name, value in selected
        }
        logger.debug("Captured request metadata: %s", request.url)
        self.captured.append({"url": request.url, "method": request.method, "headers": headers})
        self._event.set()

    def attach(self) -> None:
        self._page.on("request", self._on_request)

    def detach(self) -> None:
        self._page.remove_listener("request", self._on_request)

    async def __aenter__(self) -> RequestInterceptor:
        self.attach()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.detach()

    async def wait_for_header(self, header_name: str, timeout: float = 30.0) -> str:
        needle = header_name.lower()
        if needle not in SAFE_HEADER_NAMES:
            raise ValueError(
                f"Header '{header_name}' is not allowlisted for value access; "
                "sensitive and custom header values are redacted"
            )
        try:
            async with asyncio.timeout(timeout):
                while True:
                    for record in self.captured:
                        for name, value in record["headers"].items():
                            if name.lower() == needle:
                                return value
                    snapshot_len = len(self.captured)
                    self._event.clear()
                    if len(self.captured) > snapshot_len:
                        continue
                    await self._event.wait()
        except TimeoutError:
            logger.warning("Header '%s' not captured within %ss", header_name, timeout)
            raise TimeoutError(f"Header {header_name} not captured within {timeout}s")
