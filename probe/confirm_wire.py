# CONFIRM WIRE — release-Y sweep around the true connector hit-point (~588,190).
# Drag from terminal 'a' (582,806) up to the output-node input connector; find which
# release point actually creates a connection (connCount increase).
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

def conn_count(pg):
    return pg.evaluate("""() => { let o={}; try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){}
       return (o.connections||[]).length; }""" % LS_KEY)

def dismiss_popup(pg):
    try:
        el = pg.query_selector('button:has-text("OK")')
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass

def clear_canvas(pg):
    pg.once("dialog", lambda d: d.accept())
    el = pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)

def wire(pg, sx, sy, tx, ty):
    pg.mouse.move(sx, sy); pg.wait_for_timeout(70)
    pg.mouse.down(); pg.wait_for_timeout(100)
    pg.mouse.move(sx+3, sy-6, steps=4); pg.wait_for_timeout(30)        # cross drag threshold
    pg.mouse.move(tx, (sy+ty)//2, steps=20); pg.wait_for_timeout(30)   # travel
    pg.mouse.move(tx, ty, steps=18); pg.wait_for_timeout(180)          # slow approach + dwell on target
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

        results = {}
        for ty in [186, 190, 193, 196, 200]:
            clear_canvas(pg)
            before = conn_count(pg)
            wire(pg, 582, 806, 588, ty)
            after = conn_count(pg)
            ok = after > before
            results[ty] = {"before": before, "after": after, "connected": ok}
            print(f"release y={ty}: before={before} after={after} {'<<< CONNECTED' if ok else ''}")
            if ok:
                pg.screenshot(path=f"{PROBE_DIR}/cw_connected_y{ty}.png")
        print("\nSUMMARY:", json.dumps(results))
        b.close()

if __name__ == "__main__":
    main()
