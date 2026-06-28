# WIRE TUNING — NandGame wiring uses triangle handles ("Tap or drag the triangle").
# Test which connect primitive is most reliable: tap-tap (click source handle, click
# target) vs tuned interpolated drag. Source = input terminal 'a', target = output node.
import json
from playwright.sync_api import sync_playwright

PROBE_DIR = "/Users/holden/HackathonSF26/probe"
LS_KEY = "NandGame:Levels:RELAY_NAND"

POINTS = r"""
() => {
  const ctr = e => { const r=e.getBoundingClientRect();
    return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), w:Math.round(r.width), h:Math.round(r.height)}; };
  const o = {};
  const outNode = document.querySelector('.output-node');
  if (outNode){ const ic = outNode.querySelector('.input-connector'); if (ic) o.out_in = ctr(ic); }
  const inNodes = Array.from(document.querySelectorAll('.input-node'));
  if (inNodes[0]){ const oc = inNodes[0].querySelector('.output-connector'); if (oc) o.a_out = ctr(oc); }
  // all svg polygons (triangle handles) with center + nearby connector context
  o.polygons = Array.from(document.querySelectorAll('svg polygon, svg path')).map(p=>{
    const c = ctr(p);
    const host = p.closest('.input-connector,.output-connector,.connector,.input-node,.output-node,.diagram-node');
    return {...c, host: host ? (host.getAttribute('class')||'').slice(0,40) : null, tag:p.tagName};
  }).filter(p=>p.w>0 && p.w<40 && p.h<40).slice(0,40);
  return o;
}
"""

def read_conn(pg):
    return pg.evaluate("""() => { let o={}; try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){}
      return {nodeCount:(o.nodes||[]).length, connCount:(o.connections||[]).length}; }""" % LS_KEY)

def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    try:
        el = pg.query_selector('button:has-text("Clear canvas")')
        if el: el.click(); pg.wait_for_timeout(500)
    except Exception: pass

def tap(pg, x, y):
    pg.mouse.move(x, y); pg.wait_for_timeout(50); pg.mouse.click(x, y); pg.wait_for_timeout(150)

def drag_tuned(pg, x1,y1,x2,y2, steps=35):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(70)
    pg.mouse.down(); pg.wait_for_timeout(100)
    pg.mouse.move(x1+4,y1-4, steps=4); pg.wait_for_timeout(40)
    pg.mouse.move((x1+x2)//2,(y1+y2)//2, steps=steps//2); pg.wait_for_timeout(40)
    pg.mouse.move(x2,y2, steps=steps); pg.wait_for_timeout(150)   # slow approach
    pg.mouse.move(x2+2,y2, steps=2); pg.mouse.move(x2,y2, steps=2); pg.wait_for_timeout(120)  # wiggle+dwell
    pg.mouse.up(); pg.wait_for_timeout(250)

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        dismiss_popup(pg); clear_canvas(pg)

        pts = pg.evaluate(POINTS)
        print("POINTS:", json.dumps(pts, indent=2))
        a = pts.get("a_out"); out = pts.get("out_in")
        if not a or not out:
            print("!! missing endpoints"); b.close(); return
        ax, ay = a["x"], a["y"]; ox, oy = out["x"], out["y"]

        # find triangle near 'a' (closest polygon to a_out) and near output (closest to out_in)
        polys = pts.get("polygons", [])
        def closest(px, py):
            best=None; bd=1e9
            for q in polys:
                d=(q["x"]-px)**2+(q["y"]-py)**2
                if d<bd: bd=d; best=q
            return best
        a_tri = closest(ax, ay); print("triangle near a:", a_tri)

        strategies = []
        # S1: tap-tap on connector circles
        def s1():
            clear_canvas(pg); tap(pg, ax, ay); tap(pg, ox, oy)
        # S2: tap triangle(a) then tap target connector
        def s2():
            clear_canvas(pg)
            if a_tri: tap(pg, a_tri["x"], a_tri["y"])
            tap(pg, ox, oy)
        # S3: tuned drag from connector circle a -> out
        def s3():
            clear_canvas(pg); drag_tuned(pg, ax, ay, ox, oy)
        # S4: tuned drag from triangle(a) -> out
        def s4():
            clear_canvas(pg)
            sx, sy = (a_tri["x"], a_tri["y"]) if a_tri else (ax, ay)
            drag_tuned(pg, sx, sy, ox, oy)

        for name, fn in [("S1 tap-tap circle", s1), ("S2 tap tri->circle", s2),
                         ("S3 drag circle->out", s3), ("S4 drag tri->out", s4)]:
            try:
                fn(); st = read_conn(pg)
                print(f"{name}: {json.dumps(st)}  {'<<< CONNECTED' if st['connCount']>0 else ''}")
                pg.screenshot(path=f"{PROBE_DIR}/wt_{name.split()[0]}.png")
            except Exception as e:
                print(f"{name}: ERROR {e}")
        b.close()

if __name__ == "__main__":
    main()
