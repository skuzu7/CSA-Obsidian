from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click

from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.humanize import HumanBehavior


@click.group()
def cli():
    pass


@cli.command()
@click.argument("url")
@click.option("--profile", default="default")
@click.option("--screenshot", is_flag=True)
def open_page(url: str, profile: str, screenshot: bool):
    try:
        asyncio.run(_open_page(url, profile, screenshot))
    except Exception as e:
        click.echo(f"Erro: {e}", err=True)
        raise SystemExit(1)


async def _open_page(url: str, profile: str, screenshot: bool):
    from stealth_browser.snapshot import take_snapshot
    from stealth_browser.page_ops import navigate

    cfg = BrowserConfig(profile_dir=Path.home() / ".automation-stealth" / "profiles" / profile)
    async with BrowserManager(cfg) as bm:
        page = await bm.get_page()
        await navigate(page, url)
        snap = await take_snapshot(page, include_screenshot=screenshot)
        click.echo(snap.to_llm_text())
        if screenshot:
            out = Path("screenshot.png")
            await page.screenshot(path=str(out))
            click.echo(f"Screenshot saved: {out}")


@cli.command()
@click.option("--profile", default="default")
@click.option("--timeout", default=60.0, type=float)
def binance_tokens(profile: str, timeout: float):
    try:
        asyncio.run(_binance_tokens(profile, timeout))
    except Exception as e:
        click.echo(f"Erro: {e}", err=True)
        raise SystemExit(1)


async def _binance_tokens(profile: str, timeout: float):
    from tasks.trading.binance import BinanceTokenTask

    cfg = BrowserConfig(profile_dir=Path.home() / ".automation-stealth" / "profiles" / profile)
    async with BrowserManager(cfg) as bm:
        page = await bm.get_page()
        human = HumanBehavior(cfg)
        task = BinanceTokenTask(page, human, cfg)
        result = await task.run(timeout=timeout)
        for k, v in result.items():
            if k != "captured":
                click.echo(f"{k}: {v}")


@cli.command()
@click.argument("url")
@click.option("--profile", default="default")
@click.option("--interval", default=60.0, type=float)
@click.option("--checks", default=10, type=int)
def monitor(url: str, profile: str, interval: float, checks: int):
    try:
        asyncio.run(_monitor(url, profile, interval, checks))
    except Exception as e:
        click.echo(f"Erro: {e}", err=True)
        raise SystemExit(1)


async def _monitor(url: str, profile: str, interval: float, checks: int):
    from tasks.scraping.monitor import PageMonitorTask

    cfg = BrowserConfig(profile_dir=Path.home() / ".automation-stealth" / "profiles" / profile)
    async with BrowserManager(cfg) as bm:
        page = await bm.get_page()
        human = HumanBehavior(cfg)
        task = PageMonitorTask(page, human, cfg)
        result = await task.run(url=url, interval=interval, max_checks=checks)
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
