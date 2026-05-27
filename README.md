<div align="center">

# 🦊 automation-stealth

### Undetectable browser automation that an LLM can actually drive.

Camoufox-powered stealth + a full **MCP server** = give Claude (or any LLM) real hands on a real browser, with human-like behavior that sails past bot detection.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Built on Camoufox](https://img.shields.io/badge/stealth-Camoufox-orange.svg)](https://github.com/daijro/camoufox)
[![MCP](https://img.shields.io/badge/MCP-17_tools-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Tests](https://img.shields.io/badge/tests-61_passing-brightgreen.svg)](#-tests)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-ff69b4.svg)](CONTRIBUTING.md)

</div>

---

## ⚡ Why this exists

Most automation gets flagged the second it loads: `navigator.webdriver`, canvas hashes, robotic mouse paths, instant typing. `automation-stealth` fixes all of that **and** wraps it in a [Model Context Protocol](https://modelcontextprotocol.io/) server, so an LLM can navigate, click, type, and scrape — behaving like a human the whole way.

> **Real demo:** we pointed Claude at this framework and told it to take the *Anthropic Academy "Claude 101"* certification quiz on a live, login-gated site. It navigated there, read each question, and scored **10/10 (100%)** — driving a real browser end-to-end, undetected. 🎓

## ✨ Features

- 🕵️ **True stealth** — [Camoufox](https://github.com/daijro/camoufox) (hardened Firefox) spoofs canvas, WebGL, fonts, and `navigator` properties; removes automation flags; blocks WebRTC IP leaks.
- 🧠 **LLM-native** — a **17-tool MCP server** turns any MCP client (Claude Code, Claude Desktop, …) into a browser operator. Snapshots return indexed, clickable elements an LLM can reason about.
- 🤚 **Human behavior** — Gaussian typing cadence, multi-step scroll inertia, and **interpolated mouse drags with jitter** — no teleporting cursors.
- 🍪 **Sessions that persist** — save/restore cookies + `localStorage`, persistent profiles, optional Chrome cookie import via CDP (bypasses v20 app-bound encryption).
- 🧰 **Three ways in** — a `stealth-browser` CLI, the MCP server, or a clean async Python API.
- 🌐 **Proxy & locale aware** — authenticated proxies, OS/locale spoofing, configurable window size.

## 🚀 Quickstart

```bash
git clone https://github.com/skuzu7/CSA-Obsidian
cd CSA-Obsidian
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -e .
```

```python
import asyncio
from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.snapshot import take_snapshot

async def main():
    async with BrowserManager(BrowserConfig(headless=True)) as bm:
        page = await bm.get_page()
        await page.goto("https://example.com")
        snap = await take_snapshot(page)
        print(snap.to_llm_text())   # title, URL, indexed interactive elements, markdown

asyncio.run(main())
```

## 🤖 Plug it into Claude

Start the MCP server (stdio transport, works with any MCP client):

```bash
stealth-browser-mcp
```

Register it in Claude Code:

```bash
claude mcp add stealth-browser -- stealth-browser-mcp
```

…then just ask Claude to *"open example.com and click the first link."* It gets a snapshot, picks a `ref`, and acts.

### The 17 MCP tools

| Tool | What it does |
|---|---|
| `browser_open` | Navigate to a URL → snapshot of interactive elements |
| `browser_snapshot` | Snapshot current page (elements + markdown, optional screenshot) |
| `browser_screenshot` | Full-page screenshot as base64 PNG |
| `browser_navigate_back` | Go back → snapshot |
| `browser_refresh` | Reload → fresh snapshot |
| `browser_click` | Click element by `ref` (human-like) |
| `browser_type` | Type into element by `ref`, human cadence |
| `browser_select` | Pick a `<select>` option by `ref` |
| `browser_hover` | Hover by `ref` (tooltips, dropdowns) |
| `browser_scroll` | Human-like scroll up/down |
| `browser_press_key` | Press a key (`Enter`, `Tab`, …) |
| `browser_get_text` | Page text as markdown |
| `browser_get_cookies` | All cookies for the context |
| `browser_evaluate` | Run arbitrary JS, return result |
| `browser_save_session` | Save cookies to a named session |
| `browser_load_session` | Restore a named session |
| `browser_close` | Close browser, reset state |

## 🖥️ CLI

```bash
stealth-browser open-page https://example.com               # snapshot to stdout
stealth-browser open-page https://example.com --screenshot  # + save screenshot
stealth-browser monitor https://news.site --interval 30 --checks 20
stealth-browser binance-tokens --timeout 90
```

## ⚙️ Configuration

Copy `env.example` → `.env` and tune:

| Variable | Default | Description |
|---|---|---|
| `STEALTH_PROFILE_DIR` | `profiles/default` | Persistent browser profile path |
| `STEALTH_HEADLESS` | `false` | Headless mode |
| `STEALTH_OS_TARGET` | `windows` | Spoofed OS (`windows`, `macos`, `linux`) |
| `STEALTH_LOCALE` | `pt-BR,pt` | Browser locale |
| `STEALTH_WINDOW` | `1366,768` | Window size (`width,height`) |
| `STEALTH_BLOCK_WEBRTC` | `true` | Block WebRTC (prevent IP leaks) |
| `STEALTH_HUMANIZE` | `true` | Human-like input simulation |
| `STEALTH_PROXY_SERVER` | _(unset)_ | Proxy URL, e.g. `socks5://127.0.0.1:1080` |
| `STEALTH_PROXY_USERNAME` / `_PASSWORD` | _(unset)_ | Proxy auth (optional) |

## 🐍 Python API — tasks

```python
import asyncio
from stealth_browser.browser import BrowserManager
from stealth_browser.config import BrowserConfig
from stealth_browser.humanize import HumanBehavior
from tasks.trading.binance import BinanceTokenTask

async def main():
    cfg = BrowserConfig(headless=True)
    async with BrowserManager(cfg) as bm:
        page = await bm.get_page()
        task = BinanceTokenTask(page, HumanBehavior(cfg), cfg)
        print(await task.run(timeout=90))

asyncio.run(main())
```

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest --cov --cov-report=term-missing -q
```

**61 tests**, covering errors, config, snapshot, request interception, the MCP layer, and page ops. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design.

## 🗂️ Project structure

```
automation-stealth/
├── stealth_browser/    # Core: browser, config, humanize, snapshot, page_ops, intercept, session, errors
├── mcp_server/         # FastMCP server (17 tools) + concurrency lock + error decorator
├── cli/                # Click CLI (open-page, monitor, binance-tokens)
├── tasks/              # BinanceTokenTask, PageMonitorTask, FormFillTask
├── tests/              # pytest suite (asyncio)
├── docs/ARCHITECTURE.md
└── pyproject.toml
```

## 🤝 Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Run `ruff check .` and `pytest` before opening one.

## ⚖️ Responsible use

Built for legitimate automation: QA, end-to-end testing, accessibility audits, personal data collection, and LLM agents acting on your behalf. **Respect each site's Terms of Service, `robots.txt`, and applicable law.** You are responsible for how you use it.

## 📜 License

[MIT](LICENSE) © Anton ([@skuzu7](https://github.com/skuzu7))

<div align="center">

**If this saved you from another flagged automation run, drop a ⭐ — it genuinely helps.**

</div>
