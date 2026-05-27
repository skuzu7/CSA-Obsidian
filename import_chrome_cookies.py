"""Extract Chrome cookies and inject into the running Camoufox LinkedIn session."""
import asyncio
from pathlib import Path

from chrome_cookies import extract
from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig


async def main():
    cookies = extract(Path("chrome_cookies.json"))
    print(f"\n{len(cookies)} cookies extraídos do Chrome.")

    cfg = BrowserConfig(profile_dir=Path("profiles/linkedin"))
    async with BrowserManager(cfg) as bm:
        ctx = bm.context
        await ctx.add_cookies(cookies)
        page = await bm.get_page()
        await page.goto("https://www.linkedin.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        title = await page.title()
        print(f"Página: {title}")

        if "feed" in page.url or "mynetwork" in page.url:
            print("Login detectado — cookies importados com sucesso!")
        else:
            print(f"URL atual: {page.url}")
            print("Pode ser que o LinkedIn exija re-login mesmo com cookies (security check).")

        print("\nBrowser aberto. Feche manualmente quando terminar.")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
