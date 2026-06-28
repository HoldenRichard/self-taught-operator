# RELIABILITY — measure the two core mechanics against the localStorage oracle:
#   A) component placement via drag (toolbox -> canvas), N=6
#   B) wiring via TAP-TAP (click source connector, click target connector), N=12 with
#      small coordinate jitter to test target tolerance (simulating imperfect aim).
import json, random
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
random.seed(7)

def state(pg):
    return pg.evaluate("""() => { let o={}; try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){}
       return {n:(o.nodes||[]).length, c:(o.connections||[]).length}; }""" % LS_KEY)

def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(400)
def tap(pg,x,y):
    pg.mouse.move(x,y); pg.wait_for_timeout(50); pg.mouse.click(x,y); pg.wait_for_timeout(160)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1); pg.wait_for_timeout(60); pg.mouse.down(); pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4); pg.wait_for_timeout(30)
    pg.mouse.move(x2,y2,steps=steps); pg.wait_for_timeout(120); pg.mouse.up(); pg.wait_for_timeout(220)

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss_popup(pg); clear_canvas(pg)

        # A) PLACEMENT (drag toolbox 'relay default on' @375,215 -> random canvas point)
        place_ok = 0; N_PLACE = 6
        for i in range(N_PLACE):
            clear_canvas(pg)
            tx, ty = random.randint(620,1280), random.randint(300,720)
            drag(pg, 375, 215, tx, ty)
            ok = state(pg)["n"] >= 1
            place_ok += ok
            print(f"[place {i+1}/{N_PLACE}] -> {tx},{ty}  nodes={state(pg)['n']}  {'OK' if ok else 'MISS'}")

        # B) WIRING via tap-tap (a connector 582,806 -> output connector ~588,190) with jitter
        clear_canvas(pg)
        wire_ok = 0; N_WIRE = 12
        for i in range(N_WIRE):
            clear_canvas(pg)
            jx, jy = random.randint(-3,3), random.randint(-3,3)   # jitter on target
            sx, sy = 582 + random.randint(-2,2), 806 + random.randint(-2,2)
            tap(pg, sx, sy)
            tap(pg, 588+jx, 190+jy)
            c = state(pg)["c"]
            ok = c >= 1
            wire_ok += ok
            print(f"[wire {i+1}/{N_WIRE}] src=({sx},{sy}) tgt=(588{jx:+},190{jy:+})  conn={c}  {'OK' if ok else 'MISS'}")

        print("\n==== RESULTS ====")
        print(f"PLACEMENT (drag):  {place_ok}/{N_PLACE}  = {100*place_ok/N_PLACE:.0f}%")
        print(f"WIRING (tap-tap):  {wire_ok}/{N_WIRE} = {100*wire_ok/N_WIRE:.0f}%")
        b.close()

if __name__ == "__main__":
    main()
