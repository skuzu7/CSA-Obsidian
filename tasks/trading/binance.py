from __future__ import annotations

from stealth_browser.intercept import RequestInterceptor
from stealth_browser.page_ops import navigate
from tasks.base import BaseTask


class BinanceTokenTask(BaseTask):
    async def run(self, *, timeout: float = 60.0) -> dict:
        interceptor = RequestInterceptor(
            self.page,
            url_pattern="*api.binance.com*",
            header_names=["csrftoken", "bnc-uuid", "x-trace-id"],
        )
        interceptor.attach()
        try:
            await navigate(self.page, "https://www.binance.com/en")
            token = await interceptor.wait_for_header("csrftoken", timeout=timeout)
            return {"csrftoken": token, "captured": interceptor.captured}
        finally:
            interceptor.detach()
