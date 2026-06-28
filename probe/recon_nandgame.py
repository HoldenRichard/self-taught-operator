# RECON v1 — determine NandGame's rendering model (SVG/DOM vs canvas) and locate
# level navigation + circuit parts. Read-only: loads the page and dumps structure.
# Run with the harness venv: computer-use-preview/.venv/bin/python probe/recon_nandgame.py
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"

JS_SUMMARY = r"""
() => {
  const q = (s) => Array.from(document.querySelectorAll(s));
  const brief = (e) => ({
    tag: e.tagName,
    id: e.id || null,
    cls: ((e.getAttribute && e.getAttribute('class')) || '').slice(0,90) || null,
    txt: (e.textContent||'').trim().replace(/\s+/g,' ').slice(0,50) || null
  });
  return {
    url: location.href,
    title: document.title,
    counts: {
      canvas: q('canvas').length,
      svg: q('svg').length,
      svgPath: q('svg path').length,
      svgG: q('svg g').length,
      svgCircle: q('svg circle').length,
      svgRect: q('svg rect').length,
      svgLine: q('svg line').length,
      button: q('button').length,
    },
    bodyChildren: Array.from(document.body.children).map(brief),
    menuish: q('a,li,button,div').filter(e=>{
      const t=(e.textContent||'').trim();
      return /^(NAND|Invert|Inverter|AND|OR|XOR|NOT|Adder|Half|Latch|Relay|Flip)\b/i.test(t) && t.length<40;
    }).slice(0,50).map(brief),
    partish: q('[class*=wire],[class*=pin],[class*=node],[class*=gate],[class*=component],[class*=connector],[class*=terminal],[class*=socket]').slice(0,30).map(brief),
    globals: Object.keys(window).filter(k=>/game|level|circuit|nand|state|app|store|component|wire|board/i.test(k)).slice(0,60),
  };
}
"""

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page()
        print("loading nandgame.com ...")
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3500)
        info = pg.evaluate(JS_SUMMARY)
        print(json.dumps(info, indent=2, default=str))
        pg.screenshot(path=PROBE_DIR+"/recon_landing.png", full_page=False)
        print("SAVED:", PROBE_DIR+"/recon_landing.png")
        pg.wait_for_timeout(800)
        b.close()

if __name__ == "__main__":
    main()
