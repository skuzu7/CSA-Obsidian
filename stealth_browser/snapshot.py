from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import dataclass

import trafilatura
from playwright.async_api import Page

logger = logging.getLogger(__name__)

SNAPSHOT_JS = """
(() => {
  const sel = [
    'a[href]', 'button', 'input', 'select', 'textarea',
    '[role=button]', '[role=link]', '[role=tab]', '[role=menuitem]',
    '[role=checkbox]', '[role=radio]', '[onclick]', '[tabindex]'
  ].join(',');

  const seen = new Set();
  const out = [];
  let i = 0;

  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.top < -100 || r.top > window.innerHeight + 100) continue;

    const role = el.getAttribute('role') || el.tagName.toLowerCase();
    let label = (
      el.getAttribute('aria-label') ||
      el.getAttribute('placeholder') ||
      el.getAttribute('data-testid') ||
      el.innerText ||
      el.value ||
      el.getAttribute('title') || ''
    ).trim().replace(/\\s+/g, ' ');

    if (label.length > 80) label = label.slice(0, 80);

    const key = `${role}:${label}:${Math.round(r.x)}:${Math.round(r.y)}`;
    if (seen.has(key)) continue;
    seen.add(key);

    out.push({
      index: i++,
      role,
      label,
      tag: el.tagName.toLowerCase(),
      bbox: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]
    });
  }
  return JSON.stringify(out);
})()
"""


@dataclass
class RefElement:
    index: int
    role: str
    label: str
    tag: str
    bbox: tuple[float, float, float, float]


@dataclass
class PageSnapshot:
    url: str
    title: str
    refs: list[RefElement]
    markdown: str
    screenshot_b64: str | None = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "refs": [
                {"index": r.index, "role": r.role, "label": r.label, "tag": r.tag, "bbox": list(r.bbox)}
                for r in self.refs
            ],
            "markdown": self.markdown,
            "screenshot_b64": self.screenshot_b64,
        }

    def to_llm_text(self, max_chars: int = 3000) -> str:
        lines = [f"Page: {self.title} ({self.url})", "", "Interactive elements:"]
        for r in self.refs:
            lines.append(f'[{r.index}] {r.role} "{r.label}"')
        if self.markdown:
            lines.extend(["", "Content:", self.markdown[:max_chars]])
        return "\n".join(lines)


async def take_snapshot(
    page: Page,
    include_screenshot: bool = False,
    include_markdown: bool = True,
) -> PageSnapshot:
    logger.debug("Taking snapshot of %s", page.url)
    raw = await page.evaluate(SNAPSHOT_JS)
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        from stealth_browser.errors import SnapshotError
        raise SnapshotError(f"Invalid JSON from snapshot JS: {exc}") from exc
    refs = [
        RefElement(
            index=el["index"],
            role=el["role"],
            label=el["label"],
            tag=el["tag"],
            bbox=tuple(el["bbox"]),
        )
        for el in items
    ]

    markdown = ""
    if include_markdown:
        html = await page.content()
        markdown = await asyncio.to_thread(trafilatura.extract, html, output_format="markdown") or ""

    screenshot_b64 = None
    if include_screenshot:
        png_bytes = await page.screenshot()
        screenshot_b64 = base64.b64encode(png_bytes).decode()

    logger.info("Snapshot: %d refs, markdown=%d chars", len(refs), len(markdown))
    return PageSnapshot(
        url=page.url,
        title=await page.title(),
        refs=refs,
        markdown=markdown,
        screenshot_b64=screenshot_b64,
    )
