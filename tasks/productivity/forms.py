from __future__ import annotations

from stealth_browser.page_ops import fill, navigate
from tasks.base import BaseTask


class FormFillTask(BaseTask):
    async def run(self, *, url: str, fields: dict[str, str]) -> dict:
        await navigate(self.page, url)
        for selector, value in fields.items():
            await fill(self.page, selector, value, human=self.human)
            await self.human.delay(0.5, 0.2)
        return {"ok": True, "filled": len(fields)}
