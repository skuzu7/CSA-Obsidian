"""Teste prático end-to-end do automation-stealth."""
import asyncio
import time
from pathlib import Path

from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.humanize import HumanBehavior
from stealth_browser.snapshot import take_snapshot
from stealth_browser.page_ops import navigate, extract_text
from stealth_browser.intercept import RequestInterceptor
from stealth_browser.session import save_cookies, load_cookies

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


async def main():
    results = {}
    project_root = Path(__file__).resolve().parent
    cfg = BrowserConfig(
        profile_dir=project_root / "profiles" / "test",
        headless=False,
        window=(1366, 768),
    )
    human = HumanBehavior(cfg)

    print("=" * 60)
    print("  TESTE PRÁTICO — automation-stealth")
    print("=" * 60)

    t0 = time.monotonic()
    async with BrowserManager(cfg) as bm:
        launch_time = time.monotonic() - t0

        # 1. Launch
        print(f"\n[1/7] Browser launch ............ {PASS} ({launch_time:.1f}s)")
        results["launch"] = True

        page = await bm.get_page()

        # 2. Navigate to a test page
        try:
            t0 = time.monotonic()
            await navigate(page, "https://example.com")
            nav_time = time.monotonic() - t0
            title = await page.title()
            assert "Example" in title
            print(f"[2/7] Navegação ................. {PASS} ({nav_time:.1f}s) title='{title}'")
            results["navigate"] = True
        except Exception as e:
            print(f"[2/7] Navegação ................. {FAIL} {e}")
            results["navigate"] = False

        # 3. Snapshot
        try:
            snap = await take_snapshot(page, include_screenshot=True, include_markdown=True)
            assert snap.url == "https://example.com/"
            assert len(snap.refs) >= 0
            assert snap.markdown
            assert snap.screenshot_b64
            print(f"[3/7] Snapshot .................. {PASS} refs={len(snap.refs)}, md={len(snap.markdown)} chars, screenshot={len(snap.screenshot_b64)} b64")
            results["snapshot"] = True
        except Exception as e:
            print(f"[3/7] Snapshot .................. {FAIL} {e}")
            results["snapshot"] = False

        # 4. Extract text
        try:
            text = await extract_text(page)
            assert len(text) > 10
            print(f"[4/7] Extract text .............. {PASS} ({len(text)} chars)")
            results["extract"] = True
        except Exception as e:
            print(f"[4/7] Extract text .............. {FAIL} {e}")
            results["extract"] = False

        # 5. Humanize delays
        try:
            t0 = time.monotonic()
            await human.delay(0.2, 0.05)
            await human.lognormal_delay(0.15)
            elapsed = time.monotonic() - t0
            assert elapsed >= 0.1
            print(f"[5/7] Human delays .............. {PASS} ({elapsed:.2f}s)")
            results["humanize"] = True
        except Exception as e:
            print(f"[5/7] Human delays .............. {FAIL} {e}")
            results["humanize"] = False

        # 6. Session persistence (save/load cookies)
        try:
            cookie_path = project_root / "profiles" / "test" / "cookies_test.json"
            cookie_path.parent.mkdir(parents=True, exist_ok=True)
            await save_cookies(page, cookie_path)
            await load_cookies(page, cookie_path)
            assert cookie_path.exists()
            print(f"[6/7] Session persistence ........ {PASS} ({cookie_path})")
            cookie_path.unlink(missing_ok=True)
            results["session"] = True
        except Exception as e:
            print(f"[6/7] Session persistence ........ {FAIL} {e}")
            results["session"] = False

        # 7. Request interceptor
        try:
            page = await bm.get_page()
            interceptor = RequestInterceptor(page, url_pattern="*example*")
            interceptor.attach()
            await page.goto("https://example.com", wait_until="domcontentloaded")
            await asyncio.sleep(1)
            interceptor.detach()
            print(f"[7/7] Request interceptor ........ {PASS} captured={len(interceptor.captured)} requests")
            results["interceptor"] = True
        except Exception as e:
            print(f"[7/7] Request interceptor ........ {FAIL} {e}")
            results["interceptor"] = False

        # Save screenshot
        screenshot_path = project_root / "test_screenshot.png"
        try:
            await page.screenshot(path=str(screenshot_path))
        except Exception:
            pass

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print("\n" + "=" * 60)
    color = "\033[92m" if passed == total else "\033[93m"
    print(f"  RESULTADO: {color}{passed}/{total} testes passaram\033[0m")
    print("=" * 60)

    if screenshot_path.exists():
        print(f"\nScreenshot salvo: {screenshot_path.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
