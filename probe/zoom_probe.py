# Empirically find a zoom scheme that (a) makes NandGame pins bigger/more separated, (b) keeps
# the whole layout (toolbox, Output top, Input bottom) on-screen, (c) keeps wiring functional.
# Test a larger viewport + CSS zoom; measure element fit + pin spacing; screenshot.
import json
from playwright.sync_api import sync_playwright
PROBE="/Users/holden/HackathonSF26/probe"

MEASURE = r"""
() => {
  const r = (sel) => { const e=document.querySelector(sel); if(!e) return null; const b=e.getBoundingClientRect();
    return {x:Math.round(b.x+b.width/2), y:Math.round(b.y+b.height/2), w:Math.round(b.width)}; };
  // relay free-node connectors give representative pin spacing
  const relay = document.querySelector('.diagram-node.free-node');
  let cgap=null, cin=null, inn=null;
  if (relay){ const c=relay.querySelector('.input-connector.c'); const i=relay.querySelector('.input-connector.in');
    if(c&&i){ const cb=c.getBoundingClientRect(), ib=i.getBoundingClientRect();
      cin={x:Math.round(cb.x+cb.width/2),y:Math.round(cb.y+cb.height/2)};
      inn={x:Math.round(ib.x+ib.width/2),y:Math.round(ib.y+ib.height/2)};
      cgap=Math.round(Math.abs((ib.x+ib.width/2)-(cb.x+cb.width/2))); } }
  return {
    viewport: {w: window.innerWidth, h: window.innerHeight},
    docScroll: {w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight},
    toolboxRelay: r('.diagram-node.free-node'),
    inputA: r('.input-node .output-connector.a'),
    inputV: r('.input-node .output-connector.V'),
    outputPin: r('.output-node .input-connector'),
    relay_c: cin, relay_in: inn, c_in_gap_px: cgap,
  };
}
"""
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def run(viewport, zoom, tag):
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport=viewport, device_scale_factor=1); pg=ctx.new_page(); pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(3000); dismiss(pg)
        print(f"\n[{tag}] requested viewport={viewport} zoom={zoom}")
        print("  BEFORE zoom:", json.dumps(run_measure(pg)))
        if zoom != 1.0:
            pg.evaluate("(z)=>{document.documentElement.style.zoom=String(z);}", zoom)
            pg.wait_for_timeout(400)
        m = run_measure(pg)
        print("  AFTER  zoom:", json.dumps(m))
        # fits? Output pin and Input pin both within viewport height?
        vh = m["viewport"]["h"]
        out_ok = m["outputPin"] and 0 <= m["outputPin"]["y"] <= vh
        in_ok = m["inputA"] and 0 <= m["inputA"]["y"] <= vh
        print(f"  FIT: output_on_screen={out_ok} input_on_screen={in_ok} | relay c_in_gap_px={m['c_in_gap_px']}")
        pg.screenshot(path=f"{PROBE}/zoom_{tag}.png")
        b.close()

def run_measure(pg): return pg.evaluate(MEASURE)

def main():
    run({"width":1440,"height":900}, 1.0, "base_1440x900_z1")
    run({"width":1440,"height":900}, 1.4, "z1.4_1440x900")
    run({"width":1500,"height":1300}, 1.4, "z1.4_1500x1300")
    run({"width":1600,"height":1400}, 1.5, "z1.5_1600x1400")

if __name__=="__main__": main()
