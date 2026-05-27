from __future__ import annotations

from stealth_browser.errors import AutomationError
from stealth_browser.intercept import RequestInterceptor
from stealth_browser.page_ops import navigate
from tasks.base import BaseTask


class BinanceTokenTask(BaseTask):
    async def run(self, *, timeout: float = 60.0) -> dict:
        async with RequestInterceptor(
            self.page,
            url_pattern="*api.binance.com*",
            header_names=["csrftoken", "bnc-uuid", "x-trace-id"],
        ) as interceptor:
            await navigate(self.page, "https://www.binance.com/en")
            try:
                token = await interceptor.wait_for_header("csrftoken", timeout=timeout)
            except TimeoutError as exc:
                raise AutomationError(f"csrftoken nao capturado — timeout de {timeout}s") from exc
            return {"csrftoken": token, "captured": list(interceptor.captured)}
