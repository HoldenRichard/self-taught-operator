# DRAG DIAGNOSTIC — single Plan-A vs Plan-B drag, observe exactly what changes in
# localStorage connections + DOM, to calibrate the success oracle before measuring at scale.
# Wires input terminal 'a' (582,806) -> output-node input connector (588,183): both exist
# from level start, far apart, small targets -> a clean precision test.
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"
LS_KEY = "NandGame:Levels:RELAY_NAND"

A = (582, 807)   # terminal 'a' output connector
OUT = (588, 183) # output-node input connector

READ_STATE = """
() => {
  const ls = localStorage.getItem('%s');
  let conns=null, nodes=null;
  try { const o=JSON.parse(ls||'{}'); conns=o.connections||[]; nodes=o.nodes||[]; } catch(e){}
  return { connCount: conns?conns.length:null, nodeCount: nodes?nodes.length:null,
           connections: conns, wireLines: document.querySelectorAll('line.wire').length };
}
""" % LS_KEY

def read_state(pg): return pg.evaluate(READ_STATE)

def drag_planA(pg, x1,y1,x2,y2):
    # exact replica of harness drag_and_drop: single jump, no interpolation
    pg.mouse.move(x1,y1); pg.mouse.down(); pg.mouse.move(x2,y2); pg.mouse.up()

def drag_planB(pg, x1,y1,x2,y2, steps=30):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(60)
    pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+5, y1-5, steps=4); pg.wait_for_timeout(40)   # threshold nudge
    pg.mouse.move(x2,y2, steps=steps); pg.wait_for_timeout(120)    # interpolated travel
    pg.mouse.move(x2,y2, steps=3); pg.wait_for_timeout(60)         # settle on target
    pg.mouse.up(); pg.wait_for_timeout(250)

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
    except Exception as e:
        print("clear_canvas err:", e)

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())  # auto-accept any confirm()
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        dismiss_popup(pg)
        clear_canvas(pg)
        print("BASELINE:", json.dumps(read_state(pg)))

        print("\n--- PLAN B (interpolated) drag a -> out ---")
        drag_planB(pg, *A, *OUT)
        st = read_state(pg)
        print("AFTER B:", json.dumps(st))
        pg.screenshot(path=PROBE_DIR+"/diag_after_B.png")

        clear_canvas(pg)
        print("\nafter clear:", json.dumps(read_state(pg)))

        print("\n--- PLAN A (single-jump, harness replica) drag a -> out ---")
        drag_planA(pg, *A, *OUT)
        pg.wait_for_timeout(250)
        st = read_state(pg)
        print("AFTER A:", json.dumps(st))
        pg.screenshot(path=PROBE_DIR+"/diag_after_A.png")

        pg.wait_for_timeout(500)
        b.close()

if __name__ == "__main__":
    main()
