# FIND & WIRE — locate the real triangle handles near source 'a' and the output node,
# then test tap-tap and drag FROM THE TRIANGLE. Dump full localStorage after each attempt
# to settle both the gesture and the connection oracle.
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"

NEAR = r"""
(arg) => {
  const cx=arg[0], cy=arg[1], r=arg[2];
  const ctr = e => { const b=e.getBoundingClientRect();
    return {x:Math.round(b.x+b.width/2), y:Math.round(b.y+b.height/2), w:Math.round(b.width), h:Math.round(b.height)}; };
  return Array.from(document.querySelectorAll('svg polygon, svg path, .input-connector, .output-connector, .connector'))
    .map(e=>({...ctr(e), tag:e.tagName, cls:(((e.getAttribute&&e.getAttribute('class'))||'')).slice(0,32)}))
    .filter(e=>e.w>0 && Math.hypot(e.x-cx,e.y-cy)<r)
    .sort((a,b)=>Math.hypot(a.x-cx,a.y-cy)-Math.hypot(b.x-cx,b.y-cy));
}
"""
LS_ALL = "() => { const o={}; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i); o[k]=localStorage.getItem(k);} return o; }"

def ls(pg): return pg.evaluate(LS_ALL)
def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def tap(pg,x,y):
    pg.mouse.move(x,y); pg.wait_for_timeout(60); pg.mouse.click(x,y); pg.wait_for_timeout(200)
def drag(pg,x1,y1,x2,y2,steps=30):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(70); pg.mouse.down(); pg.wait_for_timeout(110)
    pg.mouse.move(x1+3,y1-5,steps=4); pg.wait_for_timeout(30)
    pg.mouse.move(x2,y2,steps=steps); pg.wait_for_timeout(200)
    pg.mouse.up(); pg.wait_for_timeout(250)

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss_popup(pg); clear_canvas(pg)

        print("NEAR a (582,806):"); print(json.dumps(pg.evaluate(NEAR,[582,806,45]), indent=1))
        print("\nNEAR out (588,190):"); print(json.dumps(pg.evaluate(NEAR,[588,190,45]), indent=1))

        a_near = pg.evaluate(NEAR,[582,806,45]); out_near = pg.evaluate(NEAR,[588,190,45])
        a_tri = next((e for e in a_near if e["tag"] in ("polygon","path")), None)
        out_tri = next((e for e in out_near if e["tag"] in ("polygon","path")), None)
        print("\na_tri:", a_tri, "| out_tri:", out_tri)
        if not a_tri:
            print("!! no source triangle found near a");
        a_t = (a_tri["x"], a_tri["y"]) if a_tri else (582,806)
        o_t = (out_tri["x"], out_tri["y"]) if out_tri else (588,190)

        base = json.dumps(ls(pg))
        attempts = [
            ("T1 tap a_tri -> tap out_tri", lambda: (clear_canvas(pg), tap(pg,*a_t), tap(pg,*o_t))),
            ("T2 tap a_tri -> tap out_conn", lambda: (clear_canvas(pg), tap(pg,*a_t), tap(pg,588,190))),
            ("T3 drag a_tri -> out_tri",     lambda: (clear_canvas(pg), drag(pg,*a_t,*o_t))),
            ("T4 drag a_tri -> out_conn",    lambda: (clear_canvas(pg), drag(pg,a_t[0],a_t[1],588,190))),
        ]
        for name, fn in attempts:
            fn(); cur = ls(pg)
            changed = json.dumps(cur) != base
            print(f"\n=== {name} -> changed={changed} ===")
            print(json.dumps(cur))
            if changed: pg.screenshot(path=f"{PROBE_DIR}/fw_{name.split()[0]}.png")
        b.close()

if __name__ == "__main__":
    main()
