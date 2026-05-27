from __future__ import annotations

import asyncio
import hashlib

from stealth_browser.page_ops import extract_text, navigate
from tasks.base import BaseTask


class PageMonitorTask(BaseTask):
    async def run(self, *, url: str, interval: float = 60.0, max_checks: int = 10) -> dict:
        await navigate(self.page, url)
        baseline = hashlib.sha256((await extract_text(self.page)).encode()).hexdigest()

        for i in range(max_checks):
            await asyncio.sleep(interval)
            await self.page.reload(wait_until="domcontentloaded")
            current = hashlib.sha256((await extract_text(self.page)).encode()).hexdigest()
            if current != baseline:
                snap = await self.snapshot()
                return {"changed": True, "check": i + 1, "snapshot": snap.to_llm_text()}
        return {"changed": False, "checks": max_checks}
