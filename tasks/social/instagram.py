from __future__ import annotations

from tasks.base import BaseTask


class InstagramTask(BaseTask):
    async def run(self, **kwargs) -> dict:
        raise NotImplementedError("Instagram task module not yet implemented")
