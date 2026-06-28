# RECON v2 — dismiss popup, enumerate connectors (pins) with exact viewport-center
# coordinates, count wires (drag success oracle), and dump localStorage (referee research).
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"

JS_CONNECTORS = r"""
() => {
  const round = (n) => Math.round(n);
  const center = (e) => { const r = e.getBoundingClientRect();
    return {x: round(r.x + r.width/2), y: round(r.y + r.height/2), w: round(r.width), h: round(r.height)}; };
  const nodeType = (e) => {
    const n = e.closest('.diagram-node');
    return n ? (n.getAttribute('class')||'').replace('diagram-node','').trim() : null;
  };
  const conns = Array.from(document.querySelectorAll('.input-connector, .output-connector, .output-connector-droptarget'))
    .map(e => {
      const c = center(e);
      return {
        role: (e.getAttribute('class')||'').includes('output') ? 'output' : 'input',
        droptarget: (e.getAttribute('class')||'').includes('droptarget'),
        cls: (e.getAttribute('class')||'').slice(0,60),
        label: (e.textContent||'').trim().slice(0,12) || null,
        node: nodeType(e),
        ...c,
      };
    })
    .filter(c => c.w > 0 && c.x >= 0 && c.y >= 0);
  const nodes = Array.from(document.querySelectorAll('.diagram-node')).map(n => {
    const c = center(n);
    return {type:(n.getAttribute('class')||'').replace('diagram-node','').trim().slice(0,40), ...c};
  });
  const ls = {};
  for (let i=0;i<localStorage.length;i++){ const k=localStorage.key(i); ls[k]=(localStorage.getItem(k)||'').slice(0,120); }
  return {
    wireLines: document.querySelectorAll('line.wire').length,
    wireDots: document.querySelectorAll('circle.wire-dot').length,
    connectorCount: conns.length,
    connectors: conns,
    nodes: nodes,
    checkButtons: Array.from(document.querySelectorAll('button')).map(b=>(b.textContent||'').trim()).filter(Boolean),
    localStorageKeys: Object.keys(ls),
    localStorage: ls,
  };
}
"""

def dismiss_popup(pg):
    for sel in ['button:has-text("OK")', 'button:has-text("Ok")', '.popup button', '.modal button']:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible():
                el.click()
                pg.wait_for_timeout(500)
                print("dismissed popup via", sel)
                return
        except Exception as e:
            pass
    try:
        pg.keyboard.press("Escape")
        print("pressed Escape to dismiss popup")
    except Exception:
        pass

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page()
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        dismiss_popup(pg)
        pg.wait_for_timeout(1000)
        info = pg.evaluate(JS_CONNECTORS)
        print(json.dumps(info, indent=2, default=str))
        pg.screenshot(path=PROBE_DIR+"/recon_level1.png", full_page=False)
        print("SAVED:", PROBE_DIR+"/recon_level1.png")
        pg.wait_for_timeout(800)
        b.close()

if __name__ == "__main__":
    main()
