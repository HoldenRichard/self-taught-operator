# EVENT PROBE — instrument the page to discover NandGame's drag interaction model.
# Records which events actually fire (pointer* / mouse* / native drag*) during a
# low-level Playwright drag, checks draggable attributes, and tests BOTH component
# placement (toolbox->canvas) and pin wiring.
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"
LS_KEY = "NandGame:Levels:RELAY_NAND"

INSTRUMENT = r"""
() => {
  window.__ev = [];
  window.__mm = 0; window.__pm = 0;
  const types = ['pointerdown','pointerup','mousedown','mouseup','dragstart','dragover','drop','dragend','click'];
  types.forEach(t => document.addEventListener(t, e => {
    const tgt = e.target;
    const cls = (tgt && tgt.getAttribute && (tgt.getAttribute('class')||'')) || (tgt && tgt.tagName) || '?';
    window.__ev.push({t, cls: String(cls).slice(0,40), x: Math.round(e.clientX||0), y: Math.round(e.clientY||0)});
  }, true));
  document.addEventListener('mousemove', ()=>{window.__mm++;}, true);
  document.addEventListener('pointermove', ()=>{window.__pm++;}, true);
  const palette = document.querySelector('.palette-nodetype') || document.querySelector('.free-node') || document.querySelector('.diagram-node');
  const conn = document.querySelector('.output-connector');
  return {
    paletteTag: palette && palette.tagName, paletteCls: palette && (palette.getAttribute('class')||'').slice(0,50),
    paletteDraggable: palette ? palette.draggable : null,
    paletteClosestDraggable: palette ? !!palette.closest('[draggable="true"]') : null,
    connDraggable: conn ? conn.draggable : null,
    connClosestDraggable: conn ? !!conn.closest('[draggable="true"]') : null,
    anyDraggableTrue: document.querySelectorAll('[draggable="true"]').length,
  };
}
"""

DUMP = r"""
() => {
  const ls = localStorage.getItem('%s');
  let o={}; try{o=JSON.parse(ls||'{}')}catch(e){}
  // summarize events: counts by type + first/last few
  const counts = {}; window.__ev.forEach(e=>counts[e.t]=(counts[e.t]||0)+1);
  return { evCounts: counts, evFirst: window.__ev.slice(0,6), evLast: window.__ev.slice(-4),
           moveMouse: window.__mm, movePointer: window.__pm,
           nodeCount:(o.nodes||[]).length, connCount:(o.connections||[]).length };
}
""" % LS_KEY

def reset_ev(pg): pg.evaluate("() => { window.__ev=[]; window.__mm=0; window.__pm=0; }")

def drag_planB(pg, x1,y1,x2,y2, steps=30):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(60)
    pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+5, y1-5, steps=4); pg.wait_for_timeout(40)
    pg.mouse.move(x2,y2, steps=steps); pg.wait_for_timeout(120)
    pg.mouse.move(x2,y2, steps=3); pg.wait_for_timeout(60)
    pg.mouse.up(); pg.wait_for_timeout(300)

def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    try:
        el = pg.query_selector('button:has-text("Clear canvas")')
        if el: el.click(); pg.wait_for_timeout(600)
    except Exception: pass

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        dismiss_popup(pg)
        clear_canvas(pg)
        meta = pg.evaluate(INSTRUMENT)
        print("DRAGGABLE/META:", json.dumps(meta, indent=2))

        print("\n=== TEST 1: place relay (toolbox 375,215 -> canvas 900,450) ===")
        reset_ev(pg)
        drag_planB(pg, 375, 215, 900, 450)
        print(json.dumps(pg.evaluate(DUMP), indent=2))
        pg.screenshot(path=PROBE_DIR+"/ev_place.png")

        clear_canvas(pg)
        print("\n=== TEST 2: wire a(582,807) -> out(588,183) ===")
        reset_ev(pg)
        drag_planB(pg, 582, 807, 588, 183)
        print(json.dumps(pg.evaluate(DUMP), indent=2))
        pg.screenshot(path=PROBE_DIR+"/ev_wire.png")

        pg.wait_for_timeout(500)
        b.close()

if __name__ == "__main__":
    main()
