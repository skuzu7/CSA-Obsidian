from __future__ import annotations

from abc import ABC, abstractmethod

from playwright.async_api import Page

from stealth_browser.config import BrowserConfig
from stealth_browser.humanize import HumanBehavior
from stealth_browser.page_ops import navigate
from stealth_browser.snapshot import PageSnapshot, take_snapshot


class BaseTask(ABC):
    def __init__(self, page: Page, human: HumanBehavior, config: BrowserConfig) -> None:
        self.page = page
        self.human = human
        self.config = config

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        ...

    async def snapshot(self, include_screenshot: bool = False) -> PageSnapshot:
        return await take_snapshot(self.page, include_screenshot)

    async def navigate(self, url: str) -> None:
        await navigate(self.page, url)
