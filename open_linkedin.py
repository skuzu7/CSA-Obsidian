"""Open LinkedIn in stealth browser and keep it open for interactive use."""
import asyncio
from pathlib import Path

from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.page_ops import navigate


async def main():
    cfg = BrowserConfig(profile_dir=Path("profiles/linkedin"))
    async with BrowserManager(cfg) as bm:
        page = await bm.get_page()
        await navigate(page, "https://www.linkedin.com")
        print("LinkedIn aberto. Feche o browser manualmente quando terminar.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
