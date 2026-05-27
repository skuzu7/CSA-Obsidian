from __future__ import annotations

import asyncio
import logging
import math
import random

from playwright.async_api import Locator, Page

from stealth_browser.config import BrowserConfig
from stealth_browser.errors import ElementNotFound

logger = logging.getLogger(__name__)


class HumanBehavior:
    def __init__(self, cfg: BrowserConfig) -> None:
        self._cfg = cfg

    async def delay(self, mean: float, std: float, minimum: float = 0.1) -> None:
        await asyncio.sleep(max(minimum, random.gauss(mean, std)))

    async def lognormal_delay(self, mean: float, std: float = 0.8) -> None:
        await asyncio.sleep(random.lognormvariate(math.log(mean), std))

    async def type_text(self, page: Page, text: str) -> None:
        cfg = self._cfg
        for char in text:
            cps = max(1.0, random.gauss(cfg.typing_cps_mean, cfg.typing_cps_std))
            delay = 1.0 / cps
            await page.keyboard.type(char)
            if char == " ":
                delay += max(0.0, random.gauss(cfg.typing_word_pause_mean, cfg.typing_word_pause_std))
            if random.random() < cfg.typing_hesitation_prob:
                delay += random.uniform(0.8, 2.5)
            await asyncio.sleep(delay)

    async def scroll(self, page: Page, pixels: int = 300) -> None:
        cfg = self._cfg
        steps = random.randint(cfg.scroll_steps_min, cfg.scroll_steps_max)
        per_step = pixels / steps
        for _ in range(steps):
            delta = random.gauss(per_step, per_step * 0.2)
            await page.mouse.wheel(0, delta)
            await asyncio.sleep(max(0.0, random.gauss(0.15, 0.05)))

    async def click(self, page: Page, locator: Locator) -> None:
        cfg = self._cfg
        await locator.scroll_into_view_if_needed()
        await locator.hover()
        await asyncio.sleep(max(0.1, random.gauss(cfg.click_hover_mean, cfg.click_hover_std)))
        await locator.click()

    async def hover(self, page: Page, locator: Locator) -> None:
        await locator.hover()
        await asyncio.sleep(max(0.05, random.gauss(0.15, 0.05)))

    async def drag(self, page: Page, source: Locator, target: Locator) -> None:
        src_box = await source.bounding_box()
        if src_box is None:
            raise ElementNotFound("source element")
        tgt_box = await target.bounding_box()
        if tgt_box is None:
            raise ElementNotFound("target element")
        sx = src_box["x"] + src_box["width"] / 2
        sy = src_box["y"] + src_box["height"] / 2
        tx = tgt_box["x"] + tgt_box["width"] / 2
        ty = tgt_box["y"] + tgt_box["height"] / 2
        await page.mouse.move(sx, sy)
        await page.mouse.down()
        await asyncio.sleep(max(0.05, random.gauss(0.1, 0.03)))
        steps = 8
        for step in range(1, steps + 1):
            t = step / steps
            ix = sx + (tx - sx) * t + random.gauss(0, 2)
            iy = sy + (ty - sy) * t + random.gauss(0, 2)
            await page.mouse.move(ix, iy)
            await asyncio.sleep(max(0.0, random.gauss(0.02, 0.005)))
        await page.mouse.move(tx, ty)
        await page.mouse.up()
