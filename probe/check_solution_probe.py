# CHECK-SOLUTION PROBE — confirm NandGame's validator ("Check solution") emits a
# machine-readable verdict (DOM classes / localStorage), so the REFEREE can be read
# programmatically (non-LLM). Tests an (incorrect) a->out wire.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

SCAN = r"""
() => {
  const q=(s)=>Array.from(document.querySelectorAll(s));
  const verdictish = q('[class*=success],[class*=correct],[class*=solved],[class*=fail],[class*=error],[class*=pass],[class*=result],[class*=complete],[class*=valid]')
    .map(e=>({cls:(e.getAttribute('class')||'').slice(0,50), txt:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,60)}))
    .filter(e=>e.cls).slice(0,30);
  // truth-table / eval rows: look at tables and rows with red/green styling
  const rows = q('tr,.row,.testcase,.test-row').map(r=>({cls:(r.getAttribute('class')||'').slice(0,40), txt:(r.textContent||'').trim().replace(/\s+/g,' ').slice(0,40),
     bg: getComputedStyle(r).backgroundColor})).filter(r=>r.txt).slice(0,20);
  const ls={}; for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i); ls[k]=localStorage.getItem(k);}
  // any visible popup/modal
  const popup = q('.popup,.modal,[class*=popup],[class*=modal]').map(e=>(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,120)).filter(Boolean).slice(0,5);
  return {verdictish, rows, popup, ls};
}
"""

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
def click_btn(pg, text):
    el = pg.query_selector(f'button:has-text("{text}")')
    if el: el.click(); pg.wait_for_timeout(800); return True
    return False

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx = b.new_context(viewport={"width":1440,"height":900})
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss_popup(pg); clear_canvas(pg)

        # make an (incorrect) connection so there's something to check
        tap(pg, 582, 806); tap(pg, 588, 191)
        print("connections before check:", pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return (o.connections||[]).length}" % LS_KEY))

        print("\n--- BEFORE Check solution ---")
        print(json.dumps(pg.evaluate(SCAN)["verdictish"], indent=1))

        click_btn(pg, "Check solution")
        pg.screenshot(path=PROBE_DIR+"/check_after.png")
        res = pg.evaluate(SCAN)
        print("\n--- AFTER Check solution (incorrect circuit) ---")
        print("verdictish:", json.dumps(res["verdictish"], indent=1))
        print("popup:", json.dumps(res["popup"], indent=1))
        print("rows(sample):", json.dumps(res["rows"][:8], indent=1))
        print("localStorage keys:", list(res["ls"].keys()))
        b.close()

if __name__ == "__main__":
    main()
