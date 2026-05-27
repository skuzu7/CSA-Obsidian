from __future__ import annotations

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import BrowserContext, Page

from stealth_browser.config import BrowserConfig


class BrowserManager:
    def __init__(self, config: BrowserConfig | None = None) -> None:
        self._config = config or BrowserConfig()
        self._cfx: AsyncCamoufox | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> BrowserManager:
        cfg = self._config

        if cfg.import_chrome_cookies:
            from stealth_browser.chrome_import import extract_chrome_cookies
            self._chrome_cookies = await extract_chrome_cookies(
                cache_dir=cfg.profile_dir,
                cache_ttl=cfg.chrome_cookie_ttl,
            )
        else:
            self._chrome_cookies = []

        self._cfx = AsyncCamoufox(
            persistent_context=True,
            user_data_dir=str(cfg.profile_dir),
            humanize=cfg.humanize,
            os=cfg.os_target,
            locale=cfg.locale,
            window=cfg.window,
            headless=cfg.headless,
            block_webrtc=cfg.block_webrtc,
            proxy=cfg.proxy,
            enable_cache=cfg.enable_cache,
        )
        self._context = await self._cfx.__aenter__()

        if self._chrome_cookies:
            await self._context.add_cookies(self._chrome_cookies)

        return self

    async def __aexit__(self, *args) -> None:
        await self._cfx.__aexit__(*args)

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("BrowserManager must be used as an async context manager")
        return self._context

    async def get_page(self) -> Page:
        pages = self.context.pages
        if pages:
            return pages[0]
        return await self.context.new_page()

    async def new_page(self) -> Page:
        return await self.context.new_page()

    async def close(self) -> None:
        if self._cfx is not None:
            await self._cfx.__aexit__(None, None, None)
