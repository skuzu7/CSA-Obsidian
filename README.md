# automation-stealth: SOTA Stealth Browser Automation

A framework for stealth browser automation with anti-detection capabilities, built on [Camoufox](https://github.com/daijro/camoufox) + [Playwright](https://playwright.dev/) and exposing a full [MCP](https://modelcontextprotocol.io/) server for LLM-driven browser control.

## Overview

`automation-stealth` lets you automate browsers in a way that is resistant to bot-detection heuristics. Key capabilities:

- **Stealth fingerprinting** — Camoufox spoofs canvas, WebGL, fonts, and navigator properties to match a realistic browser profile.
- **Human-like behavior** — randomized mouse movement, scroll inertia, and typing cadence via `HumanBehavior`.
- **MCP server** — 15 browser-control tools usable by any MCP-compatible LLM client (Claude Code, Claude Desktop, etc.).
- **CLI** — `stealth-browser` command for quick page automation, monitoring, and Binance token scraping.
- **Python API** — composable `BrowserManager`, `take_snapshot`, and task classes for scripted workflows.
- **Session management** — save and restore cookies across runs; optional WebRTC blocking and proxy support.

## Requirements

- Python 3.11 or newer
- Core dependencies: `camoufox`, `mcp`, `playwright`, `trafilatura`, `click`, `pycookiecheat`, `browser-cookie3`
- Playwright browsers (installed separately — see below)

## Installation

```bash
git clone https://github.com/anton/automation-stealth
cd automation-stealth
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -e .
playwright install chromium   # or: playwright install
```

For development (linting, type-checking, tests):

```bash
pip install -e ".[dev]"
# or, without PEP 735 support:
pip install pytest pytest-asyncio pytest-cov ruff mypy
```

## Configuration

Copy `env.example` to `.env` in the project root and adjust as needed:

```bash
cp env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `STEALTH_PROFILE_DIR` | `profiles/default` | Path to browser profile directory |
| `STEALTH_HEADLESS` | `false` | Run browser without a visible window |
| `STEALTH_OS_TARGET` | `windows` | OS fingerprint to spoof (`windows`, `macos`, `linux`) |
| `STEALTH_LOCALE` | `pt-BR,pt` | Browser locale string |
| `STEALTH_WINDOW` | `1366,768` | Browser window size (`width,height`) |
| `STEALTH_BLOCK_WEBRTC` | `true` | Block WebRTC to prevent IP leaks |
| `STEALTH_HUMANIZE` | `true` | Enable human-like mouse/keyboard/scroll simulation |
| `STEALTH_PROXY_SERVER` | _(unset)_ | Proxy URL, e.g. `socks5://127.0.0.1:1080` |
| `STEALTH_PROXY_USERNAME` | _(unset)_ | Proxy username (optional) |
| `STEALTH_PROXY_PASSWORD` | _(unset)_ | Proxy password (optional) |

## Usage — CLI

```bash
# Open a page (headless) and print its snapshot
stealth-browser open-page https://example.com

# Open a page and save a screenshot
stealth-browser open-page https://example.com --screenshot

# Monitor a page for content changes every 30 s, up to 20 checks
stealth-browser monitor https://news.site --interval 30 --checks 20

# Scrape Binance new tokens listing (90 s timeout)
stealth-browser binance-tokens --timeout 90
```

## Usage — MCP Server

Start the server (stdio transport, compatible with any MCP client):

```bash
stealth-browser-mcp
```

### Registering in Claude Code

Add to your `.claude/settings.json` or via `claude mcp add`:

```json
{
  "mcpServers": {
    "stealth-browser": {
      "command": "stealth-browser-mcp"
    }
  }
}
```

### Available tools (15)

| Tool | Description |
|---|---|
| `browser_open` | Navigate to a URL and return a snapshot of all interactive elements |
| `browser_snapshot` | Snapshot the current page (elements + markdown content; optionally includes screenshot) |
| `browser_screenshot` | Capture a full-page screenshot as base64 PNG |
| `browser_navigate_back` | Go back in browser history and return a snapshot |
| `browser_refresh` | Reload the current page and return a fresh snapshot |
| `browser_click` | Click an interactive element by its `ref` index from the last snapshot |
| `browser_type` | Type text into an input element by `ref` index, with human-like timing |
| `browser_select` | Select an option by value in a `<select>` element by `ref` index |
| `browser_hover` | Hover over an element by `ref` index (triggers tooltips, dropdowns) |
| `browser_scroll` | Scroll the page up or down by a given number of pixels |
| `browser_press_key` | Press a keyboard key (e.g. `Enter`, `Tab`, `Escape`, `ArrowDown`) |
| `browser_get_text` | Extract the visible text content of the current page as markdown |
| `browser_get_cookies` | Return all cookies for the current page context |
| `browser_evaluate` | Execute arbitrary JavaScript and return the result |
| `browser_save_session` | Save current cookies to a named session file |
| `browser_load_session` | Load cookies from a previously saved named session |
| `browser_close` | Close the browser and reset internal state |

## Usage — Python API

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
        print(snap.to_llm_text())

asyncio.run(main())
```

For more complex workflows, use the built-in tasks:

```python
from tasks.binance import BinanceTokenTask

async def main():
    task = BinanceTokenTask()
    tokens = await task.run()
    print(tokens)
```

## Tests

```bash
pytest --cov --cov-report=term-missing -v
```

Coverage is collected over `stealth_browser/`, `mcp_server/`, `cli/`, and `tasks/`.

## Project structure

```
automation-stealth/
├── stealth_browser/       # Core library
│   ├── browser.py         # BrowserManager (async context manager)
│   ├── config.py          # BrowserConfig (env-driven)
│   ├── humanize.py        # Human-like mouse/keyboard/scroll
│   ├── snapshot.py        # Page snapshot + ref-element index
│   ├── page_ops.py        # screenshot, extract_text, cookies, evaluate
│   ├── intercept.py       # Request/response interception helpers
│   └── session.py         # Cookie save/load utilities
├── mcp_server/
│   └── server.py          # FastMCP server with 15 browser tools
├── cli/
│   └── main.py            # Click CLI (open-page, monitor, binance-tokens)
├── tasks/
│   ├── binance.py         # BinanceTokenTask
│   ├── monitor.py         # PageMonitorTask
│   └── form_fill.py       # FormFillTask
├── tests/
├── env.example            # Environment variable reference
└── pyproject.toml
```

## License

MIT