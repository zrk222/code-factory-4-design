"""Browser-rendered design evidence for visibility, overflow, and overlap."""
from __future__ import annotations

from pathlib import Path
import json


VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}

_INSPECT = """() => {
  const body = document.body;
  const style = getComputedStyle(body);
  const text = (body.innerText || '').trim();
  const ctas = [...document.querySelectorAll('button,a[href],input[type=submit]')];
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width >= 1 && r.height >= 1 && s.display !== 'none' &&
      s.visibility !== 'hidden' && Number(s.opacity || 1) > 0;
  };
  const regions = [...document.querySelectorAll('body > header, body > nav, body > main, body > section, body > footer, body > [role=dialog]')]
    .filter(visible).map((el, i) => ({i, tag: el.tagName, r: el.getBoundingClientRect().toJSON()}));
  const overlaps = [];
  for (let i=0; i<regions.length; i++) for (let j=i+1; j<regions.length; j++) {
    const a=regions[i].r, b=regions[j].r;
    const w=Math.max(0, Math.min(a.right,b.right)-Math.max(a.left,b.left));
    const h=Math.max(0, Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
    if (w*h > 64) overlaps.push(`${regions[i].tag}:${regions[i].i}/${regions[j].tag}:${regions[j].i}`);
  }
  return {
    title: document.title,
    text_chars: text.length,
    body_hidden: style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity || 1) === 0,
    horizontal_overflow_px: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
    visible_actions: ctas.filter(visible).length,
    regions: regions.length,
    overlaps,
  };
}"""


def render_audit(target: str | Path, out_dir: Path) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("render-audit requires: python -m pip install 'code-factory-4-design[render]'") from exc

    target_text = str(target)
    url = target_text if target_text.startswith(("http://", "https://", "file://")) else Path(target_text).resolve().as_uri()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for name, viewport in VIEWPORTS.items():
                page = browser.new_page(viewport=viewport)
                page.goto(url, wait_until="networkidle")
                evidence = page.evaluate(_INSPECT)
                screenshot = out_dir / f"{name}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                findings = []
                if evidence["body_hidden"] or evidence["text_chars"] == 0:
                    findings.append("R_BLANK_OR_HIDDEN")
                if evidence["horizontal_overflow_px"] > 1:
                    findings.append("R_HORIZONTAL_OVERFLOW")
                if evidence["overlaps"]:
                    findings.append("R_REGION_OVERLAP")
                if evidence["visible_actions"] == 0:
                    findings.append("R_NO_VISIBLE_ACTION")
                reports.append({
                    "viewport": name,
                    "size": viewport,
                    "passed": not findings,
                    "findings": findings,
                    "evidence": evidence,
                    "screenshot": str(screenshot),
                })
                page.close()
        finally:
            browser.close()
    payload = {
        "schema": "prestige.render_receipt.v1",
        "target": url,
        "passed": all(item["passed"] for item in reports),
        "viewports": reports,
    }
    receipt = out_dir / "render-receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload | {"receipt_path": str(receipt)}
