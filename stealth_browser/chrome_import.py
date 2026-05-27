"""Import cookies from Chrome via CDP (Chrome DevTools Protocol).

Launches Chrome headless with the user's real profile, connects via CDP,
and extracts all cookies already decrypted — bypasses v20 app-bound encryption.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

_CHROME_CANDIDATES = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe",
]

CHROME_USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"

CACHE_FILENAME = "chrome_cookies_cache.json"


def _find_chrome() -> Path:
    for p in _CHROME_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("Chrome executable not found")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _is_chrome_running() -> bool:
    r = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True,
    )
    return "chrome.exe" in r.stdout.lower()


def _close_chrome(timeout: int = 10) -> bool:
    if not _is_chrome_running():
        return True
    subprocess.run(["taskkill", "/IM", "chrome.exe"], capture_output=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _is_chrome_running():
            return True
        time.sleep(0.5)
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(1)
    return not _is_chrome_running()


async def _wait_cdp_ready(port: int, timeout: float = 20.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2)
            data = json.loads(resp.read())
            return data["webSocketDebuggerUrl"]
        except Exception:
            await asyncio.sleep(0.5)
    raise TimeoutError(f"Chrome CDP not ready on port {port} after {timeout}s")


def _cdp_to_playwright(cdp_cookies: list[dict]) -> list[dict]:
    pw = []
    for c in cdp_cookies:
        same_site = c.get("sameSite", "None")
        if same_site not in ("Strict", "Lax", "None"):
            same_site = "None"
        pw.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ""),
            "path": c.get("path", "/"),
            "expires": c.get("expires", -1),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": same_site,
        })
    return pw


def _read_cache(cache_dir: Path, ttl: int) -> list[dict] | None:
    cache_file = cache_dir / CACHE_FILENAME
    if not cache_file.exists():
        return None
    age = time.time() - cache_file.stat().st_mtime
    if age >= ttl:
        return None
    return json.loads(cache_file.read_text(encoding="utf-8"))


def _write_cache(cache_dir: Path, cookies: list[dict]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / CACHE_FILENAME).write_text(
        json.dumps(cookies, ensure_ascii=False), encoding="utf-8",
    )


async def extract_chrome_cookies(
    cache_dir: Path | None = None,
    cache_ttl: int = 3600,
    chrome_profile: str = "Default",
) -> list[dict]:
    """Extract all cookies from Chrome via CDP.

    Closes Chrome if running, launches headless with CDP, extracts cookies,
    then kills headless Chrome. Caches results for ``cache_ttl`` seconds.
    """
    if cache_dir:
        cached = _read_cache(cache_dir, cache_ttl)
        if cached is not None:
            return cached

    chrome_path = _find_chrome()
    port = _free_port()

    was_running = _is_chrome_running()
    if was_running:
        _close_chrome()
        await asyncio.sleep(1)

    proc = subprocess.Popen(
        [
            str(chrome_path),
            f"--remote-debugging-port={port}",
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={CHROME_USER_DATA}",
            f"--profile-directory={chrome_profile}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        await _wait_cdp_ready(port)

        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            try:
                cdp = await browser.new_browser_cdp_session()
                result = await cdp.send("Network.getAllCookies")
                raw = result.get("cookies", [])
            finally:
                await browser.close()

        cookies = _cdp_to_playwright(raw)

        if cache_dir:
            _write_cache(cache_dir, cookies)

        return cookies
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
