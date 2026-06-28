# CALIBRATE & SOLVE — robust wiring: connector ELEMENT bbox centers (no sub-element drill)
# + self-calibrating wire() that searches small y-offsets, cancels stray armed wires with
# Escape, and gates each connection on the oracle. Build relay-NAND, Check, capture verdict.
import json
from playwright.sync_api import sync_playwright

LS_KEY = "NandGame:Levels:RELAY_NAND"
PROBE_DIR = "/Users/holden/HackathonSF26/probe"

PINS = r"""
() => {
  const c = el => { if(!el) return null; const r=el.getBoundingClientRect();
    return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)}; };
  const o={};
  o.a=c(document.querySelector('.input-node .output-connector.a'));
  o.b=c(document.querySelector('.input-node .output-connector.b'));
  o.V=c(document.querySelector('.input-node .output-connector.V'));
  o.output=c(document.querySelector('.output-node .input-connector'));
  const placed=Array.from(document.querySelectorAll('.diagram-node'))
    .filter(n=>n.querySelector('.input-connector.c')&&n.querySelector('.input-connector.in'))
    .filter(n=>{const r=n.getBoundingClientRect();return r.x>460&&r.width>0;})
    .sort((p,q)=>p.getBoundingClientRect().x-q.getBoundingClientRect().x);
  o.relays=placed.map(n=>({out:c(n.querySelector('.output-connector')), c:c(n.querySelector('.input-connector.c')), in_:c(n.querySelector('.input-connector.in'))}));
  return o;
}
"""
VERDICT = r"""
() => {
  const pick=sel=>Array.from(document.querySelectorAll(sel)).map(e=>({cls:(e.getAttribute('class')||'').slice(0,70), txt:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,200)}));
  return { dialogs:pick('[class*=popup-dialog]'),
    successish:pick('[class*=success],[class*=correct],[class*=solved],[class*=complete],[class*=congrat],[class*=passed],[class*=next-level]'),
    error_banner: !!document.querySelector('.error-banner'),
    error_text: (document.querySelector('.error-banner')||{}).textContent||null,
    test_rows: Array.from(document.querySelectorAll('.test-results .error, .test-results tr')).map(r=>(r.textContent||'').trim().replace(/\s+/g,' ').slice(0,30)).slice(0,12),
    levels: localStorage.getItem('NandGame:Levels') };
}
"""
def ntotal(pg): return pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return (o.connections||[]).length}" % LS_KEY)
def dismiss(pg):
    try:
        el=pg.query_selector('button:has-text("OK")');
        if el and el.is_visible(): el.click(); pg.wait_for_timeout(400)
    except Exception: pass
def clear(pg):
    pg.once("dialog", lambda d:d.accept()); el=pg.query_selector('button:has-text("Clear canvas")')
    if el: el.click(); pg.wait_for_timeout(450)
def drag(pg,x1,y1,x2,y2,steps=28):
    pg.mouse.move(x1,y1);pg.wait_for_timeout(60);pg.mouse.down();pg.wait_for_timeout(90)
    pg.mouse.move(x1+4,y1+4,steps=4);pg.wait_for_timeout(30);pg.mouse.move(x2,y2,steps=steps);pg.wait_for_timeout(120);pg.mouse.up();pg.wait_for_timeout(250)

def wire(pg, src, tgt, label=""):
    """Self-calibrating tap-tap. Returns True when oracle shows a NEW connection."""
    before = ntotal(pg)
    for sdy, tdy in [(0,0),(0,7),(0,10),(0,4),(-3,7),(3,10),(0,-4)]:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(50)
        pg.mouse.move(src["x"], src["y"]+sdy); pg.wait_for_timeout(40)
        pg.mouse.click(src["x"], src["y"]+sdy); pg.wait_for_timeout(140)
        pg.mouse.move(tgt["x"], tgt["y"]+tdy); pg.wait_for_timeout(40)
        pg.mouse.click(tgt["x"], tgt["y"]+tdy); pg.wait_for_timeout(160)
        if ntotal(pg) > before:
            return True
    return False

def main():
    with sync_playwright() as p:
        b=p.chromium.launch(headless=False,args=["--disable-extensions","--disable-dev-shm-usage"])
        ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
        pg.on("dialog", lambda d:d.accept())
        pg.goto("https://nandgame.com", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000); dismiss(pg); clear(pg)
        drag(pg,375,215,660,400); drag(pg,375,215,940,400)
        pins=pg.evaluate(PINS); print("PINS:", json.dumps(pins))
        if len(pins["relays"])<2: print("!! relays not placed"); b.close(); return
        A,B=pins["relays"][0],pins["relays"][1]
        plan=[("V->A.in",pins["V"],A["in_"]),("a->A.c",pins["a"],A["c"]),("A.out->output",A["out"],pins["output"]),
              ("V->B.in",pins["V"],B["in_"]),("b->B.c",pins["b"],B["c"]),("B.out->output",B["out"],pins["output"])]
        for name,s,t in plan:
            ok=wire(pg,s,t,name); print(f"  {name}: {'OK' if ok else 'FAIL'} (total={ntotal(pg)})")
        print("\nCONNS:", json.dumps(pg.evaluate("()=>{let o={};try{o=JSON.parse(localStorage.getItem('%s')||'{}')}catch(e){};return o.connections||[]}" % LS_KEY)))
        pg.screenshot(path=PROBE_DIR+"/cs_built.png")
        el=pg.query_selector('button:has-text("Check solution")')
        if el: el.click(); pg.wait_for_timeout(900)
        print("\n===== VERDICT =====\n"+json.dumps(pg.evaluate(VERDICT), indent=2))
        pg.screenshot(path=PROBE_DIR+"/cs_verdict.png")
        pg.wait_for_timeout(400); b.close()

if __name__=="__main__":
    main()
