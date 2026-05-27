from __future__ import annotations

import asyncio
import fnmatch
import logging
from typing import Any

from playwright.async_api import Page, Request

logger = logging.getLogger(__name__)


class RequestInterceptor:
    def __init__(
        self,
        page: Page,
        url_pattern: str = "*",
        header_names: list[str] | None = None,
    ) -> None:
        self._page = page
        self._url_pattern = url_pattern
        self._header_names = [h.lower() for h in header_names] if header_names else None
        self.captured: list[dict] = []
        self._event = asyncio.Event()

    def _on_request(self, request: Request) -> None:
        if not fnmatch.fnmatch(request.url, self._url_pattern):
            return
        headers = dict(request.headers)
        if self._header_names is not None:
            headers_lower = {k.lower() for k in headers}
            if not any(name in headers_lower for name in self._header_names):
                return
        logger.debug("Captured request: %s", request.url)
        self.captured.append({"url": request.url, "method": request.method, "headers": headers})
        self._event.set()

    def attach(self) -> None:
        self._page.on("request", self._on_request)

    def detach(self) -> None:
        self._page.remove_listener("request", self._on_request)

    async def wait_for_header(self, header_name: str, timeout: float = 30.0) -> str:
        needle = header_name.lower()
        try:
            async with asyncio.timeout(timeout):
                while True:
                    for record in self.captured:
                        for k, v in record["headers"].items():
                            if k.lower() == needle:
                                return v
                    self._event.clear()
                    await self._event.wait()
        except TimeoutError:
            logger.warning("Header '%s' not captured within %ss", header_name, timeout)
            raise TimeoutError(f"Header {header_name} not captured within {timeout}s")
