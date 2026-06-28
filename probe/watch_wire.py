# WATCH WIRE — one instrumented wire drag a->out with: elementFromPoint maps around
# source/target (find the exact connectable pixel), mid-drag screenshots (does a wire
# follow? does target highlight?), connector hover-event logging, and post wire/conn dump.
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"
LS_KEY = "NandGame:Levels:RELAY_NAND"

EFP_MAP = r"""
(arg) => {
  const cx = arg[0], cy = arg[1];
  const out = [];
  for (let dy=-12; dy<=12; dy+=6){
    for (let dx=-12; dx<=12; dx+=6){
      const el = document.elementFromPoint(cx+dx, cy+dy);
      out.push({dx, dy, cls: el ? ((el.getAttribute && el.getAttribute('class'))||el.tagName).slice(0,34) : null});
    }
  }
  return out;
}
"""

INSTR = r"""
() => {
  window.__h = [];
  ['pointerover','pointerenter','mouseover'].forEach(t=>document.addEventListener(t, e=>{
    const c=(e.target.getAttribute&&e.target.getAttribute('class'))||e.target.tagName||'?';
    if(/connector|droptarget|overlay/i.test(String(c))) window.__h.push({t, c:String(c).slice(0,34), x:Math.round(e.clientX), y:Math.round(e.clientY)});
  }, true));
}
"""

WIRES = r"""
() => {
  const longWires = Array.from(document.querySelectorAll('line.wire')).map(l=>{
    const x1=+l.getAttribute('x1'),y1=+l.getAttribute('y1'),x2=+l.getAttribute('x2'),y2=+l.getAttribute('y2');
    return {x1,y1,x2,y2,len:Math.round(Math.hypot(x2-x1,y2-y1))};
  }).filter(w=>w.len>60);
  let o={}; try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){}
  return {longWires, connCount:(o.connections||[]).length, hovers: window.__h.slice(0,12)};
}
""" % LS_KEY

def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(500)

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        dismiss_popup(pg); clear_canvas(pg)

        print("EFP around a_out (582,806):"); print(json.dumps(pg.evaluate(EFP_MAP, [582,806])))
        print("\nEFP around out_in (588,183):"); print(json.dumps(pg.evaluate(EFP_MAP, [588,183])))

        pg.evaluate(INSTR)
        # manual stepped drag with mid screenshots
        pg.mouse.move(582,806); pg.wait_for_timeout(80)
        pg.mouse.down(); pg.wait_for_timeout(120)
        pg.mouse.move(585,650, steps=12); pg.wait_for_timeout(80); pg.screenshot(path=PROBE_DIR+"/ww_1mid.png")
        pg.mouse.move(588,400, steps=12); pg.wait_for_timeout(80)
        pg.mouse.move(588,190, steps=12); pg.wait_for_timeout(120); pg.screenshot(path=PROBE_DIR+"/ww_2attarget.png")
        pg.mouse.move(588,183, steps=4); pg.wait_for_timeout(250); pg.screenshot(path=PROBE_DIR+"/ww_3hover.png")
        pg.mouse.up(); pg.wait_for_timeout(300); pg.screenshot(path=PROBE_DIR+"/ww_4released.png")

        print("\nPOST-DRAG:", json.dumps(pg.evaluate(WIRES), indent=2))
        b.close()

if __name__ == "__main__":
    main()
